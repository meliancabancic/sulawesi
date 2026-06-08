# SKILL: data-pipeline

## Activación
Trigger: "filtrar CSV", "convertir a GeoJSON", "descargar dataset", "GVP", "NGL", "IHFC", "WorldHeatFlow", "compilar campos", "bbox filter".

---

## Directorio de salida

Todos los GeoJSON procesados van a `mapa/fuentes/`. Ejecutar scripts desde:
```
c:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\
```

---

## Patrón base: CSV → GeoJSON con bbox filter

```python
import csv, json
from pathlib import Path

def csv_to_geojson(csv_path, lon_col, lat_col, bbox, extra_fields: dict = {}):
    """
    bbox: (lon_min, lat_min, lon_max, lat_max)
    extra_fields: {nombre_salida: nombre_columna_csv}
    """
    features = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lon = float(row[lon_col]); lat = float(row[lat_col])
            except (ValueError, KeyError):
                continue
            if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                continue
            props = {k: row.get(v) for k, v in extra_fields.items()}
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": props
            })
    return {"type": "FeatureCollection", "features": features}

SULAWESI_BBOX = (117.0, -6.0, 130.0, 5.0)
```

---

## Pipelines específicos

### GVP Holocene Volcanoes
Fuente: `volcano.si.edu` → Resources → GVP Volcano List → Download CSV (Holocene)
Columnas relevantes: `Volcano Number`, `Volcano Name`, `Country`, `Primary Volcano Type`,
  `Last Known Eruption`, `Latitude`, `Longitude`, `Elevation (m)`

```python
result = csv_to_geojson(
    "tmp/GVP_Volcano_List_Holocene.csv",
    lon_col="Longitude", lat_col="Latitude",
    bbox=SULAWESI_BBOX,
    extra_fields={
        "name":            "Volcano Name",
        "gvp_id":          "Volcano Number",
        "volcano_type":    "Primary Volcano Type",
        "last_eruption":   "Last Known Eruption",
        "elev_m":          "Elevation (m)"
    }
)
# Agregar pvmbg_type manualmente cruzando con Pratama 2025 Fig. 4c
# Tipos A, B, C según actividad histórica:
#   A = erupción histórica confirmada
#   B = solfataras/fumarolas activas, sin erupción reciente
#   C = sin actividad registrada
for f in result["features"]:
    f["properties"]["pvmbg_type"] = None  # rellenar tras leer Pratama Fig. 4c

Path("fuentes/volcanoes_sulawesi_gvp.geojson").write_text(json.dumps(result, indent=2))
```

### NGL GPS Velocities
Fuente: `geodesy.unr.edu/NGLStationPages/GlobalStationList`
Descargable como tabla HTML o CSV. Buscar columnas: `Sta`, `Lon`, `Lat`, `E (mm/yr)`, `N (mm/yr)`, `U (mm/yr)`.

```python
import math

def build_gps_geojson(csv_path: str, bbox: tuple) -> dict:
    features = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lon = float(row["Lon"]); lat = float(row["Lat"])
                ve = float(row["E (mm/yr)"]); vn = float(row["N (mm/yr)"])
            except (ValueError, KeyError):
                continue
            if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
                continue
            mag = round(math.hypot(ve, vn), 1)
            az  = round(math.degrees(math.atan2(ve, vn)) % 360, 1)
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "station": row.get("Sta", ""),
                    "Ve_mmyr": ve, "Vn_mmyr": vn,
                    "magnitude_mmyr": mag, "azimuth_deg": az,
                    "ref_frame": "ITRF2014"
                }
            })
    return {"type": "FeatureCollection", "features": features}

result = build_gps_geojson("tmp/ngl_velocities.csv", SULAWESI_BBOX)
Path("fuentes/gps_velocities_sulawesi_ngl.geojson").write_text(json.dumps(result, indent=2))
```

### WorldHeatFlow Database
Si la API responde (heatflow.org/api/v1/measurements):
```python
import requests

def fetch_whf(bbox: tuple) -> dict:
    r = requests.get("https://heatflow.org/api/v1/measurements", params={
        "lat_min": bbox[1], "lat_max": bbox[3],
        "lon_min": bbox[0], "lon_max": bbox[2],
        "format": "json"
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    features = []
    for m in data.get("measurements", data.get("results", [])):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [m["lon"], m["lat"]]},
            "properties": {
                "q_val":    m.get("q_val"),      # mW/m²
                "q_unc":    m.get("q_unc"),
                "quality":  m.get("quality"),    # A-E
                "depth_m":  m.get("depth_m"),
                "method":   m.get("method"),
                "source":   "WorldHeatFlow_2024"
            }
        })
    return {"type": "FeatureCollection", "features": features}

result = fetch_whf(SULAWESI_BBOX)
Path("fuentes/heat_flow_whf_sulawesi.geojson").write_text(json.dumps(result, indent=2))
```

Fallback Lucazeau 2019 (CSV del supplementary DOI 10.1029/2019GC008389):
```python
result = csv_to_geojson(
    "tmp/lucazeau2019_NGHF.csv",
    lon_col="lon", lat_col="lat",
    bbox=SULAWESI_BBOX,
    extra_fields={"q_val": "q", "q_unc": "q_unc", "quality": "quality"}
)
Path("fuentes/heat_flow_ihfc_sulawesi.geojson").write_text(json.dumps(result, indent=2))
```

### IRIS FDSN Station (precachear como GeoJSON estático)
```python
import requests

r = requests.get("https://service.iris.edu/fdsnws/station/1/query", params={
    "network": "IA,GE,MN", "minlat": -5, "maxlat": 5,
    "minlon": 117, "maxlon": 130,
    "level": "station", "format": "json"
}, timeout=20)

data = r.json()  # FDSNStationXML convertido a JSON
features = []
for net in data.get("FDSNStationXML", {}).get("Network", []):
    for sta in net.get("Station", []):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [
                float(sta["Longitude"]), float(sta["Latitude"])
            ]},
            "properties": {
                "network": net.get("code", ""),
                "station": sta.get("code", ""),
                "name":    sta.get("Site", {}).get("Name", ""),
                "start":   sta.get("startDate", ""),
                "end":     sta.get("endDate", "")
            }
        })
result = {"type": "FeatureCollection", "features": features}
Path("fuentes/seismic_stations_sulawesi.geojson").write_text(json.dumps(result, indent=2))
```

---

## Convenciones de campos GeoJSON del proyecto

| campo | tipo | descripción |
|-------|------|-------------|
| `name` | str | nombre del elemento |
| `source` | str | paper/dataset de origen (mismo valor que geo_features.source) |
| `layer_type` | str | vocabulario del proyecto |
| `lon`, `lat` | float | en EPSG:4326 |
| magnitudes en mm/año: `Ve_mmyr`, `Vn_mmyr`, `magnitude_mmyr` | float | |
| flujo calórico: `q_val` (mW/m²), `q_unc`, `quality` | float/str | |
| volcanes: `pvmbg_type` (A/B/C), `elev_m`, `last_eruption`, `gvp_id` | | |

---

## Checklist

1. Guardar CSV fuente en `mapa/tmp/` (no comitear)
2. Correr script → GeoJSON en `mapa/fuentes/`
3. Verificar: `python -c "import json; d=json.load(open('fuentes/X.geojson')); print(len(d['features']), 'features')"`
4. Si el GeoJSON tiene ≥5 features en el bbox, proceder con la integración al mapa
5. Actualizar `mapa_plan.json` → tarea correspondiente → `"estado": "implementado"`
