"""
Descarga USGS Mw 5.5-5.9 con mecanismos focales para la región de Sulawesi.
Reanuda desde donde quedó: carga los eventos ya descargados y solo busca los faltantes.
"""
import urllib.request, json, os, time, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

OUT = os.path.join(os.path.dirname(__file__), 'fuentes', 'gcmt55_sulawesi.json')
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; research-script/1.0)'}

def fault_type(rake):
    r = rake % 360
    if r > 180: r -= 360
    if abs(r) <= 45 or abs(r) >= 135: return 'S'
    if 45 < r <= 135: return 'T'
    return 'N'

def fetch_json(url, retries=5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)   # backoff: 2, 4, 8, 16s
            time.sleep(wait)

def process_event(feat):
    try:
        det = fetch_json(feat['properties']['detail'])
        props = det['properties']
        coords = det['geometry']['coordinates']
        lo = round(coords[0], 3)
        la = round(coords[1], 3)
        de = round(coords[2], 1)
        mw = round(props.get('mag', 0), 1)
        yr = datetime.datetime.fromtimestamp(props['time'] / 1000, tz=datetime.timezone.utc).year
        mt_list = props.get('products', {}).get('moment-tensor', [])
        if not mt_list:
            return None
        mt_props = mt_list[0].get('properties', {})
        s1 = mt_props.get('nodal-plane-1-strike')
        d1 = mt_props.get('nodal-plane-1-dip')
        r1 = mt_props.get('nodal-plane-1-rake')
        s2 = mt_props.get('nodal-plane-2-strike')
        d2 = mt_props.get('nodal-plane-2-dip')
        r2 = mt_props.get('nodal-plane-2-rake')
        if any(x is None for x in [s1, d1, r1, s2, d2, r2]):
            return None
        s1,d1,r1,s2,d2,r2 = [int(round(float(x))) for x in (s1,d1,r1,s2,d2,r2)]
        derived_dep = mt_props.get('derived-depth')
        if derived_dep:
            try: de = round(float(derived_dep), 1)
            except: pass
        return {
            'lo': lo, 'la': la, 'de': de,
            'mw': mw, 'yr': yr,
            'ft': fault_type(r1),
            's1': s1, 'd1': d1, 'r1': r1,
            's2': s2, 'd2': d2, 'r2': r2,
            'label': ''
        }
    except Exception:
        return None

# Cargar eventos ya descargados
existing = []
existing_keys = set()
if os.path.exists(OUT):
    with open(OUT) as f:
        existing = json.load(f)
    existing_keys = {(e['lo'], e['la'], e['yr']) for e in existing}
    print(f"Eventos ya descargados: {len(existing)}")

# Obtener lista completa
list_url = (
    'https://earthquake.usgs.gov/fdsnws/event/1/query'
    '?format=geojson'
    '&minmagnitude=5.5&maxmagnitude=5.9'
    '&minlatitude=-12&maxlatitude=7'
    '&minlongitude=114&maxlongitude=132'
    '&starttime=1990-01-01&endtime=2026-12-31'
    '&producttype=moment-tensor'
    '&orderby=time-asc'
)
print("Obteniendo lista completa...", flush=True)
ev_list = fetch_json(list_url)
features = ev_list['features']
print(f"Total en catálogo: {len(features)}", flush=True)

# Filtrar solo los que faltan (por id de evento USGS)
existing_ids = set()
# Re-descargar sin filtro por coords para evitar falsos positivos en deduplicación
# Identificamos faltantes por posición en la lista vs lo que tenemos
# Más seguro: descargar todos y deduplicar al final
pending = features   # intentar todos; process_event devuelve None si ya no tiene MT

print(f"Procesando {len(pending)} eventos (los que ya están se deduplicarán)...", flush=True)

new_results = []
done = 0
errors = 0
with ThreadPoolExecutor(max_workers=8) as pool:   # 8 workers, más conservador
    futs = {pool.submit(process_event, f): f for f in pending}
    for fut in as_completed(futs):
        done += 1
        try:
            ev = fut.result()
            if ev:
                key = (ev['lo'], ev['la'], ev['yr'])
                if key not in existing_keys:
                    new_results.append(ev)
                    existing_keys.add(key)
        except Exception:
            errors += 1
        if done % 50 == 0:
            print(f"  {done}/{len(pending)} — nuevos: {len(new_results)}, errores: {errors}", flush=True)

all_events = existing + new_results
all_events.sort(key=lambda e: (e['yr'], e['lo'], e['la']))

print(f"\nTotal final: {len(all_events)} eventos ({len(new_results)} nuevos, {errors} errores)")

with open(OUT, 'w') as f:
    json.dump(all_events, f, separators=(',', ':'))
print(f"Guardado: {OUT}")
