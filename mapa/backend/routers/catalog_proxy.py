from fastapi import APIRouter, Query, HTTPException
from datetime import datetime, timedelta, timezone
import asyncio, httpx, time

router = APIRouter()

FDSN_URL  = "https://earthquake.usgs.gov/fdsnws/event/1/query"
ISC_URL   = "https://www.isc.ac.uk/fdsnws/event/1/query"
BBOX      = dict(minlatitude=-12, maxlatitude=7, minlongitude=114, maxlongitude=132)
TIMEOUT   = 45.0

# Cache ISC en memoria — TTL 6 horas
_ISC_CACHE: dict = {}
_ISC_TTL = 6 * 3600  # segundos


def _fault_type(rake):
    if rake is None:
        return "O"
    r = float(rake)
    if r > 180:  r -= 360
    if r < -180: r += 360
    if  45 <= r <= 135:  return "T"
    if -135 <= r <= -45: return "N"
    if (-30 <= r <= 30) or r >= 150 or r <= -150: return "S"
    return "O"


async def _fetch_mt(client: httpx.AsyncClient, detail_url: str) -> dict | None:
    """Extract nodal planes from a USGS ComCat event detail URL."""
    try:
        resp = await client.get(detail_url, timeout=10.0)
        resp.raise_for_status()
        detail = resp.json()
        products = ((detail.get("properties") or {}).get("products")) or {}
        for key in ("moment-tensor", "focal-mechanism"):
            lst = products.get(key) or []
            if not lst:
                continue
            props = lst[0].get("properties") or {}
            try:
                s1 = float(props["nodal-plane-1-strike"])
                d1 = float(props["nodal-plane-1-dip"])
                r1 = float(props["nodal-plane-1-rake"])
                s2 = float(props["nodal-plane-2-strike"])
                d2 = float(props["nodal-plane-2-dip"])
                r2 = float(props["nodal-plane-2-rake"])
                return dict(s1=round(s1), d1=round(d1), r1=round(r1),
                            s2=round(s2), d2=round(d2), r2=round(r2))
            except (KeyError, ValueError, TypeError):
                continue
    except Exception:
        pass
    return None


@router.get("/catalog/live")
async def get_live_catalog(
    min_mag: float = Query(5.0, alias="minMag", ge=3.0, le=9.9),
    days:    int   = Query(30,  alias="days",   ge=1,   le=365),
):
    end_dt   = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)

    params = {
        "format":       "geojson",
        "minmagnitude": min_mag,
        "starttime":    start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime":      end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "orderby":      "time-asc",
        **BBOX,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(FDSN_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException:
            raise HTTPException(504, "Timeout consultando USGS FDSN")
        except httpx.HTTPStatusError as e:
            raise HTTPException(502, f"USGS FDSN devolvió {e.response.status_code}")

        feats = data.get("features", [])

        # Collect events that have a moment-tensor or focal-mechanism product
        mt_needed: dict[str, str] = {}   # event_id → detail_url
        for feat in feats:
            p = feat["properties"]
            types_str = (p.get("types") or "")
            if "moment-tensor" in types_str or "focal-mechanism" in types_str:
                detail_url = p.get("detail", "")
                if detail_url:
                    mt_needed[feat["id"]] = detail_url

        # Batch-fetch moment tensors in parallel (cap at 50 to avoid hammering USGS)
        mt_results: dict[str, dict] = {}
        if mt_needed:
            ids  = list(mt_needed.keys())[:50]
            urls = [mt_needed[i] for i in ids]
            raw  = await asyncio.gather(*[_fetch_mt(client, u) for u in urls])
            for eid, mt in zip(ids, raw):
                if mt:
                    mt_results[eid] = mt

    features = []
    for feat in feats:
        p      = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        mag    = p.get("mag") or 0
        ts     = p.get("time")
        yr     = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).year if ts else 0
        iso    = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat() if ts else None

        mt = mt_results.get(feat["id"])
        s1, d1, r1 = (mt["s1"], mt["d1"], mt["r1"]) if mt else (None, None, None)
        s2, d2, r2 = (mt["s2"], mt["d2"], mt["r2"]) if mt else (None, None, None)
        ft = _fault_type(r1) if mt else "O"

        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [coords[0], coords[1]]},
            "properties": {
                "lo":    round(coords[0], 3),
                "la":    round(coords[1], 3),
                "de":    round(coords[2], 1),
                "mw":    round(mag, 1),
                "yr":    yr,
                "ft":    ft,
                "s1": s1, "d1": d1, "r1": r1,
                "s2": s2, "d2": d2, "r2": r2,
                "label": p.get("place", ""),
                "time":  iso,
                "url":   p.get("url", ""),
                "live":  True,
            },
        })

    return {
        "type":     "FeatureCollection",
        "features": features,
        "count":    len(features),
        "with_mt":  len(mt_results),
        "days":     days,
        "minMag":   min_mag,
        "updated":  end_dt.isoformat(),
    }



@router.get("/catalog/isc")
async def get_isc_catalog(
    min_mag:   float = Query(4.5,  alias="minMag",   ge=3.0, le=9.9),
    max_mag:   float = Query(5.4,  alias="maxMag",   ge=3.0, le=9.9),
    days:      int   = Query(365,  alias="days",      ge=1,   le=3650),
    min_depth: float = Query(0,    alias="minDepth",  ge=0),
    max_depth: float = Query(700,  alias="maxDepth",  le=750),
):
    """Catálogo ISC FDSN — cubre el gap Mw 4.5-5.4 entre GCMT y USGS. Cacheado 6h."""
    cache_key = f"{min_mag}_{max_mag}_{days}_{min_depth}_{max_depth}"
    cached = _ISC_CACHE.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _ISC_TTL:
        return cached["data"]

    end_dt   = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=days)

    params = {
        "format":    "text",
        "minmag":    min_mag,
        "maxmag":    max_mag,
        "starttime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime":   end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "mindepth":  min_depth,
        "maxdepth":  max_depth,
        **BBOX,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(ISC_URL, params=params)
            resp.raise_for_status()
            text = resp.text
    except httpx.TimeoutException:
        raise HTTPException(504, "Timeout consultando ISC FDSN")
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"ISC FDSN devolvió {e.response.status_code}")
    except Exception as e:
        raise HTTPException(502, f"Error ISC: {e}")

    # Formato text: #EventID|Time|Latitude|Longitude|Depth/km|Author|...|Magnitude|...
    features = []
    for line in text.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cols = line.split("|")
        if len(cols) < 11:
            continue
        try:
            lat     = float(cols[2])
            lon     = float(cols[3])
            depth   = float(cols[4]) if cols[4] else 0.0
            mag     = float(cols[10]) if cols[10] else 0.0
            ev_time = cols[1]
        except ValueError:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [round(lon, 3), round(lat, 3)]},
            "properties": {
                "lo": round(lon, 3),
                "la": round(lat, 3),
                "de": round(depth, 1),
                "mw": round(mag, 1),
                "time": ev_time,
                "catalog": "ISC",
            },
        })

    result = {
        "type":     "FeatureCollection",
        "features": features,
        "count":    len(features),
        "days":     days,
        "minMag":   min_mag,
        "maxMag":   max_mag,
        "updated":  end_dt.isoformat(),
    }
    _ISC_CACHE[cache_key] = {"data": result, "ts": time.time()}
    return result
