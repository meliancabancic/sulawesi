"""
Descarga mecanismos focales del ISC Bulletin para la región de Sulawesi
e integra los planos nodales en la base de datos.

Estrategia:
  1. Descargar catálogo FMCSV del ISC (todas las agencias, M≥5.0, 1976-2025).
  2. Por evento ISC, conservar una sola solución priorizando: GCMT > GCMT-MT > NEIC > otras.
  3. Para cada evento con planos nodales válidos:
       a. Buscar coincidencia en DB (±0.25° lat/lon, ±0.3 Mw, mismo año).
       b. Si coincide y le faltan planos → ACTUALIZAR strike/dip/rake.
       c. Si no coincide → INSERTAR como source='isc'.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_isc
"""
import csv, io, math, sqlite3
from pathlib import Path
from datetime import datetime

import httpx

BASE    = Path(__file__).parent.parent.parent
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"

ISC_URL = (
    "http://www.isc.ac.uk/cgi-bin/web-db-run"
    "?request=FMECH&out_format=FMCSV"
    "&searchshape=RECT"
    "&bot_lat=-12&top_lat=7&left_lon=114&right_lon=132"
    "&start_year=1976&start_mon=1&end_year=2025&end_mon=12"
    "&min_mag=5.0&req_mag_agcy=Any&req_mag_type=Any"
)

# Orden de preferencia de agencias (menor índice = mejor)
AGENCY_RANK = {
    "GCMT": 0, "GCMT-MT": 0,
    "NEIC": 1, "PDE": 1, "USGS": 1,
    "HRV": 2,
}


# ── Clasificación de tipo de falla ────────────────────────────────────────────
def fault_type(rake) -> str:
    if rake is None:
        return "O"
    r = float(rake)
    if r > 180:  r -= 360
    if r < -180: r += 360
    if  45 <= r <= 135:  return "T"
    if -135 <= r <= -45: return "N"
    if (-30 <= r <= 30) or r >= 150 or r <= -150: return "S"
    return "O"


# ── Descarga ──────────────────────────────────────────────────────────────────
def download() -> str:
    print("  Descargando ISC focal mechanism bulletin…")
    with httpx.Client(timeout=180, follow_redirects=True) as client:
        resp = client.get(ISC_URL)
        resp.raise_for_status()
    print(f"  Recibidos {len(resp.content)//1024} KB")
    return resp.text


# ── Parseo FMCSV ─────────────────────────────────────────────────────────────
def parse(text: str) -> list[dict]:
    """
    El ISC FMCSV tiene líneas de comentario con '#' y una cabecera también con '#'.
    Columnas clave: EVENTID, AUTHOR, DATE, TIME, LAT, LON, DEPTH, MW,
                    STRIKEA, DIPA, RAKEA, STRIKEB, DIPB, RAKEB
    """
    lines = text.splitlines()

    # Localizar línea de cabecera
    header_line = None
    for line in lines:
        stripped = line.lstrip("#").strip()
        if stripped.upper().startswith("EVENTID"):
            header_line = stripped
            break
    if header_line is None:
        raise ValueError("No se encontró la cabecera FMCSV del ISC")

    cols = [c.strip().upper() for c in header_line.split(",")]

    def idx(name: str) -> int:
        try:
            return cols.index(name)
        except ValueError:
            return -1

    I_EID    = idx("EVENTID")
    I_AUTH   = idx("AUTHOR")
    I_DATE   = idx("DATE")
    I_LAT    = idx("LAT")
    I_LON    = idx("LON")
    I_DEP    = idx("DEPTH")
    I_MW     = idx("MW")
    I_STRA   = idx("STRIKEA")
    I_DIPA   = idx("DIPA")
    I_RAKA   = idx("RAKEA")
    I_STRB   = idx("STRIKEB")
    I_DIPB   = idx("DIPB")
    I_RAKB   = idx("RAKEB")

    def flt(parts, i) -> float:
        try:
            return float(parts[i]) if i >= 0 and i < len(parts) else math.nan
        except (ValueError, TypeError):
            return math.nan

    def intr(parts, i):
        v = flt(parts, i)
        return int(round(v)) if not math.isnan(v) else None

    events = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or line.upper().startswith("STOP"):
            continue
        parts = line.split(",")

        lat = flt(parts, I_LAT)
        lon = flt(parts, I_LON)
        dep = flt(parts, I_DEP)
        mw  = flt(parts, I_MW)
        s1  = intr(parts, I_STRA)
        d1  = intr(parts, I_DIPA)
        r1  = intr(parts, I_RAKA)
        s2  = intr(parts, I_STRB)
        d2  = intr(parts, I_DIPB)
        r2  = intr(parts, I_RAKB)

        if any(math.isnan(v) for v in [lat, lon, dep]):
            continue
        if s1 is None or d1 is None or r1 is None:
            continue  # sin planos nodales → no útil

        # Año
        date_str = parts[I_DATE].strip() if I_DATE >= 0 and I_DATE < len(parts) else ""
        try:
            yr = int(date_str[:4])
            mo = int(date_str[5:7]) if len(date_str) >= 7 else 0
        except (ValueError, IndexError):
            continue

        eid    = parts[I_EID].strip()  if I_EID >= 0 and I_EID < len(parts) else ""
        author = parts[I_AUTH].strip() if I_AUTH >= 0 and I_AUTH < len(parts) else ""

        events.append({
            "eid": eid, "author": author,
            "yr": yr, "mo": mo,
            "lo": round(lon, 3), "la": round(lat, 3), "de": round(dep, 1),
            "mw": round(mw, 1) if not math.isnan(mw) else None,
            "s1": s1, "d1": d1, "r1": r1,
            "s2": s2, "d2": d2, "r2": r2,
            "ft": fault_type(r1),
        })

    return events


# ── Dedup: mejor agencia por evento ISC ──────────────────────────────────────
def best_per_event(events: list[dict]) -> list[dict]:
    by_eid: dict[str, dict] = {}
    for e in events:
        eid = e["eid"]
        if not eid:
            continue
        if eid not in by_eid:
            by_eid[eid] = e
        else:
            prev_rank = AGENCY_RANK.get(by_eid[eid]["author"].upper(), 99)
            curr_rank = AGENCY_RANK.get(e["author"].upper(), 99)
            if curr_rank < prev_rank:
                by_eid[eid] = e
    return list(by_eid.values())


# ── Integración en DB ────────────────────────────────────────────────────────
def integrate(events: list[dict]) -> tuple[int, int, int]:
    conn = sqlite3.connect(DB_PATH)
    updated = inserted = skipped = 0

    for e in events:
        if e["mw"] is None:
            skipped += 1
            continue

        # Buscar coincidencias en DB: misma zona, misma magnitud, mismo año
        rows = conn.execute("""
            SELECT id, strike1
            FROM   earthquakes
            WHERE  year            =  ?
              AND  ABS(lat  - ?)  <= 0.25
              AND  ABS(lon  - ?)  <= 0.25
              AND  ABS(magnitude - ?) <= 0.3
        """, (e["yr"], e["la"], e["lo"], e["mw"])).fetchall()

        if rows:
            for row_id, strike1 in rows:
                if strike1 is None:
                    conn.execute("""
                        UPDATE earthquakes
                        SET    strike1=?, dip1=?, rake1=?,
                               strike2=?, dip2=?, rake2=?,
                               fault_type=?
                        WHERE  id=?
                    """, (e["s1"], e["d1"], e["r1"],
                          e["s2"], e["d2"], e["r2"],
                          e["ft"], row_id))
                    updated += 1
                else:
                    skipped += 1
        else:
            conn.execute("""
                INSERT INTO earthquakes
                    (source, lon, lat, depth, magnitude, year, fault_type,
                     strike1, dip1, rake1, strike2, dip2, rake2)
                VALUES ('isc', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (e["lo"], e["la"], e["de"], e["mw"], e["yr"], e["ft"],
                  e["s1"], e["d1"], e["r1"], e["s2"], e["d2"], e["r2"]))
            inserted += 1

    conn.commit()
    conn.close()
    return updated, inserted, skipped


# ── Punto de entrada ──────────────────────────────────────────────────────────
def run():
    from backend.database import init_db
    init_db()

    text     = download()
    all_evts = parse(text)
    print(f"  Soluciones parseadas:      {len(all_evts)}")

    best = best_per_event(all_evts)
    print(f"  Eventos únicos (ISC ID):   {len(best)}")

    updated, inserted, skipped = integrate(best)
    print(f"  Eventos actualizados (MT añadido): {updated}")
    print(f"  Eventos insertados  (nuevos):      {inserted}")
    print(f"  Omitidos (ya tenían MT o sin Mw):  {skipped}")

    conn = sqlite3.connect(DB_PATH)
    total   = conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
    with_mt = conn.execute(
        "SELECT COUNT(*) FROM earthquakes WHERE strike1 IS NOT NULL"
    ).fetchone()[0]
    pct = with_mt / total * 100 if total else 0
    conn.close()
    print(f"\n  Total en DB: {total}  —  con MT: {with_mt} ({pct:.1f}%)")


if __name__ == "__main__":
    run()
