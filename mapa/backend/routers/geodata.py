from fastapi import APIRouter, Query, HTTPException, Body
from ..database import get_conn
from pathlib import Path
import json, math, shutil
from datetime import datetime
from typing import Any

MAPA_ROOT = Path(__file__).parent.parent.parent  # mapa/

router = APIRouter()

GEOREF_FILE = Path(__file__).parent.parent.parent / "data" / "georef_extents.json"


@router.post("/georef/save")
def save_georef_extents(body: dict = Body(...)):
    """Persiste los extents calibrados desde el frontend al archivo georef_extents.json."""
    try:
        GEOREF_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if GEOREF_FILE.exists():
            existing = json.loads(GEOREF_FILE.read_text(encoding="utf-8"))
        existing.update(body)
        GEOREF_FILE.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"status": "saved", "keys": list(body.keys()), "file": str(GEOREF_FILE)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── /api/geodata/features ──────────────────────────────────────────────────

@router.get("/geodata/features")
def list_features(
    source:     str | None = Query(None),
    layer_type: str | None = Query(None, alias="layerType"),
    unmatched:  bool       = Query(False, description="Solo features sin canonical_id"),
):
    conn  = get_conn()
    where = []
    args  = []
    if source:
        where.append("source=?"); args.append(source)
    if layer_type:
        where.append("layer_type=?"); args.append(layer_type)
    if unmatched:
        where.append("canonical_id IS NULL")

    sql = "SELECT * FROM geo_features"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY layer_type, source, id"

    rows = conn.execute(sql, args).fetchall()
    conn.close()

    features = [
        {
            "type": "Feature",
            "geometry": json.loads(r["geometry"]),
            "properties": {
                "id":           r["id"],
                "canonical_id": r["canonical_id"],
                "source":       r["source"],
                "layer_type":   r["layer_type"],
                "name":         r["name"],
                "confidence":   r["confidence"],
                "year":         r["year"],
                **(json.loads(r["properties"]) if r["properties"] else {}),
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}


# ── /api/geodata/canonical/{id}/features (fe_15) ─────────────────────────

@router.get("/geodata/canonical/{canonical_id}/features")
def get_canonical_features(canonical_id: str):
    """Features asignados a un canonical — para previsualizar en el draw tool."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM geo_features WHERE canonical_id=? ORDER BY source, id",
        (canonical_id,)
    ).fetchall()
    conn.close()
    features = [
        {
            "type": "Feature",
            "geometry": json.loads(r["geometry"]),
            "properties": {
                "id":         r["id"],
                "source":     r["source"],
                "layer_type": r["layer_type"],
                "name":       r["name"],
                **(json.loads(r["properties"]) if r["properties"] else {}),
            },
        }
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features, "count": len(features)}


# ── /api/geodata/canonical ─────────────────────────────────────────────────

@router.get("/geodata/canonical")
def list_canonical(
    layer_type: str | None = Query(None, alias="layerType"),
):
    conn  = get_conn()
    where = []
    args  = []
    if layer_type:
        where.append("layer_type=?"); args.append(layer_type)

    sql = "SELECT * FROM canonical_structures"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY layer_type, id"

    rows = conn.execute(sql, args).fetchall()
    conn.close()

    features = []
    for r in rows:
        def _j(s, default):
            try: return json.loads(s) if s else default
            except Exception: return default
        geom = _j(r["merged_geom"], None)
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "id":           r["id"],
                "layer_type":   r["layer_type"],
                "name":         r["name"],
                "source_count": r["source_count"],
                "sources":      _j(r["sources"], []),
                "updated_at":   r["updated_at"],
                **_j(r["properties"], {}),
            },
        })
    return {"type": "FeatureCollection", "features": features, "count": len(features)}


# ── /api/geodata/features/{id}/canonical ─────────────────────────────────

@router.patch("/geodata/features/{feature_id}/canonical")
def set_feature_canonical(feature_id: int, body: dict = Body(...)):
    """Reasigna o desasigna el canonical_id de un feature."""
    canonical_id = body.get("canonical_id")  # None = desasignar
    conn = get_conn()
    if not conn.execute("SELECT id FROM geo_features WHERE id=?", (feature_id,)).fetchone():
        conn.close(); raise HTTPException(404, "Feature not found")
    conn.execute("UPDATE geo_features SET canonical_id=? WHERE id=?", (canonical_id, feature_id))
    conn.commit(); conn.close()
    return {"status": "updated", "feature_id": feature_id, "canonical_id": canonical_id}


@router.delete("/geodata/canonical/{canonical_id}")
def delete_canonical(canonical_id: str):
    """Borra un canonical y desasigna todos sus features."""
    conn = get_conn()
    conn.execute("UPDATE geo_features SET canonical_id=NULL WHERE canonical_id=?", (canonical_id,))
    conn.execute("DELETE FROM canonical_structures WHERE id=?", (canonical_id,))
    conn.commit(); conn.close()
    return {"status": "deleted", "canonical_id": canonical_id}


# ── /api/geodata/canonical/pending (fe_15) ────────────────────────────────

@router.get("/geodata/canonical/pending")
def list_canonical_pending(all: int = Query(0)):
    """Canonicals para la herramienta de dibujo. all=1 incluye los que ya tienen merged_geom."""
    conn = get_conn()
    where = "" if all else "WHERE cs.merged_geom IS NULL"
    rows = conn.execute(f"""
        SELECT cs.id, cs.name, cs.layer_type,
               COUNT(gf.id) AS feature_count,
               CASE WHEN cs.merged_geom IS NOT NULL THEN 1 ELSE 0 END AS has_geom
        FROM canonical_structures cs
        LEFT JOIN geo_features gf ON gf.canonical_id = cs.id
        {where}
        GROUP BY cs.id
        ORDER BY cs.layer_type, cs.name
    """).fetchall()
    conn.close()
    return {"canonicals": [dict(r) for r in rows]}


@router.patch("/geodata/canonical/{canonical_id}/merged_geom")
def set_canonical_merged_geom(canonical_id: str, body: dict = Body(...)):
    """Guarda una geometría dibujada manualmente como merged_geom."""
    geom      = body.get("geometry")
    name      = body.get("name", canonical_id)
    layer_type = body.get("layer_type", "fault")
    if not geom:
        raise HTTPException(400, "geometry required")
    conn = get_conn()
    existing = conn.execute(
        "SELECT id FROM canonical_structures WHERE id=?", (canonical_id,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE canonical_structures SET merged_geom=?, updated_at=datetime('now') WHERE id=?",
            (json.dumps(geom), canonical_id)
        )
    else:
        conn.execute(
            "INSERT INTO canonical_structures (id, layer_type, name, merged_geom, source_count, sources) "
            "VALUES (?,?,?,?,0,'[]')",
            (canonical_id, layer_type, name, json.dumps(geom))
        )
    conn.commit()
    conn.close()
    return {"status": "saved", "canonical_id": canonical_id}


# ── /api/geodata/matches ───────────────────────────────────────────────────

@router.get("/geodata/matches")
def list_matches(
    status: str = Query("pending", description="pending | approved | rejected | split_needed"),
):
    conn = get_conn()
    rows = conn.execute(
        "SELECT mp.*, "
        "  fa.source AS src_a, fa.layer_type AS lt_a, fa.name AS name_a, fa.geometry AS geom_a, "
        "  fb.source AS src_b, fb.layer_type AS lt_b, fb.name AS name_b, fb.geometry AS geom_b "
        "FROM match_proposals mp "
        "JOIN geo_features fa ON mp.feature_a_id = fa.id "
        "JOIN geo_features fb ON mp.feature_b_id = fb.id "
        "WHERE mp.status=? "
        "ORDER BY mp.similarity DESC",
        (status,)
    ).fetchall()
    conn.close()

    return {
        "matches": [
            {
                "id":           r["id"],
                "feature_a": {"id": r["feature_a_id"], "source": r["src_a"],
                               "name": r["name_a"], "layer_type": r["lt_a"],
                               "geometry": json.loads(r["geom_a"])},
                "feature_b": {"id": r["feature_b_id"], "source": r["src_b"],
                               "name": r["name_b"], "layer_type": r["lt_b"],
                               "geometry": json.loads(r["geom_b"])},
                "similarity":   r["similarity"],
                "status":       r["status"],
                "canonical_id": r["canonical_id"],
                "notes":        r["notes"],
                "created_at":   r["created_at"],
            }
            for r in rows
        ],
        "count": len(rows),
    }


# ── /api/geodata/matches/{id}/approve ─────────────────────────────────────

@router.post("/geodata/matches/{match_id}/approve")
def approve_match(match_id: int):
    """Marca el par como 'misma estructura'. Unifica canonical_id si alguno ya tiene uno."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM match_proposals WHERE id=?", (match_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Match not found")

    fa = conn.execute("SELECT * FROM geo_features WHERE id=?", (row["feature_a_id"],)).fetchone()
    fb = conn.execute("SELECT * FROM geo_features WHERE id=?", (row["feature_b_id"],)).fetchone()

    ca, cb = fa["canonical_id"], fb["canonical_id"]

    if ca and cb and ca != cb:
        # Unificar: todos los features con cb pasan a usar ca
        conn.execute("UPDATE geo_features    SET canonical_id=? WHERE canonical_id=?", (ca, cb))
        conn.execute("UPDATE match_proposals SET canonical_id=? WHERE canonical_id=?", (ca, cb))
        cid = ca
    elif ca:
        cid = ca
    elif cb:
        cid = cb
    else:
        cid = f"canon_{match_id}"

    conn.execute("UPDATE match_proposals SET status='approved', canonical_id=? WHERE id=?",
                 (cid, match_id))
    conn.execute("UPDATE geo_features SET canonical_id=? WHERE id IN (?,?)",
                 (cid, row["feature_a_id"], row["feature_b_id"]))
    conn.commit()
    conn.close()
    return {"status": "approved", "canonical_id": cid}


# ── /api/geodata/matches/{id}/reject ──────────────────────────────────────

@router.post("/geodata/matches/{match_id}/reject")
def reject_match(match_id: int, notes: str | None = Query(None)):
    conn = get_conn()
    n = conn.execute("UPDATE match_proposals SET status='rejected', notes=? WHERE id=?",
                     (notes, match_id)).rowcount
    conn.commit()
    conn.close()
    if not n:
        raise HTTPException(404, "Match not found")
    return {"status": "rejected"}


# ── /api/geodata/matches/{id}/split ───────────────────────────────────────

@router.post("/geodata/matches/{match_id}/split")
def split_match(match_id: int, notes: str | None = Query(None)):
    """Marca el match como 'split_needed': una fuente agrupa lo que la otra divide en segmentos."""
    conn = get_conn()
    n = conn.execute(
        "UPDATE match_proposals SET status='split_needed', notes=? WHERE id=?",
        (notes, match_id)
    ).rowcount
    conn.commit()
    conn.close()
    if not n:
        raise HTTPException(404, "Match not found")
    return {"status": "split_needed"}


# ── /api/geodata/canonical-groups ─────────────────────────────────────────

@router.get("/geodata/canonical-groups")
def get_canonical_groups():
    """Devuelve grupos de features con el mismo canonical_id para selección de geometría."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT canonical_id, id, source, layer_type, name, geometry "
        "FROM geo_features WHERE canonical_id IS NOT NULL "
        "ORDER BY canonical_id, source"
    ).fetchall()

    groups: dict[str, dict] = {}
    for r in rows:
        cid = r["canonical_id"]
        if cid not in groups:
            groups[cid] = {"canonical_id": cid, "layer_type": r["layer_type"], "features": []}
        groups[cid]["features"].append({
            "id":       r["id"],
            "source":   r["source"],
            "name":     r["name"] or "",
            "geometry": json.loads(r["geometry"]),
        })

    # Estado de resolución
    resolved_ids = {r["id"] for r in
                    conn.execute("SELECT id FROM canonical_structures WHERE merged_geom IS NOT NULL").fetchall()}
    conn.close()

    result = []
    for cid, g in groups.items():
        if len(g["features"]) < 2:
            continue
        g["resolved"] = cid in resolved_ids
        g["name"] = next((f["name"] for f in g["features"] if f["name"]), cid)
        result.append(g)

    result.sort(key=lambda g: (g["resolved"], g["layer_type"], g["canonical_id"]))
    return {"groups": result, "count": len(result)}


@router.post("/geodata/canonical-groups/{canonical_id}/resolve")
def resolve_canonical_geometry(
    canonical_id:       str,
    chosen_feature_id:  int = Query(..., alias="chosenId"),
):
    """Fija la geometría del feature elegido como canónica del grupo."""
    conn = get_conn()
    chosen = conn.execute("SELECT * FROM geo_features WHERE id=?", (chosen_feature_id,)).fetchone()
    if not chosen:
        conn.close()
        raise HTTPException(404, "Feature not found")

    all_feats = conn.execute(
        "SELECT * FROM geo_features WHERE canonical_id=?", (canonical_id,)
    ).fetchall()

    chosen_geom = json.loads(chosen["geometry"])
    all_geoms   = [json.loads(f["geometry"]) for f in all_feats]
    uncert      = _uncertainty_hull(all_geoms)
    sources     = sorted({f["source"] for f in all_feats})

    existing = conn.execute(
        "SELECT id FROM canonical_structures WHERE id=?", (canonical_id,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE canonical_structures SET merged_geom=?, uncert_geom=?, name=?, "
            "source_count=?, sources=?, updated_at=datetime('now') WHERE id=?",
            (json.dumps(chosen_geom), json.dumps(uncert) if uncert else None,
             chosen["name"], len(sources), json.dumps(sources), canonical_id)
        )
    else:
        conn.execute(
            "INSERT INTO canonical_structures "
            "(id, layer_type, name, merged_geom, uncert_geom, source_count, sources) "
            "VALUES (?,?,?,?,?,?,?)",
            (canonical_id, chosen["layer_type"], chosen["name"],
             json.dumps(chosen_geom), json.dumps(uncert) if uncert else None,
             len(sources), json.dumps(sources))
        )

    conn.commit()
    conn.close()
    return {"status": "resolved", "canonical_id": canonical_id}


# ── /api/geodata/clusters ─────────────────────────────────────────────────

@router.get("/geodata/clusters")
def get_clusters(min_sim: float = Query(0.50, alias="minSim")):
    """Agrupa features en clusters via union-find sobre proposals pendientes con sim >= minSim."""
    conn = get_conn()
    proposals = conn.execute(
        "SELECT id, feature_a_id, feature_b_id, similarity "
        "FROM match_proposals WHERE status='pending' AND similarity>=? "
        "ORDER BY similarity DESC",
        (min_sim,)
    ).fetchall()

    if not proposals:
        conn.close()
        return {"clusters": [], "count": 0, "pending_low_sim": 0}

    # Union-find
    parent: dict[int, int] = {}
    def find(x):
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    def union(x, y):
        parent[find(x)] = find(y)

    prop_by_pair: dict[tuple, list] = {}
    for p in proposals:
        union(p["feature_a_id"], p["feature_b_id"])
        key = (min(p["feature_a_id"], p["feature_b_id"]),
               max(p["feature_a_id"], p["feature_b_id"]))
        prop_by_pair.setdefault(key, []).append(p["id"])

    # Build clusters
    cluster_map: dict[int, set] = {}
    cluster_proposals: dict[int, list] = {}
    for p in proposals:
        for fid in (p["feature_a_id"], p["feature_b_id"]):
            root = find(fid)
            cluster_map.setdefault(root, set()).add(fid)

    # Collect all proposal IDs per cluster
    for p in proposals:
        root = find(p["feature_a_id"])
        cluster_proposals.setdefault(root, []).append(p["id"])

    # Load feature details
    all_fids = set()
    for fids in cluster_map.values():
        all_fids.update(fids)
    feat_rows = conn.execute(
        "SELECT id, source, layer_type, name, geometry FROM geo_features WHERE id IN ({})".format(
            ",".join("?" * len(all_fids))
        ),
        list(all_fids)
    ).fetchall()
    feat_by_id = {r["id"]: r for r in feat_rows}

    # Count low-similarity pending proposals not in any cluster
    pending_low = conn.execute(
        "SELECT COUNT(*) FROM match_proposals WHERE status='pending' AND similarity<?",
        (min_sim,)
    ).fetchone()[0]
    conn.close()

    clusters = []
    for root, fids in cluster_map.items():
        feats = []
        for i, fid in enumerate(sorted(fids)):
            r = feat_by_id.get(fid)
            if not r:
                continue
            feats.append({
                "id":         fid,
                "source":     r["source"],
                "layer_type": r["layer_type"],
                "name":       r["name"],
                "geometry":   json.loads(r["geometry"]),
                "color_idx":  i,
            })
        if len(feats) < 2:
            continue
        prop_ids = cluster_proposals.get(root, [])
        sims = [p["similarity"] for p in proposals if p["id"] in prop_ids]
        clusters.append({
            "id":           root,
            "layer_type":   feats[0]["layer_type"],
            "feature_count": len(feats),
            "min_sim":      round(min(sims), 3) if sims else 0,
            "max_sim":      round(max(sims), 3) if sims else 0,
            "features":     feats,
            "proposal_ids": prop_ids,
        })

    clusters.sort(key=lambda c: -c["max_sim"])
    return {"clusters": clusters, "count": len(clusters), "pending_low_sim": pending_low}


# ── /api/geodata/clusters/resolve ─────────────────────────────────────────

@router.post("/geodata/clusters/resolve")
def resolve_cluster(
    chosen_id:    int | None  = Query(None, alias="chosenId", description="feature_id elegido como canónico (None si split)"),
    feature_ids:  str         = Query(...,  alias="featureIds", description="IDs separados por coma"),
    proposal_ids: str         = Query(...,  alias="proposalIds", description="IDs de proposals separados por coma"),
    action:       str         = Query("approve", description="approve | split | reject"),
):
    fids = [int(x) for x in feature_ids.split(",") if x.strip()]
    pids = [int(x) for x in proposal_ids.split(",") if x.strip()]
    conn = get_conn()

    if action == "approve" and chosen_id:
        cid = f"canon_c{chosen_id}"
        # Geometry from chosen feature
        chosen = conn.execute("SELECT * FROM geo_features WHERE id=?", (chosen_id,)).fetchone()
        if not chosen:
            conn.close()
            raise HTTPException(404, "Chosen feature not found")
        chosen_geom = json.loads(chosen["geometry"])

        # Build uncertainty hull from all features
        all_geoms = []
        for fid in fids:
            r = conn.execute("SELECT geometry FROM geo_features WHERE id=?", (fid,)).fetchone()
            if r:
                all_geoms.append(json.loads(r["geometry"]))
        uncert = _uncertainty_hull(all_geoms)

        sources = []
        for fid in fids:
            r = conn.execute("SELECT source FROM geo_features WHERE id=?", (fid,)).fetchone()
            if r and r["source"] not in sources:
                sources.append(r["source"])

        # Upsert canonical_structure
        existing = conn.execute("SELECT * FROM canonical_structures WHERE id=?", (cid,)).fetchone()
        if existing:
            existing_sources = set(json.loads(existing["sources"] or "[]"))
            existing_sources.update(sources)
            conn.execute(
                "UPDATE canonical_structures SET source_count=?, sources=?, merged_geom=?, "
                "uncert_geom=?, updated_at=datetime('now') WHERE id=?",
                (len(existing_sources), json.dumps(sorted(existing_sources)),
                 json.dumps(chosen_geom), json.dumps(uncert) if uncert else None, cid)
            )
        else:
            conn.execute(
                "INSERT INTO canonical_structures (id, layer_type, name, merged_geom, uncert_geom, "
                "source_count, sources) VALUES (?,?,?,?,?,?,?)",
                (cid, chosen["layer_type"], chosen["name"],
                 json.dumps(chosen_geom), json.dumps(uncert) if uncert else None,
                 len(sources), json.dumps(sources))
            )

        # Update features and proposals
        for fid in fids:
            conn.execute("UPDATE geo_features SET canonical_id=? WHERE id=?", (cid, fid))
        for pid in pids:
            conn.execute("UPDATE match_proposals SET status='approved', canonical_id=? WHERE id=?",
                         (cid, pid))
        conn.commit()
        conn.close()
        return {"status": "approved", "canonical_id": cid}

    elif action in ("split", "reject"):
        status = "split_needed" if action == "split" else "rejected"
        for pid in pids:
            conn.execute("UPDATE match_proposals SET status=? WHERE id=?", (status, pid))
        conn.commit()
        conn.close()
        return {"status": status}

    conn.close()
    raise HTTPException(400, "Acción inválida o falta chosenId")


# ── /api/geodata/matches/run ───────────────────────────────────────────────

@router.post("/geodata/matches/run")
def run_matching(threshold: float = Query(0.20)):
    """Lanza el algoritmo de matching en el proceso actual (síncrono, puede tardar)."""
    from ..scripts.match_geodata import run as _run
    _run(threshold=threshold)
    conn  = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM match_proposals").fetchone()[0]
    conn.close()
    return {"generated": total, "threshold": threshold}


# ── PATCH /api/geodata/features/{id} — actualiza geometría ────────────────

@router.patch("/geodata/features/{feature_id}")
def update_feature_geometry(
    feature_id: int,
    body: dict[str, Any] = Body(...),
):
    """Actualiza la geometría de un feature en geo_features. Acepta GeoJSON geometry."""
    geom = body.get("geometry")
    if not geom or "type" not in geom or "coordinates" not in geom:
        raise HTTPException(400, "Se requiere 'geometry' GeoJSON válido")

    allowed_types = {"Point", "LineString", "Polygon", "MultiLineString", "MultiPolygon"}
    if geom["type"] not in allowed_types:
        raise HTTPException(400, f"Tipo de geometría no soportado: {geom['type']}")

    conn = get_conn()
    row = conn.execute("SELECT id, name FROM geo_features WHERE id=?", (feature_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, f"Feature {feature_id} no encontrado")

    conn.execute(
        "UPDATE geo_features SET geometry=? WHERE id=?",
        (json.dumps(geom, ensure_ascii=False), feature_id)
    )
    conn.commit()
    conn.close()
    return {"updated": feature_id, "name": row["name"], "geometry_type": geom["type"]}


# ── Helpers geométricos ────────────────────────────────────────────────────

def _resample(coords, n=50):
    if len(coords) < 2:
        return coords
    segs, total = [], 0.0
    for i in range(len(coords)-1):
        dx = coords[i+1][0]-coords[i][0]
        dy = coords[i+1][1]-coords[i][1]
        lat_avg = math.radians((coords[i][1]+coords[i+1][1])/2)
        d = math.sqrt((dx*math.cos(lat_avg))**2 + dy**2)
        segs.append(d); total += d
    if total == 0:
        return [coords[0]]*n
    step  = total / (n-1)
    res   = [coords[0]]
    acc   = 0.0; si = 0; sacc = 0.0
    for _ in range(n-2):
        target = len(res) * step
        while si < len(segs):
            if sacc + segs[si] >= target - acc + 1e-12:
                t = (target - acc - sacc) / segs[si]
                p1, p2 = coords[si], coords[si+1]
                res.append([p1[0]+t*(p2[0]-p1[0]), p1[1]+t*(p2[1]-p1[1])])
                break
            sacc += segs[si]; acc += segs[si]; si += 1
    res.append(coords[-1])
    return res


def _merge_geometries(g1: dict, g2: dict) -> dict:
    t1, t2 = g1.get("type"), g2.get("type")
    if t1 in ("LineString",) and t2 in ("LineString",):
        c1 = _resample(g1["coordinates"], 50)
        c2 = _resample(g2["coordinates"], 50)
        avg = [[(c1[i][0]+c2[i][0])/2, (c1[i][1]+c2[i][1])/2] for i in range(50)]
        return {"type": "LineString", "coordinates": avg}
    if t1 == "Point" and t2 == "Point":
        lon = (g1["coordinates"][0] + g2["coordinates"][0]) / 2
        lat = (g1["coordinates"][1] + g2["coordinates"][1]) / 2
        return {"type": "Point", "coordinates": [lon, lat]}
    return g1  # fallback


def _uncertainty_hull(geometries: list[dict]) -> dict | None:
    """Convex hull simplificado de todos los vértices."""
    pts = []
    for g in geometries:
        t = g.get("type")
        if t == "LineString":
            pts.extend(g["coordinates"])
        elif t == "Point":
            pts.append(g["coordinates"])
    if len(pts) < 3:
        return None
    hull = _convex_hull(pts)
    if len(hull) < 3:
        return None
    ring = hull + [hull[0]]
    return {"type": "Polygon", "coordinates": [ring]}


def _cross(o, a, b):
    return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])


def _convex_hull(pts):
    pts = sorted(set(map(tuple, pts)))
    if len(pts) <= 1:
        return [list(p) for p in pts]
    lower = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return [list(p) for p in hull]


# ── /api/crop-image ────────────────────────────────────────────────────────
@router.post("/crop-image")
def crop_image(body: dict = Body(...)):
    """
    Recorta una imagen y la reemplaza en disco.
    Body: { path: str (relativo a mapa/), x, y, w, h: int, backup: bool=true }
    """
    try:
        from PIL import Image as PILImage
    except ImportError:
        raise HTTPException(500, "Pillow no instalado — pip install pillow")

    rel_path = body.get("path", "")
    x, y, w, h = int(body["x"]), int(body["y"]), int(body["w"]), int(body["h"])
    do_backup = body.get("backup", True)

    if not rel_path:
        raise HTTPException(400, "path requerido")

    img_path = MAPA_ROOT / rel_path
    if not img_path.exists():
        raise HTTPException(404, f"Imagen no encontrada: {rel_path}")

    # Backup automático antes de sobreescribir
    if do_backup:
        bak = img_path.with_suffix(".bak" + img_path.suffix)
        if not bak.exists():
            shutil.copy2(img_path, bak)

    img = PILImage.open(img_path)
    iw, ih = img.size
    # Clamp al tamaño real
    x  = max(0, min(x, iw))
    y  = max(0, min(y, ih))
    x2 = max(0, min(x + w, iw))
    y2 = max(0, min(y + h, ih))

    if x2 <= x or y2 <= y:
        raise HTTPException(400, "Recorte vacío")

    cropped = img.crop((x, y, x2, y2))
    cropped.save(img_path)

    return {"status": "ok", "path": rel_path,
            "original_size": [iw, ih],
            "crop": [x, y, x2 - x, y2 - y],
            "backup": str(bak.name) if do_backup else None}
