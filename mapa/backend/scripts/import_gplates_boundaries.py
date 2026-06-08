"""
Importa trazos de limites de placas del GPlates Web Service (present-day, time=0)
a la tabla geo_features como fuente 'gplates_topology_present'.

Filtra la region Sulawesi (lon 115-135 E, lat -10 a 6 N).
Solo importa SubductionZone, Transform y OrogenicBelt.
Omite CLONE artifacts, InferredPaleoBoundary y MidOceanRidge.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_gplates_boundaries
"""
import json, sqlite3, urllib.request
from pathlib import Path

DB_PATH     = Path(__file__).parent.parent / "sulawesi.db"
SOURCE      = "gplates_topology_present"
GPLATES_URL = "https://gws.gplates.org/topology/plate_boundaries?time=0"

# GPlates type -> our layer_type
TYPE_MAP = {
    "SubductionZone": "subduction_zone",
    "Transform":      "fault",
    "OrogenicBelt":   "fold_thrust_belt",
}

# Region de interes
LON_MIN, LON_MAX = 115.0, 135.0
LAT_MIN, LAT_MAX = -10.0,   6.0


def in_region(coords: list) -> bool:
    for pt in coords:
        if isinstance(pt[0], list):
            if in_region(pt):
                return True
        elif LON_MIN <= pt[0] <= LON_MAX and LAT_MIN <= pt[1] <= LAT_MAX:
            return True
    return False


def flatten_coords(geom: dict) -> list | None:
    """Devuelve lista de coordenadas [lon, lat] para LineString o primer seg de MultiLineString."""
    t = geom.get("type")
    c = geom.get("coordinates", [])
    if t == "LineString":
        return c
    if t == "MultiLineString":
        return c[0] if c else None
    return None


def run():
    print(f"Descargando {GPLATES_URL} ...")
    with urllib.request.urlopen(GPLATES_URL, timeout=30) as r:
        data = json.loads(r.read())

    feats = data.get("features", [])
    print(f"Total features globales: {len(feats)}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Verificar si ya fue importado
    existing = conn.execute(
        "SELECT COUNT(*) FROM geo_features WHERE source=?", (SOURCE,)
    ).fetchone()[0]
    if existing:
        print(f"AVISO: ya existen {existing} features de '{SOURCE}' en la DB.")
        resp = input("Reimportar? (s/N): ").strip().lower()
        if resp != "s":
            print("Abortado.")
            conn.close()
            return
        conn.execute("DELETE FROM geo_features WHERE source=?", (SOURCE,))
        print(f"  Eliminados {existing} features previos.")

    # Agrupar por nombre para numerar segmentos
    name_counts: dict[str, int] = {}
    to_insert = []

    for f in feats:
        p    = f.get("properties", {})
        btype = p.get("type", "")
        name  = p.get("name", "").strip()
        geom  = f.get("geometry", {})
        coords = geom.get("coordinates", [])

        # Filtros
        if btype not in TYPE_MAP:
            continue
        if "CLONE" in name or "InferredPaleo" in btype:
            continue
        if not in_region(coords):
            continue

        layer_type = TYPE_MAP[btype]
        coords_flat = flatten_coords(geom)
        if not coords_flat or len(coords_flat) < 2:
            continue

        # Nombre unico por segmento
        name_counts[name] = name_counts.get(name, 0) + 1
        seg_name = name  # se ajusta despues con el indice real

        polarity = p.get("polarity", "")
        notes = btype
        if polarity:
            notes += f" ({polarity}-dipping)"

        geometry_json = json.dumps({"type": "LineString", "coordinates": coords_flat})
        to_insert.append((name, SOURCE, layer_type, geometry_json, json.dumps({"boundary_type": btype, "polarity": polarity})))

    # Re-numerar segmentos con el mismo nombre
    seen: dict[str, int] = {}
    rows = []
    for name, source, layer_type, geometry_json, props_json in to_insert:
        seen[name] = seen.get(name, 0) + 1
        total = name_counts[name]
        seg_label = f" - seg {seen[name]}/{total}" if total > 1 else ""
        full_name = name + seg_label
        rows.append((full_name, source, layer_type, geometry_json, None, props_json))

    conn.executemany(
        "INSERT INTO geo_features (name, source, layer_type, geometry, canonical_id, properties) "
        "VALUES (?,?,?,?,?,?)",
        rows
    )
    conn.commit()

    # Resumen
    print(f"\nImportados: {len(rows)} features de '{SOURCE}'")
    from collections import Counter
    counts = Counter(r[2] for r in rows)
    for lt, n in sorted(counts.items()):
        print(f"  {lt}: {n}")

    print("\nFeatures importados:")
    for r in conn.execute(
        "SELECT id, name, layer_type FROM geo_features WHERE source=? ORDER BY layer_type, name",
        (SOURCE,)
    ).fetchall():
        print(f"  id={r['id']} [{r['layer_type']}] {r['name']}")

    conn.close()


if __name__ == "__main__":
    run()
