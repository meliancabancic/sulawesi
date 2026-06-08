from fastapi import APIRouter, Query
from ..database import get_conn
import json

router = APIRouter()


@router.get("/faults/gem")
def get_gem_faults(
    fault_type: str | None = Query(None, alias="faultType", description="Filtrar por tipo (Reverse, Dextral, Subduction_Thrust…)"),
):
    conn = get_conn()
    if fault_type:
        rows = conn.execute(
            "SELECT id, fault_type, coords FROM gem_faults WHERE fault_type=? ORDER BY id",
            (fault_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, fault_type, coords FROM gem_faults ORDER BY id"
        ).fetchall()
    conn.close()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": json.loads(r["coords"])},
            "properties": {
                "id":         r["id"],
                "fault_type": r["fault_type"],
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}
