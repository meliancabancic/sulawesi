# SKILL: api-integration

## Activación
Trigger: "integrar API", "nuevo endpoint", "proxy", "agregar fuente externa", nombre de una de las APIs del proyecto (ISC, IRIS, GPlates, ICGEM, WorldHeatFlow, NGL).

---

## Arquitectura del backend

```
mapa/
  backend/
    main.py          ← registra routers con app.include_router(..., prefix="/api")
    database.py      ← get_conn() → sqlite3.Connection con row_factory=sqlite3.Row
    routers/         ← un archivo por dominio; importar en main.py
    sulawesi.db
```

### Patrón de router nuevo

```python
# backend/routers/mi_router.py
from fastapi import APIRouter, Query, HTTPException
from ..database import get_conn
import json, httpx

router = APIRouter()

@router.get("/mi_endpoint")
def mi_endpoint(param: str = Query(...)):
    ...
    return {"type": "FeatureCollection", "features": [...]}
```

Registrar en `main.py`:
```python
from .routers import mi_router
app.include_router(mi_router.router, prefix="/api", tags=["Mi dominio"])
```

### Convenciones de respuesta
- Features geoespaciales → siempre `{"type": "FeatureCollection", "features": [...], "count": N}`
- Cada feature: `{"type": "Feature", "geometry": {...}, "properties": {...}}`
- Errores: `raise HTTPException(status_code, detail)`
- Campos de properties en snake_case; geometry como dict (no string)

---

## Cache para APIs lentas

Para ICGEM y GPlates (latencia ~2-10 s por llamada), cachear resultados:

```python
import functools, json, hashlib
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

def _cache_key(prefix: str, **params) -> Path:
    h = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]
    return CACHE_DIR / f"{prefix}_{h}.json"

def _from_cache(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return None

def _to_cache(path: Path, data):
    path.write_text(json.dumps(data))
```

---

## APIs del proyecto

### ISC Earthquake Catalog
```
GET https://www.isc.ac.uk/fdsnws/event/1/query
  ?format=json&starttime=2000-01-01
  &minlat=-5&maxlat=5&minlon=117&maxlon=130
  &mindepth={mindepth}&maxdepth={maxdepth}&minmag={minmag}
```
Respuesta: `{"features": [...]}` (GeoJSON nativo). Parsear igual que USGS FDSN.
Router sugerido: `backend/routers/catalog_isc.py`; endpoint: `GET /api/catalog/isc`.
Fallback: si ISC no responde, devolver vacío con `{"features": [], "source": "isc_unavailable"}`.

### IRIS FDSN Station
```
GET https://service.iris.edu/fdsnws/station/1/query
  ?network=IA,GE&minlat=-5&maxlat=5&minlon=117&maxlon=130
  &level=station&format=json
```
Respuesta: JSON propio (no GeoJSON). Convertir manualmente a FeatureCollection.
Cachear: las estaciones no cambian frecuentemente — TTL 7 días o GeoJSON estático en `fuentes/`.
Router sugerido: endpoint `GET /api/stations`.

### GPlates Web Service — velocidad de placa
```
POST https://gws.gplates.org/velocity/
Content-Type: application/json
{"points": [[lon, lat], ...], "model": "MULLER2019", "time": 0}
```
Respuesta: `[{"velocity": [Ve, Vn], "plate_id": N}, ...]` (mm/año, ITRF2014).
Convertir: azimuth = atan2(Ve, Vn); magnitude = sqrt(Ve²+Vn²).
Cachear resultado por grilla (la grilla no cambia — tiempo=0 es constante).
Router sugerido: endpoint `GET /api/plate_velocity?grid_step=1.0`.

### ICGEM Calculation Service
```
GET http://icgem.gfz-potsdam.de/calc/
  ?modelname=EGM2008&funcname=gravity_bouguer&lat={lat}&lon={lon}
  &height=0&unit=mgal&outputformat=json
```
O en grilla: parámetros `lat_min`, `lat_max`, `lon_min`, `lon_max`, `step`.
Lento para muchos puntos — cachear por traza (hash de coordenadas).
Alternativa: para el perfil gravitatorio, samplear los TIFFs locales es más rápido (ver `skills/raster-georef.md`).
Router sugerido: endpoint `POST /api/gravity/profile_icgem` (cuerpo: LineString GeoJSON).

### WorldHeatFlow Database
```
GET https://heatflow.org/api/v1/measurements
  ?lat_min=-5&lat_max=5&lon_min=117&lon_max=130&format=json
```
Campos relevantes: `q_val` (mW/m²), `q_unc`, `quality` (A-E), `lat`, `lon`.
Si la API requiere registro o no responde: fallback a Lucazeau 2019 CSV en `fuentes/` (descargar manualmente de DOI 10.1029/2019GC008389).
Cachear: precachear en `fuentes/heat_flow_whf_sulawesi.geojson` al primer hit.
Router sugerido: endpoint `GET /api/heatflow`.

### NGL GPS Velocities
No tiene REST API — descarga CSV de `geodesy.unr.edu/NGLStationPages/GlobalStationList`.
Pipeline: filtrar bbox → descargar velocidades por estación → armar GeoJSON.
Guardar como estático: `fuentes/gps_velocities_sulawesi_ngl.geojson`.
Servir desde `GET /api/gps_velocities` (lee el archivo estático, no hace llamada externa).

---

## Patrón proxy async con httpx

```python
import httpx, asyncio

async def _fetch(url: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()
```

Para endpoints síncronos (FastAPI por defecto): usar `requests` o `httpx.Client()`.
Para endpoints async: usar `async def` en el router + `httpx.AsyncClient`.

---

## Checklist al agregar una API nueva

1. Crear `backend/routers/{nombre}.py` con `router = APIRouter()`
2. Registrar en `main.py` con `app.include_router(..., prefix="/api", tags=[...])`
3. Implementar caché si la API es lenta (ICGEM, GPlates) o estable (NGL, IRIS stations)
4. Definir fallback explícito si la API puede no estar disponible
5. Response siempre FeatureCollection o JSON documentado
6. Agregar entrada en `mapa_plan.json` → sección relevante → `estado: "implementado"`
