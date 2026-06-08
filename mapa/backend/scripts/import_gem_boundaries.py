"""
Importa trazas de límites de placa/microplaca que se muestran en el mapa
pero no están en geo_features:
  - sang_custom  : GEM f115 — Fosa Sangihe (hardcodeada en layers.js)
  - halm_custom  : GEM f116 — Fosa Halmahera (hardcodeada en layers.js)
  - GEM NST      : segmentos f19-f24 concatenados (North Sulawesi Trench)
  - sorong_main  : Falla de Sorong principal (GEM API)
  - sorong_s     : Falla de Sorong sur (GEM API)
  - gorontalo    : Falla de Gorontalo (GEM API)

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.import_gem_boundaries
"""
import json, sqlite3, urllib.request
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "sulawesi.db"

# ── Trazas hardcodeadas de layers.js ──────────────────────────────────────────

SANG_CUSTOM_COORDS = [
    [124.876,0.297],[125.055,0.52],[125.28,0.856],[125.498,1.13],
    [125.59,1.553],[125.682,1.814],[125.75,2.298],[125.842,2.485],
    [125.888,2.578],[125.888,2.911],[125.98,3.071],[126.16,3.429],
    [126.325,3.755],[126.473,4.131],[126.583,4.437],[126.629,5.2]
]

HALM_CUSTOM_COORDS = [
    [127.149,-0.995],[126.845,-0.489],[126.819,-0.256],[126.772,0.053],
    [126.772,0.251],[126.845,0.406],[126.892,0.704],[127.005,1.176],
    [127.195,1.6],[127.376,1.838],[127.422,2.017],[127.517,2.344],
    [127.588,2.578],[127.588,3.117],[127.634,3.227],[127.563,3.522],
    [127.493,3.884],[127.422,4.391],[127.447,4.706],[127.493,5.107],
    [127.563,5.449]
]

# IDs GEM que forman el North Sulawesi Trench (en orden W→E)
GEM_NST_IDS_ORDERED = ['f24','f23','f22','f21','f20','f19']

# IDs GEM de fallas de límite de placa a importar individualmente
GEM_KEY_FAULT_IDS = {
    'sorong_main': {'name': 'Sorong Fault Zone — principal', 'layer_type': 'fault'},
    'sorong_s':    {'name': 'Sorong Fault Zone — ramal sur', 'layer_type': 'fault'},
    'gorontalo':   {'name': 'Gorontalo Fault',               'layer_type': 'fault'},
    'tolo_thrust': {'name': 'Tolo Thrust',                   'layer_type': 'fault'},
}


def fetch_gem():
    url = "http://localhost:8000/api/faults/gem"
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)


def already_imported(conn, source, name_fragment):
    row = conn.execute(
        "SELECT id FROM geo_features WHERE source=? AND name LIKE ?",
        (source, f"%{name_fragment}%")
    ).fetchone()
    return row is not None


def insert_feature(conn, source, layer_type, name, coords):
    geom = json.dumps({"type": "LineString", "coordinates": coords})
    conn.execute(
        "INSERT INTO geo_features (source, layer_type, name, geometry) VALUES (?,?,?,?)",
        (source, layer_type, name, geom)
    )
    print(f"  + Importado: [{source}] {name}  ({len(coords)} pts)")


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("Importando trazas GEM de límites de placa...")

    # 1. sang_custom
    if not already_imported(conn, 'gem_global_active_faults', 'Sangihe'):
        insert_feature(conn, 'gem_global_active_faults', 'subduction_zone',
                       'Sangihe Subduction Zone (GEM f115)',
                       SANG_CUSTOM_COORDS)
    else:
        print("  = sang_custom ya existe")

    # 2. halm_custom
    if not already_imported(conn, 'gem_global_active_faults', 'Halmahera'):
        insert_feature(conn, 'gem_global_active_faults', 'subduction_zone',
                       'Halmahera Subduction Zone (GEM f116)',
                       HALM_CUSTOM_COORDS)
    else:
        print("  = halm_custom ya existe")

    # 3. Fetch GEM API
    print("Fetching GEM API...")
    try:
        gem = fetch_gem()
    except Exception as e:
        print(f"  ERROR fetching GEM API: {e}")
        conn.close()
        return

    feat_by_id = {f['properties']['id']: f for f in gem['features']}

    # 4. NST: concatenar f19-f24 en orden W→E
    if not already_imported(conn, 'gem_global_active_faults', 'NST'):
        nst_coords = []
        for fid in GEM_NST_IDS_ORDERED:
            f = feat_by_id.get(fid)
            if not f:
                print(f"  WARNING: GEM {fid} no encontrado")
                continue
            coords = f['geometry']['coordinates']
            if not nst_coords:
                nst_coords.extend(coords)
            else:
                # Evitar duplicar el punto de unión
                if coords[0] != nst_coords[-1]:
                    nst_coords.extend(coords)
                else:
                    nst_coords.extend(coords[1:])
        if nst_coords:
            insert_feature(conn, 'gem_global_active_faults', 'subduction_zone',
                           'North Sulawesi Trench — GEM f19-f24',
                           nst_coords)
    else:
        print("  = GEM NST ya existe")

    # 5. Fallas de límite de placa individuales
    for gem_id, meta in GEM_KEY_FAULT_IDS.items():
        if already_imported(conn, 'gem_global_active_faults', meta['name'][:15]):
            print(f"  = {gem_id} ya existe")
            continue
        f = feat_by_id.get(gem_id)
        if not f:
            print(f"  WARNING: GEM {gem_id} no encontrado en API")
            continue
        coords = f['geometry']['coordinates']
        insert_feature(conn, 'gem_global_active_faults',
                       meta['layer_type'], meta['name'], coords)

    conn.commit()
    total = conn.execute(
        "SELECT COUNT(*) FROM geo_features WHERE source='gem_global_active_faults'"
    ).fetchone()[0]
    conn.close()
    print(f"\nTotal features gem_global_active_faults en DB: {total}")


if __name__ == "__main__":
    run()
