"""
Migra GVP_VOLCANOES de js/config.js a la tabla volcanoes en SQLite.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_volcanoes
"""
import json, re, sqlite3
from pathlib import Path

BASE    = Path(__file__).parent.parent.parent
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"


def init_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS volcanoes (
            id    TEXT PRIMARY KEY,
            name  TEXT NOT NULL,
            lon   REAL NOT NULL,
            lat   REAL NOT NULL,
            elev  INTEGER,
            type  TEXT,
            arc   TEXT
        )
    """)
    conn.commit()


def extract_from_config() -> list[dict]:
    text = (BASE / "js" / "config.js").read_text(encoding="utf-8")
    m = re.search(r"const GVP_VOLCANOES\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m:
        raise ValueError("GVP_VOLCANOES no encontrado en config.js")
    return json.loads(m.group(1))


def run():
    from backend.database import init_db
    init_db()

    conn = sqlite3.connect(DB_PATH)
    init_table(conn)

    volcanoes = extract_from_config()
    conn.execute("DELETE FROM volcanoes")
    conn.executemany(
        "INSERT INTO volcanoes (id, name, lon, lat, elev, type, arc) VALUES (?,?,?,?,?,?,?)",
        [(v["id"], v["name"], v["lon"], v["lat"],
          v.get("elev"), v.get("type"), v.get("arc")) for v in volcanoes]
    )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM volcanoes").fetchone()[0]
    conn.close()
    print(f"  Volcanes importados: {n}")


if __name__ == "__main__":
    run()
