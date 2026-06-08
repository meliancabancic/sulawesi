"""
Migra GEM_FAULTS de js/config.js a la tabla gem_faults en SQLite.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_gem_faults
"""
import json, re, sqlite3
from pathlib import Path

BASE    = Path(__file__).parent.parent.parent
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"


def init_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gem_faults (
            id         TEXT PRIMARY KEY,
            fault_type TEXT NOT NULL,
            coords     TEXT NOT NULL   -- JSON [[lon,lat], ...]
        )
    """)
    conn.commit()


def extract_from_config() -> list[dict]:
    text = (BASE / "js" / "config.js").read_text(encoding="utf-8")
    m = re.search(r"const GEM_FAULTS\s*=\s*(\[.*?\]);", text, re.DOTALL)
    if not m:
        raise ValueError("GEM_FAULTS no encontrado en config.js")
    return json.loads(m.group(1))


def run():
    from backend.database import init_db
    init_db()

    conn = sqlite3.connect(DB_PATH)
    init_table(conn)

    faults = extract_from_config()
    conn.execute("DELETE FROM gem_faults")
    conn.executemany(
        "INSERT INTO gem_faults (id, fault_type, coords) VALUES (?, ?, ?)",
        [(f["id"], f["t"], json.dumps(f["c"])) for f in faults]
    )
    conn.commit()

    n = conn.execute("SELECT COUNT(*) FROM gem_faults").fetchone()[0]
    types = dict(conn.execute(
        "SELECT fault_type, COUNT(*) FROM gem_faults GROUP BY fault_type"
    ).fetchall())
    conn.close()

    print(f"  Fallas GEM importadas: {n}")
    for t, c in sorted(types.items()):
        print(f"    {t}: {c}")


if __name__ == "__main__":
    run()
