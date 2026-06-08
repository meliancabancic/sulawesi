"""
Importa los datos sísmicos existentes a SQLite.
Ejecutar una sola vez (o para reimportar):

    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_earthquakes
"""
import json, sqlite3
from pathlib import Path

BASE    = Path(__file__).parent.parent.parent   # mapa/
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn


def import_usgs_55():
    """Mw 5.5-5.9 con mecanismo focal — fuentes/gcmt55_sulawesi.json"""
    path = BASE / "fuentes" / "gcmt55_sulawesi.json"
    with open(path, encoding="utf-8") as f:
        events = json.load(f)

    conn = get_conn()
    conn.execute("DELETE FROM earthquakes WHERE source='usgs'")
    conn.executemany("""
        INSERT INTO earthquakes
            (source, lon, lat, depth, magnitude, year, fault_type,
             strike1, dip1, rake1, strike2, dip2, rake2, label)
        VALUES ('usgs',?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (e["lo"], e["la"], e["de"], e["mw"], e["yr"], e["ft"],
         e["s1"], e["d1"], e["r1"], e["s2"], e["d2"], e["r2"], e.get("label", ""))
        for e in events
    ])
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM earthquakes WHERE source='usgs'").fetchone()[0]
    conn.close()
    print(f"  USGS Mw5.5-5.9: {n} eventos")


def import_cmt_inline():
    """Mw≥6 GlobalCMT — extrae CMT_EVENTS de js/config.js"""
    config_js = BASE / "js" / "config.js"
    text = config_js.read_text(encoding="utf-8")

    # CMT_EVENTS está en una sola línea larga
    events = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("const CMT_EVENTS"):
            idx = line.index("[")
            json_str = line[idx:]
            if json_str.endswith(";"):
                json_str = json_str[:-1]
            events = json.loads(json_str)
            break

    if events is None:
        print("  ERROR: CMT_EVENTS no encontrado en js/config.js")
        return

    conn = get_conn()
    conn.execute("DELETE FROM earthquakes WHERE source='cmt'")
    conn.executemany("""
        INSERT INTO earthquakes
            (source, lon, lat, depth, magnitude, year, fault_type,
             strike1, dip1, rake1, strike2, dip2, rake2, label)
        VALUES ('cmt',?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, [
        (e["lo"], e["la"], e["de"], e["mw"],
         e.get("yr", 0), e.get("ft", "O"),
         e.get("s1"), e.get("d1"), e.get("r1"),
         e.get("s2"), e.get("d2"), e.get("r2"),
         e.get("label", ""))
        for e in events
    ])
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM earthquakes WHERE source='cmt'").fetchone()[0]
    conn.close()
    print(f"  CMT Mw>=6:     {n} eventos")


if __name__ == "__main__":
    from backend.database import init_db
    init_db()
    print("Importando datos sísmicos a SQLite...")
    import_usgs_55()
    import_cmt_inline()
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM earthquakes").fetchone()[0]
    conn.close()
    print(f"  Total en DB:   {total} eventos")
    print(f"  DB:            {DB_PATH}")
