"""
Descarga y parsea el catálogo GlobalCMT en formato NDK directamente del
servidor GCMT (www.globalcmt.org) para la región de Sulawesi.

GlobalCMT es la fuente primaria de mecanismos focales (M≥5.0, 1976-presente).
Este script descarga los archivos NDK por década y los parsea.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_gcmt_ndk
"""
import math, re, sqlite3
from pathlib import Path
from io import StringIO

import httpx

DB_PATH = Path(__file__).parent.parent / "sulawesi.db"

# Región Sulawesi con margen
LAT_MIN, LAT_MAX = -12.0,  7.0
LON_MIN, LON_MAX = 114.0, 132.0

# Archivos NDK en el servidor GCMT, uno por rango de años
GCMT_BASE = "http://www.ldeo.columbia.edu/~gcmt/projects/CMT/catalog/"
# Archivo masivo 1976-2020 + años individuales recientes + Quick CMT
NDK_FILES = [
    "jan76_dec20.ndk",      # catálogo completo 1976-2020
    "NEW_QUICK/qcmt.ndk",   # soluciones rápidas recientes (2021-presente)
]


def fault_type(rake) -> str:
    if rake is None: return "O"
    r = float(rake)
    if r > 180:  r -= 360
    if r < -180: r += 360
    if  45 <= r <= 135:  return "T"
    if -135 <= r <= -45: return "N"
    if (-30 <= r <= 30) or r >= 150 or r <= -150: return "S"
    return "O"


def parse_ndk(text: str) -> list[dict]:
    """
    Formato NDK: cada evento ocupa 5 líneas NO vacías.
    L1: SOURCE  YYYY/MM/DD HH:MM:SS.S  LAT  LON  DEP  mb  ms  REGION
    L2: CMT name / data info
    L3: CENTROID: time_shift err LAT err LON err DEP err FIX...
    L4: EXP  Mrr err  Mtt err  Mpp err  Mrt err  Mrp err  Mtp err
    L5: V##  e1 pl az  e2 pl az  e3 pl az  scalar  s1 d1 r1  s2 d2 r2
    """
    events = []
    # Agrupar en bloques de 5 líneas no vacías
    non_empty = [l for l in text.splitlines() if l.strip()]
    i = 0
    while i + 4 < len(non_empty):
        L1 = non_empty[i]
        L3 = non_empty[i+2]
        L4 = non_empty[i+3]
        L5 = non_empty[i+4]
        i += 5

        # ── Línea 1: fecha YYYY/MM/DD y ubicación del hipocentro ─────────────
        m1 = re.match(
            r'\S+\s+(\d{4})/(\d{2})/(\d{2})\s+[\d:\.]+\s+([-\d\.]+)\s+([-\d\.]+)\s+([\d\.]+)',
            L1.strip()
        )
        if not m1:
            continue
        yr = int(m1.group(1))
        la = float(m1.group(4))
        lo = float(m1.group(5))
        de = float(m1.group(6))

        # Filtro geográfico rápido antes de procesar más
        if not (LAT_MIN <= la <= LAT_MAX and LON_MIN <= lo <= LON_MAX):
            continue

        # ── Línea 3: coordenadas del centroide (más precisas) ─────────────────
        # Formato: CENTROID: time_shift err LAT err LON err DEP err ...
        m3 = re.match(
            r'CENTROID:\s+[-\d\.]+\s+[\d\.]+\s+([-\d\.]+)\s+[\d\.]+\s+([-\d\.]+)\s+[\d\.]+\s+([\d\.]+)',
            L3.strip()
        )
        if m3:
            la = float(m3.group(1))
            lo = float(m3.group(2))
            de = float(m3.group(3))

        # ── Línea 4: exponente del tensor de momento (primeros 2 chars) ───────
        try:
            exp = int(L4.strip()[:2])
        except (ValueError, IndexError):
            continue

        # ── Línea 5: ejes principales + momento escalar + planos nodales ──────
        # Tokens: V##  e1 pl az  e2 pl az  e3 pl az  scalar  s1 d1 r1  s2 d2 r2
        #         [0]  [1][2][3] [4][5][6] [7][8][9]  [10]  [11-16]
        tokens = L5.strip().split()
        if len(tokens) < 17:
            continue

        try:
            scalar = float(tokens[10])
            mw = round((2/3) * (exp + math.log10(abs(scalar)) - 16.1), 1)
            s1 = int(tokens[11]); d1 = int(tokens[12]); r1 = int(tokens[13])
            s2 = int(tokens[14]); d2 = int(tokens[15]); r2 = int(tokens[16])
        except (ValueError, IndexError):
            continue

        events.append({
            "yr": yr,
            "lo": round(lo, 3), "la": round(la, 3), "de": round(de, 1),
            "mw": mw,
            "s1": s1, "d1": d1, "r1": r1,
            "s2": s2, "d2": d2, "r2": r2,
            "ft": fault_type(r1),
        })

    return events


def integrate(events: list[dict]) -> tuple[int, int, int]:
    conn = sqlite3.connect(DB_PATH)
    updated = inserted = skipped = 0

    for e in events:
        rows = conn.execute("""
            SELECT id, strike1
            FROM   earthquakes
            WHERE  year           =  ?
              AND  ABS(lat  - ?) <= 0.25
              AND  ABS(lon  - ?) <= 0.25
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
                VALUES ('gcmt', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (e["lo"], e["la"], e["de"], e["mw"], e["yr"], e["ft"],
                  e["s1"], e["d1"], e["r1"], e["s2"], e["d2"], e["r2"]))
            inserted += 1

    conn.commit()
    conn.close()
    return updated, inserted, skipped


def run():
    from backend.database import init_db
    init_db()

    total_parsed = total_upd = total_ins = total_skip = 0

    with httpx.Client(timeout=120, follow_redirects=True) as client:
        for fname in NDK_FILES:
            url = GCMT_BASE + fname
            print(f"  Descargando {fname}…", end=" ", flush=True)
            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"ERROR ({exc})")
                continue

            events = parse_ndk(resp.text)
            print(f"{len(events)} eventos en región")
            total_parsed += len(events)

            upd, ins, skp = integrate(events)
            total_upd  += upd
            total_ins  += ins
            total_skip += skp

    print(f"\n  Total parseados en región: {total_parsed}")
    print(f"  Actualizados (MT añadido): {total_upd}")
    print(f"  Insertados  (nuevos):      {total_ins}")
    print(f"  Omitidos (ya tenían MT):   {total_skip}")

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
