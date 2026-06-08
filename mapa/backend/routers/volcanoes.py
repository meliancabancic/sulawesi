from fastapi import APIRouter
from ..database import get_conn

router = APIRouter()


@router.get("/volcanoes")
def get_volcanoes():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, lon, lat, elev, type, arc FROM volcanoes ORDER BY name"
    ).fetchall()
    conn.close()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "id":   r["id"],
                "name": r["name"],
                "lon":  r["lon"],
                "lat":  r["lat"],
                "elev": r["elev"],
                "type": r["type"],
                "arc":  r["arc"],
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}
