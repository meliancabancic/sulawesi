"""
Migra SLAB2_CONTOURS de js/config.js a la tabla slab_contours en SQLite.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_slabs
"""
import json, re, sqlite3
from pathlib import Path

BASE    = Path(__file__).parent.parent.parent
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"


def init_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS slab_contours (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            region  TEXT    NOT NULL,
            depth   INTEGER NOT NULL,
            coords  TEXT    NOT NULL   -- JSON [[lon,lat], ...]
        )
    """)
    conn.commit()


def extract_from_config() -> list[dict]:
    text = (BASE / "js" / "config.js").read_text(encoding="utf-8")
    m = re.search(r"const SLAB2_CONTOURS\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m:
        raise ValueError("SLAB2_CONTOURS no encontrado en config.js")
    return json.loads(m.group(1))


def run():
    from backend.database import init_db
    init_db()

    conn = sqlite3.connect(DB_PATH)
    init_table(conn)

    contours = extract_from_config()
    conn.execute("DELETE FROM slab_contours")
    conn.executemany(
        "INSERT INTO slab_contours (region, depth, coords) VALUES (?, ?, ?)",
        [(c["r"], c["d"], json.dumps(c["c"])) for c in contours]
    )
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM slab_contours").fetchone()[0]
    conn.close()
    print(f"  Contornos SLAB2 importados: {n}")


if __name__ == "__main__":
    run()
