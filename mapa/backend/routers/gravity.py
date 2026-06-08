from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import math, json
import numpy as np

router = APIRouter()

FUENTES = Path(__file__).parent.parent.parent / "fuentes"
_grids = {}  # cache: key -> (array, meta)

def _load_grid(key: str):
    if key in _grids:
        return _grids[key]
    meta_path = FUENTES / "grav_meta.json"
    npy_path  = FUENTES / f"grav_{key}.npy"
    if not meta_path.exists() or not npy_path.exists():
        raise HTTPException(503, f"Datos de gravedad no encontrados en fuentes/ ({npy_path.name})")
    with open(meta_path) as f:
        meta = json.load(f)[key]
    arr = np.load(npy_path)
    _grids[key] = (arr, meta)
    return arr, meta


def _sample_grid(arr, meta, lon, lat):
    """Bilinear interpolation. Returns None si fuera de rango."""
    a, b, c, d, e, f = meta["transform"]
    # col = (lon - c) / a,  row = (lat - f) / e
    col_f = (lon - c) / a
    row_f = (lat - f) / e
    nrows, ncols = arr.shape
    if col_f < 0 or col_f >= ncols - 1 or row_f < 0 or row_f >= nrows - 1:
        return None
    r0, c0 = int(row_f), int(col_f)
    dr, dc = row_f - r0, col_f - c0
    v = (arr[r0,   c0  ] * (1-dr) * (1-dc)
       + arr[r0,   c0+1] * (1-dr) * dc
       + arr[r0+1, c0  ] * dr     * (1-dc)
       + arr[r0+1, c0+1] * dr     * dc)
    nd = meta.get("nodata")
    if nd is not None and abs(float(v) - nd) < 1e-6:
        return None
    return round(float(v), 2)


class ProfileRequest(BaseModel):
    coords: list[list[float]]
    n_points: int = 100


def _haversine_km(p1, p2):
    R = 6371.0
    la1, lo1 = math.radians(p1[1]), math.radians(p1[0])
    la2, lo2 = math.radians(p2[1]), math.radians(p2[0])
    dla, dlo = la2 - la1, lo2 - lo1
    a = math.sin(dla/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlo/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _interpolate_line(coords, n):
    segs, total = [], 0.0
    for i in range(len(coords)-1):
        d = _haversine_km(coords[i], coords[i+1])
        segs.append(d); total += d
    if total == 0 or n < 2:
        return coords[:1]
    step = total / (n - 1)
    pts, acc, si, sacc = [coords[0]], 0.0, 0, 0.0
    for _ in range(n - 2):
        target = len(pts) * step
        while si < len(segs):
            if sacc + segs[si] >= target - acc + 1e-9:
                t = (target - acc - sacc) / segs[si]
                p1, p2 = coords[si], coords[si+1]
                pts.append([p1[0]+t*(p2[0]-p1[0]), p1[1]+t*(p2[1]-p1[1])])
                break
            sacc += segs[si]; acc += segs[si]; si += 1
    pts.append(coords[-1])
    return pts


@router.post("/gravity/profile")
def gravity_profile(req: ProfileRequest):
    if len(req.coords) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 puntos")

    arr_b, meta_b = _load_grid("bouguer")
    arr_f, meta_f = _load_grid("freeair")

    pts   = _interpolate_line(req.coords, min(req.n_points, 200))
    dists = [0.0]
    for i in range(1, len(pts)):
        dists.append(dists[-1] + _haversine_km(pts[i-1], pts[i]))

    bouguer = [_sample_grid(arr_b, meta_b, p[0], p[1]) for p in pts]
    freeair = [_sample_grid(arr_f, meta_f, p[0], p[1]) for p in pts]

    return {
        "dist_km":  [round(d, 3) for d in dists],
        "bouguer":  bouguer,
        "freeair":  freeair,
        "lon":      [round(p[0], 4) for p in pts],
        "lat":      [round(p[1], 4) for p in pts],
        "n":        len(pts),
        "total_km": round(dists[-1], 2),
    }
