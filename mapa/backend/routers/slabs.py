from fastapi import APIRouter, Query
from ..database import get_conn
import json

router = APIRouter()


@router.get("/slabs/slab2")
def get_slab2(
    region: str | None = Query(None, description="Filtrar por región (Cotabato, Halmahera, Sulawesi, Sumatra/Java)"),
    max_depth: int     = Query(700, alias="maxDepth"),
):
    conn = get_conn()
    if region:
        rows = conn.execute(
            "SELECT id, region, depth, coords FROM slab_contours WHERE region=? AND depth<=? ORDER BY region, depth",
            (region, max_depth)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, region, depth, coords FROM slab_contours WHERE depth<=? ORDER BY region, depth",
            (max_depth,)
        ).fetchall()
    conn.close()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": json.loads(r["coords"])},
            "properties": {
                "id":     r["id"],
                "region": r["region"],
                "depth":  r["depth"],
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}
