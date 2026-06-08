"""
Genera match_proposals comparando trazas estructurales lineales.

Tres fases (en orden):
  1. Canon vs Canon   — detecta canónicos duplicados que deberían fusionarse
  2. Huérfano vs Canon — asigna cada feature sin canonical_id al canónico más cercano
  3. Huérfano vs Huérfano — entre los que no matchearon nada, busca nuevos grupos

Cross-type matching habilitado: fault ↔ subduction_zone ↔ fold_thrust_belt ↔
deformation_zone ↔ structure (distintas fuentes etiquetan la misma traza distinto).
hazard_zone solo se compara consigo misma.

Seismic gaps (category=geophysical_point, geometry=Point) quedan excluidos
naturalmente porque line_similarity() devuelve None para geometrías no-LineString.

Nunca toca proposals con status != 'pending'.

Ejecutar:
    cd c:\\Users\\PC\\Desktop\\Geo\\Tectonica\\Monografia\\mapa
    python -m backend.scripts.match_geodata [--threshold 0.65]
"""
import json, math, sqlite3, argparse
from itertools import combinations
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "sulawesi.db"

# Tipos estructurales que se comparan entre sí (cross-type permitido)
STRUCTURAL_TYPES = {"fault", "subduction_zone", "structure", "fold_thrust_belt",
                    "deformation_zone"}
# Tipos que solo se comparan consigo mismos
ISOLATED_TYPES = {"hazard_zone"}
LINE_TYPES = STRUCTURAL_TYPES | ISOLATED_TYPES


def can_cross_match(lt_a: str, lt_b: str) -> bool:
    """True si los dos layer_types son comparables entre sí."""
    if lt_a == lt_b:
        return True
    return lt_a in STRUCTURAL_TYPES and lt_b in STRUCTURAL_TYPES


# ── Similitud de nombre ──────────────────────────────────────────────────────

import re

# Palabras genéricas de tipo estructural o dirección — no son identificadores geográficos
_STRUCTURAL = {
    # Inglés — tipos
    'fault','zone','thrust','trench','subduction','boundary','convergent',
    'divergent','transform','fold','belt','deformation','slab','arc','system',
    'complex','region','area','basin','reverse','normal','strike','slip',
    'lateral','dextral','sinistral','left','right','megathrust','back','fore',
    'collision','accretionary','wedge','prism','vergent','rift','shear',
    # Inglés — direcciones/calificadores
    'north','south','east','west','central','upper','lower','northern',
    'southern','eastern','western','inner','outer','main','major','minor',
    'active','new','old','deep','shallow','frontal','offshore','onshore',
    # Español — tipos
    'falla','zona','empuje','trinchera','subduccion','limite','deformacion',
    'cinturon','pliegue','sistema','complejo','cuenca','arco',
    # Español — direcciones
    'norte','sur','este','oeste',
    # Indonesio — tipos
    'sesar','patahan','lempeng',
    # Stopwords
    'the','and','of','a','an','de','la','el','y','en','del','los','las',
    'un','una','se','con','por','para','que','al','lo',
    # Abreviaturas de fuente/dataset (no geográficas)
    'gem','gps','gcmt','iugs',
}

_ABBREV = {
    'nst': 'north sulawesi trench',
    'mst': 'makassar strait thrust',
    'pkf': 'palu koro fault',
    'tfz': 'tamponas fault zone',
    'wwf': 'west walane fault',
    'csfs': 'central sulawesi fault system',
}


def _geo_tokens(name: str) -> set:
    """Tokens geográficos (no genéricos) de un nombre de estructura."""
    if not name:
        return set()
    s = re.sub(r'[�\x00-\x1f\?\*]', ' ', name.lower())
    # Expandir abreviaturas conocidas
    for abbr, full in _ABBREV.items():
        s = re.sub(r'\b' + abbr + r'\b', full, s)
    tokens = re.findall(r'\b[a-z]{3,}\b', s)
    return {t for t in tokens if t not in _STRUCTURAL}


def name_factor(name_a: str, name_b: str) -> float:
    """
    Multiplicador basado en similitud de nombre para la similitud combinada.
    - Ambos tienen tokens geográficos que coinciden: boost ×(0.7 + 0.3·jaccard)
    - Ambos tienen tokens geográficos distintos: penaliza fuertemente ×0.25
    - Al menos uno es genérico (sin identificador geográfico): neutral ×0.8
    """
    ga = _geo_tokens(name_a)
    gb = _geo_tokens(name_b)

    if not ga or not gb:
        return 0.8  # nombre genérico en alguno → neutral moderado

    intersection = ga & gb
    if not intersection:
        return 0.25  # nombres específicos claramente distintos

    jaccard = len(intersection) / len(ga | gb)
    return 0.7 + 0.3 * jaccard  # rango 0.7–1.0


def combined_sim(geom_sim: float, name_a: str, name_b: str) -> float:
    return geom_sim * name_factor(name_a, name_b)


# ── Geometría ───────────────────────────────────────────────────────────────

def haversine(lon1, lat1, lon2, lat2) -> float:
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    return math.sqrt(dlat**2 + (dlon * math.cos(math.radians((lat1 + lat2) / 2)))**2)


def resample_line(coords: list, n: int = 40) -> list:
    if len(coords) < 2:
        return coords
    segs, total = [], 0.0
    for i in range(len(coords) - 1):
        d = haversine(*coords[i], *coords[i + 1])
        segs.append(d)
        total += d
    if total == 0:
        return [coords[0]] * n
    step = total / (n - 1)
    result, acc, seg_i, seg_acc = [coords[0]], 0.0, 0, 0.0
    for _ in range(n - 2):
        target = len(result) * step
        while seg_i < len(segs):
            if seg_acc + segs[seg_i] >= target - acc + 1e-12:
                t = (target - acc - seg_acc) / segs[seg_i]
                p1, p2 = coords[seg_i], coords[seg_i + 1]
                result.append([p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])])
                break
            seg_acc += segs[seg_i]; acc += segs[seg_i]; seg_i += 1
    result.append(coords[-1])
    return result


def directed_hausdorff(a, b):
    return max(min(haversine(*pa, *pb) for pb in b) for pa in a)


def hausdorff(a, b):
    return max(directed_hausdorff(a, b), directed_hausdorff(b, a))


def line_similarity(g1: dict, g2: dict) -> float | None:
    """Similitud Hausdorff entre dos LineStrings. Devuelve None si no comparables."""
    t1, t2 = g1.get("type"), g2.get("type")
    if t1 not in ("LineString", "MultiLineString") or t2 not in ("LineString", "MultiLineString"):
        return None
    c1 = g1["coordinates"] if t1 == "LineString" else g1["coordinates"][0]
    c2 = g2["coordinates"] if t2 == "LineString" else g2["coordinates"][0]
    if len(c1) < 2 or len(c2) < 2:
        return None
    return 1.0 / (1.0 + hausdorff(resample_line(c1), resample_line(c2)))


# ── Helpers de DB ────────────────────────────────────────────────────────────

def get_geom(geom_str: str) -> dict | None:
    try:
        return json.loads(geom_str) if geom_str else None
    except Exception:
        return None


def representative_geom(conn, canonical_id: str) -> tuple[int | None, dict | None]:
    """
    Devuelve (feature_id, geom_dict) representativo de un canonical_structure.
    Prefiere merged_geom; si no, la geometría del primer geo_feature del grupo.
    """
    cs = conn.execute(
        "SELECT merged_geom FROM canonical_structures WHERE id=?", (canonical_id,)
    ).fetchone()
    if cs and cs["merged_geom"]:
        geom = get_geom(cs["merged_geom"])
        if geom:
            # Necesitamos un feature_id real para match_proposals — usamos el primero del grupo
            feat = conn.execute(
                "SELECT id FROM geo_features WHERE canonical_id=? LIMIT 1", (canonical_id,)
            ).fetchone()
            return (feat["id"] if feat else None, geom)
    # Sin merged_geom: usar el primer feature del grupo
    feat = conn.execute(
        "SELECT id, geometry FROM geo_features WHERE canonical_id=? LIMIT 1", (canonical_id,)
    ).fetchone()
    if feat:
        return (feat["id"], get_geom(feat["geometry"]))
    return (None, None)


# ── Lógica principal ─────────────────────────────────────────────────────────

def run(threshold: float = 0.20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Borrar solo pendientes — nunca tocar approved/rejected/split_needed
    conn.execute("DELETE FROM match_proposals WHERE status='pending'")

    # Pares ya decididos (no re-proponer)
    decided = set()
    for r in conn.execute(
        "SELECT feature_a_id, feature_b_id FROM match_proposals WHERE status != 'pending'"
    ).fetchall():
        decided.add((min(r[0], r[1]), max(r[0], r[1])))

    proposals = []

    def add_proposal(id_a, id_b, sim):
        key = (min(id_a, id_b), max(id_a, id_b))
        if key not in decided:
            proposals.append((id_a, id_b, round(sim, 4), "pending", None, None))
            decided.add(key)

    # ── Cargar canonicals con geometría representativa ───────────────────────
    canonicals = []  # [(canonical_id, canon_name, layer_type, repr_feature_id, geom)]
    for cs in conn.execute("SELECT id, name, layer_type FROM canonical_structures").fetchall():
        if cs["layer_type"] not in LINE_TYPES:
            continue
        fid, geom = representative_geom(conn, cs["id"])
        if fid and geom:
            canonicals.append((cs["id"], cs["name"] or "", cs["layer_type"], fid, geom))

    # ── Cargar todos los features lineales ───────────────────────────────────
    all_feats = conn.execute(
        "SELECT id, source, name, layer_type, canonical_id, geometry FROM geo_features "
        "WHERE layer_type IN ('fault','subduction_zone','structure',"
        "'fold_thrust_belt','deformation_zone','hazard_zone')"
    ).fetchall()

    orphans = [f for f in all_feats if not f["canonical_id"]]
    assigned = [f for f in all_feats if f["canonical_id"]]

    # Fuentes ya asignadas a cada canonical (para evitar proponer mismo-fuente)
    canonical_sources: dict[str, set] = {}
    for r in conn.execute(
        "SELECT canonical_id, source FROM geo_features WHERE canonical_id IS NOT NULL"
    ).fetchall():
        canonical_sources.setdefault(r["canonical_id"], set()).add(r["source"])

    print(f"Features lineales: {len(all_feats)} total  |  "
          f"{len(orphans)} huérfanos  |  {len(assigned)} asignados")
    print(f"Canonical structures con geometría: {len(canonicals)}")
    print()

    # ══ FASE 1: Canon vs Canon ═══════════════════════════════════════════════
    print("Fase 1 — Canon vs Canon …", end=" ", flush=True)
    c1_count = 0
    for i, (cid_a, cname_a, lt_a, fid_a, geom_a) in enumerate(canonicals):
        for cid_b, cname_b, lt_b, fid_b, geom_b in canonicals[i + 1:]:
            if cid_a == cid_b or not can_cross_match(lt_a, lt_b):
                continue
            geo = line_similarity(geom_a, geom_b)
            if not geo:
                continue
            sim = combined_sim(geo, cname_a, cname_b)
            if sim >= threshold:
                add_proposal(fid_a, fid_b, sim)
                c1_count += 1
    print(f"{c1_count} propuestas")

    # ══ FASE 2: Huérfano vs Canon ════════════════════════════════════════════
    # Salta si el huérfano ya comparte fuente con algún feature del canónico.
    print("Fase 2 — Huérfano vs Canon …", end=" ", flush=True)
    c2_count = 0
    matched_orphans = set()
    for orf in orphans:
        g_orf = get_geom(orf["geometry"])
        if not g_orf:
            continue
        for cid, cname_c, lt_c, fid_c, geom_c in canonicals:
            if not can_cross_match(lt_c, orf["layer_type"]):
                continue
            if fid_c == orf["id"]:
                continue
            if orf["source"] in canonical_sources.get(cid, set()):
                continue
            geo = line_similarity(g_orf, geom_c)
            if not geo:
                continue
            sim = combined_sim(geo, orf["name"] or "", cname_c)
            if sim >= threshold:
                add_proposal(orf["id"], fid_c, round(sim, 4))
                matched_orphans.add(orf["id"])
                c2_count += 1
    print(f"{c2_count} propuestas  ({len(matched_orphans)} huérfanos con al menos 1 match)")

    # ══ FASE 3: Huérfano vs Huérfano ═════════════════════════════════════════
    unmatched_orphans = [f for f in orphans if f["id"] not in matched_orphans]
    print(f"Fase 3 — Huérfano vs Huérfano ({len(unmatched_orphans)} sin match) …", end=" ", flush=True)
    c3_count = 0
    for i, fa in enumerate(unmatched_orphans):
        g_a = get_geom(fa["geometry"])
        if not g_a:
            continue
        for fb in unmatched_orphans[i + 1:]:
            if fa["source"] == fb["source"] or not can_cross_match(fa["layer_type"], fb["layer_type"]):
                continue
            g_b = get_geom(fb["geometry"])
            if not g_b:
                continue
            geo = line_similarity(g_a, g_b)
            if not geo:
                continue
            sim = combined_sim(geo, fa["name"] or "", fb["name"] or "")
            if sim >= threshold:
                add_proposal(fa["id"], fb["id"], round(sim, 4))
                c3_count += 1
    print(f"{c3_count} propuestas")

    # ── Guardar ──────────────────────────────────────────────────────────────
    conn.executemany(
        "INSERT INTO match_proposals (feature_a_id, feature_b_id, similarity, status, canonical_id, notes) "
        "VALUES (?,?,?,?,?,?)",
        proposals
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM match_proposals").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM match_proposals WHERE status='pending'").fetchone()[0]
    conn.close()

    print(f"\nTotal proposals en DB: {total}  |  Nuevos pending: {pending}  (threshold={threshold})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.20)
    args = parser.parse_args()
    run(args.threshold)
