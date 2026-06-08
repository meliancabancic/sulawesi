"""
Importa todos los GeoJSONs de fuentes/ y NEW_FAULTS de config.js a la tabla geo_features.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_geodata
"""
import json, re, sqlite3
from pathlib import Path

BASE    = Path(__file__).parent.parent.parent
DB_PATH = Path(__file__).parent.parent / "sulawesi.db"
FUENTES = BASE / "fuentes"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def import_geojsons(conn: sqlite3.Connection) -> int:
    total = 0
    for path in sorted(FUENTES.glob("*.geojson")):
        source = path.stem
        data   = json.loads(path.read_text(encoding="utf-8"))
        meta   = data.get("metadata", {})
        year   = None
        # Try to extract year from source_paper field
        m = re.search(r'\b(19|20)\d{2}\b', meta.get("source_paper", ""))
        if m:
            year = int(m.group())

        rows = []
        for feat in data.get("features", []):
            props      = feat.get("properties", {}) or {}
            layer_type = props.get("category", "structure")
            name       = props.get("name") or props.get("label") or props.get("id")
            geom_str   = json.dumps(feat.get("geometry"))
            extra      = {k: v for k, v in props.items()
                          if k not in ("category", "name", "label", "id")}
            rows.append((source, layer_type, name, geom_str, json.dumps(extra), year))

        conn.executemany(
            "INSERT INTO geo_features (source, layer_type, name, geometry, properties, year) "
            "VALUES (?,?,?,?,?,?)",
            rows
        )
        print(f"  {source}: {len(rows)} features")
        total += len(rows)
    return total


def import_new_faults(conn: sqlite3.Connection) -> int:
    text = (BASE / "js" / "config.js").read_text(encoding="utf-8")
    m = re.search(r"const NEW_FAULTS\s*=\s*(\{.*?\});", text, re.DOTALL)
    if not m:
        print("  NEW_FAULTS: not found in config.js")
        return 0

    faults = json.loads(m.group(1))
    rows   = []
    for fid, f in faults.items():
        coords    = f.get("coords", [])
        geom      = json.dumps({"type": "LineString", "coordinates": coords})
        layer_type = "fault"
        name      = f.get("name", fid)
        extra     = {k: v for k, v in f.items()
                     if k not in ("id", "name", "coords")}
        # Try to parse year from source string
        year = None
        src_str = f.get("source", "")
        ym = re.search(r'\b(20)\d{2}\b', src_str)
        if ym:
            year = int(ym.group())
        rows.append(("new_faults", layer_type, name, geom, json.dumps(extra), year))

    conn.executemany(
        "INSERT INTO geo_features (source, layer_type, name, geometry, properties, year) "
        "VALUES (?,?,?,?,?,?)",
        rows
    )
    print(f"  new_faults: {len(rows)} features")
    return len(rows)


def run():
    from backend.database import init_db
    init_db()

    conn = get_conn()
    conn.execute("DELETE FROM geo_features")
    conn.execute("DELETE FROM canonical_structures")
    conn.execute("DELETE FROM match_proposals")

    n_geo  = import_geojsons(conn)
    n_nf   = import_new_faults(conn)
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM geo_features").fetchone()[0]
    by_lt = conn.execute(
        "SELECT layer_type, COUNT(*) FROM geo_features GROUP BY layer_type ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()

    print(f"\nTotal geo_features: {total}  ({n_geo} de GeoJSONs + {n_nf} de NEW_FAULTS)")
    print("Por layer_type:")
    for row in by_lt:
        print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    run()
