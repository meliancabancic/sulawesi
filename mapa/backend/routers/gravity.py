from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import math

router = APIRouter()

FUENTES = Path(__file__).parent.parent.parent / "fuentes"
BOUGUER_TIF  = FUENTES / "Bouguer.tiff"
FREEAIR_TIF  = FUENTES / "Anomalía_Aire_Libre.tiff"


class ProfileRequest(BaseModel):
    coords: list[list[float]]   # [[lon,lat], [lon,lat], ...]
    n_points: int = 100


def _haversine_km(p1, p2):
    R = 6371.0
    la1, lo1 = math.radians(p1[1]), math.radians(p1[0])
    la2, lo2 = math.radians(p2[1]), math.radians(p2[0])
    dla, dlo = la2 - la1, lo2 - lo1
    a = math.sin(dla/2)**2 + math.cos(la1)*math.cos(la2)*math.sin(dlo/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def _interpolate_line(coords, n):
    """Interpola n puntos equidistantes a lo largo de una polilínea."""
    segs = []
    total = 0.0
    for i in range(len(coords)-1):
        d = _haversine_km(coords[i], coords[i+1])
        segs.append(d); total += d

    if total == 0 or n < 2:
        return coords[:1]

    step = total / (n - 1)
    pts, acc, si, sacc = [coords[0]], 0.0, 0, 0.0

    for _ in range(n - 2):
        target = (len(pts)) * step
        while si < len(segs):
            if sacc + segs[si] >= target - acc + 1e-9:
                t = (target - acc - sacc) / segs[si]
                p1, p2 = coords[si], coords[si+1]
                pts.append([p1[0] + t*(p2[0]-p1[0]), p1[1] + t*(p2[1]-p1[1])])
                break
            sacc += segs[si]; acc += segs[si]; si += 1

    pts.append(coords[-1])
    return pts


@router.post("/gravity/profile")
def gravity_profile(req: ProfileRequest):
    if len(req.coords) < 2:
        raise HTTPException(400, "Se necesitan al menos 2 puntos")
    if not BOUGUER_TIF.exists() or not FREEAIR_TIF.exists():
        raise HTTPException(503, "TIFFs de gravedad no encontrados en fuentes/")

    try:
        import rasterio
        from rasterio.sample import sample_gen
    except ImportError:
        raise HTTPException(503, "rasterio no disponible")

    pts = _interpolate_line(req.coords, min(req.n_points, 200))

    # Distancias acumuladas en km
    dists = [0.0]
    for i in range(1, len(pts)):
        dists.append(dists[-1] + _haversine_km(pts[i-1], pts[i]))

    xy = [(p[0], p[1]) for p in pts]

    def sample_tif(path):
        with rasterio.open(path) as src:
            vals = [v[0] for v in src.sample(xy)]
        nodata = None
        try:
            with rasterio.open(path) as src:
                nodata = src.nodata
        except Exception:
            pass
        # Reemplazar nodata con None
        return [None if (nodata is not None and v == nodata) else round(float(v), 2) for v in vals]

    bouguer  = sample_tif(BOUGUER_TIF)
    freeair  = sample_tif(FREEAIR_TIF)

    return {
        "dist_km":   [round(d, 3) for d in dists],
        "bouguer":   bouguer,
        "freeair":   freeair,
        "lon":       [round(p[0], 4) for p in pts],
        "lat":       [round(p[1], 4) for p in pts],
        "n":         len(pts),
        "total_km":  round(dists[-1], 2),
    }
