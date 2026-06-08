import math
from fastapi import APIRouter, Query
from ..database import get_conn

router = APIRouter()


@router.get("/earthquakes")
def get_earthquakes(
    min_mag:    float = Query(5.5,  alias="minMag"),
    max_mag:    float = Query(9.9,  alias="maxMag"),
    start_year: int   = Query(1976, alias="startYear"),
    end_year:   int   = Query(2026, alias="endYear"),
    min_depth:  float = Query(0,    alias="minDepth"),
    max_depth:  float = Query(700,  alias="maxDepth"),
    fault_types: str  = Query("T,N,S,O", alias="faultTypes"),
    sources:    str   = Query("cmt,usgs", alias="sources"),
):
    ft_list  = [f.strip() for f in fault_types.split(",") if f.strip()]
    src_list = [s.strip() for s in sources.split(",")     if s.strip()]

    ph_ft  = ",".join("?" * len(ft_list))
    ph_src = ",".join("?" * len(src_list))

    conn = get_conn()
    rows = conn.execute(f"""
        SELECT lon, lat, depth, magnitude, year, fault_type,
               strike1, dip1, rake1, strike2, dip2, rake2, label
        FROM earthquakes
        WHERE magnitude  BETWEEN ? AND ?
          AND year       BETWEEN ? AND ?
          AND depth      BETWEEN ? AND ?
          AND fault_type IN ({ph_ft})
          AND source     IN ({ph_src})
        ORDER BY year, lon
    """, [min_mag, max_mag, start_year, end_year,
          min_depth, max_depth, *ft_list, *src_list]).fetchall()
    conn.close()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
            "properties": {
                "lo": r["lon"],  "la": r["lat"],  "de": r["depth"],
                "mw": r["magnitude"], "yr": r["year"], "ft": r["fault_type"],
                "s1": r["strike1"], "d1": r["dip1"], "r1": r["rake1"],
                "s2": r["strike2"], "d2": r["dip2"], "r2": r["rake2"],
                "label": r["label"] or "",
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}


def _haversine_km(lon1, lat1, lon2, lat2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _point_to_line_dist_km(px, py, ax, ay, bx, by):
    """Signed perpendicular distance (km) from point P to segment AB, plus along-strike distance."""
    ab_len = _haversine_km(ax, ay, bx, by)
    if ab_len < 0.001:
        return _haversine_km(px, py, ax, ay), 0.0
    # Unit vector along profile (Cartesian approx at small scales)
    dx = bx - ax; dy = by - ay
    length = math.sqrt(dx*dx + dy*dy)
    ux = dx/length; uy = dy/length
    # Vector from A to P
    apx = px - ax; apy = py - ay
    # Along-profile projected distance (degrees), convert to km
    along_deg = apx*ux + apy*uy
    along_km = along_deg / length * ab_len
    # Perpendicular component (degrees), convert to km
    perp_deg = apx*(-uy) + apy*ux
    perp_km = perp_deg / length * ab_len
    return abs(perp_km), along_km


@router.get("/earthquakes/profile")
def get_profile(
    lon1: float = Query(...), lat1: float = Query(...),
    lon2: float = Query(...), lat2: float = Query(...),
    half_width: float = Query(30.0, alias="halfWidth"),
    min_mag:    float = Query(4.0,  alias="minMag"),
    max_depth:  float = Query(700,  alias="maxDepth"),
):
    """Returns earthquakes projected onto a vertical cross-section defined by (lon1,lat1)-(lon2,lat2).
    half_width: corridor width in km on each side of the profile.
    Response: list of {dist_km, depth, mw, ft} sorted by dist_km.
    """
    # Broad bbox to pre-filter DB rows
    min_lon = min(lon1, lon2) - half_width/100
    max_lon = max(lon1, lon2) + half_width/100
    min_lat = min(lat1, lat2) - half_width/100
    max_lat = max(lat1, lat2) + half_width/100

    conn = get_conn()
    rows = conn.execute("""
        SELECT lon, lat, depth, magnitude, fault_type
        FROM earthquakes
        WHERE magnitude >= ?
          AND depth <= ?
          AND lon BETWEEN ? AND ?
          AND lat BETWEEN ? AND ?
    """, [min_mag, max_depth, min_lon, max_lon, min_lat, max_lat]).fetchall()
    conn.close()

    profile_len = _haversine_km(lon1, lat1, lon2, lat2)
    points = []
    for r in rows:
        perp, along = _point_to_line_dist_km(r["lon"], r["lat"], lon1, lat1, lon2, lat2)
        if perp <= half_width and 0 <= along <= profile_len:
            points.append({
                "dist_km":  round(along, 2),
                "depth":    round(r["depth"], 1),
                "mw":       r["magnitude"],
                "ft":       r["fault_type"] or "O",
                "lon":      round(r["lon"], 4),
                "lat":      round(r["lat"], 4),
            })
    points.sort(key=lambda p: p["dist_km"])
    return {"profile_km": round(profile_len, 1), "half_width_km": half_width, "points": points, "count": len(points)}
