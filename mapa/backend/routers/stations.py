from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

IRIS_URL = "https://service.iris.edu/fdsnws/station/1/query"
BBOX = dict(minlatitude=-5, maxlatitude=5, minlongitude=117, maxlongitude=130)
TIMEOUT = 20.0

# Fallback estático — estaciones BMKG/GEOFON conocidas en Sulawesi
STATIC_STATIONS = [
    {"code": "LUWI", "network": "IA", "name": "Luwuk",         "lon": 122.789, "lat": -1.038},
    {"code": "PMBI", "network": "IA", "name": "Palu-Mamboro",  "lon": 119.871, "lat":  0.895},
    {"code": "TOLI2","network": "IA", "name": "Toli-Toli",     "lon": 120.791, "lat":  1.121},
    {"code": "MANU", "network": "IA", "name": "Manado",        "lon": 124.840, "lat":  1.553},
    {"code": "WORI", "network": "IA", "name": "Wori",          "lon": 124.861, "lat":  1.573},
    {"code": "KMAI", "network": "IA", "name": "Kotamobagu",    "lon": 124.307, "lat":  0.737},
    {"code": "TNTI", "network": "IA", "name": "Tentena",       "lon": 120.637, "lat": -1.738},
    {"code": "PALU", "network": "IA", "name": "Palu",          "lon": 119.855, "lat": -0.898},
    {"code": "MKSR", "network": "IA", "name": "Makassar",      "lon": 119.430, "lat": -5.148},
    {"code": "MASI", "network": "IA", "name": "Masamba",       "lon": 120.328, "lat": -2.551},
    {"code": "MMRI", "network": "IA", "name": "Mamuju",        "lon": 118.887, "lat": -2.682},
    {"code": "BKSI", "network": "IA", "name": "Bitung/Klabat", "lon": 125.188, "lat":  1.450},
    {"code": "GLMI", "network": "IA", "name": "Gorontalo",     "lon": 123.059, "lat":  0.550},
    {"code": "SOEI", "network": "IA", "name": "Soe/Timor",     "lon": 124.284, "lat": -9.863},
    {"code": "GSI",  "network": "GE", "name": "Gorontalo (GEOFON)", "lon": 123.066, "lat":  0.534},
]


def _to_geojson(stations: list[dict]) -> dict:
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
            "properties": {
                "code":    s["code"],
                "network": s["network"],
                "name":    s.get("name", s["code"]),
                "lon":     s["lon"],
                "lat":     s["lat"],
            },
        }
        for s in stations
    ]
    return {"type": "FeatureCollection", "features": features,
            "count": len(features), "source": "IRIS FDSN"}


@router.get("/stations")
async def get_stations():
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(IRIS_URL, params={
                **BBOX,
                "network": "IA,GE",
                "level":   "station",
                "format":  "json",
            })
            resp.raise_for_status()
            data = resp.json()

        stations = []
        for net in data.get("FDSNStationXML", {}).get("Network", []):
            net_code = net.get("code", "")
            for sta in net.get("Station", []):
                lon = sta.get("Longitude") or sta.get("longitude")
                lat = sta.get("Latitude")  or sta.get("latitude")
                if lon is None or lat is None:
                    continue
                stations.append({
                    "code":    sta.get("code", sta.get("stationCode", "")),
                    "network": net_code,
                    "name":    sta.get("Site", {}).get("Name", "") or sta.get("code", ""),
                    "lon":     float(lon),
                    "lat":     float(lat),
                })

        if stations:
            return _to_geojson(stations)
    except Exception:
        pass

    # Fallback estático si IRIS no responde o devuelve formato inesperado
    return {**_to_geojson(STATIC_STATIONS), "source": "static_fallback"}
