# Skill: Map Auditor

## Activación
Trigger: "auditar", "auditoría", "audit", "chequear todo", "revisar el mapa"

## Rol
Auditor técnico del mapa tectónico. Ejecuta el checklist completo definido en CLAUDE.md y reporta hallazgos con severidad. No implementa correcciones — solo diagnostica y lista tareas pendientes.

---

## Protocolo de auditoría (ejecutar en orden)

### 1. CANONICALS — Estado DB

```python
import sqlite3, json
conn = sqlite3.connect('backend/sulawesi.db')
c = conn.cursor()

# 1a. Fuentes
c.execute("SELECT id, name, source_count FROM canonical_structures WHERE source_count=0")
sin_fuentes = c.fetchall()

# 1b. Sin merged_geom
c.execute("SELECT id, name FROM canonical_structures WHERE merged_geom IS NULL")
sin_geom = c.fetchall()

# 1c. FEAT_TO_CANONICAL vs DB — referencias huérfanas
c.execute("SELECT DISTINCT canonical_id FROM geo_features WHERE canonical_id IS NOT NULL")
cids_en_feats = {r[0] for r in c.fetchall()}
c.execute("SELECT id FROM canonical_structures")
cids_en_cs = {r[0] for r in c.fetchall()}
huerfanos = cids_en_feats - cids_en_cs
```

Reportar: sin_fuentes, sin_geom, huerfanos

### 2. INTERACTIVIDAD — index.html

Verificar que cada `feat_type` declarado en features tiene:
- Case en `map.on('singleclick')` (abre panel correcto)
- Case en `map.on('pointermove')` (tooltip + cursor)

Buscar feat_types en uso:
```bash
grep -n "feat_type.*'[a-z]" index.html | grep "f\.set\|feat_type:" | sort -u
```

Buscar cases en singleclick y pointermove:
```bash
grep -n "type==='" index.html | grep -v "//"
```

Reportar feat_types sin case en alguno de los dos handlers.

### 3. SECTION_KEYS vs CANON_LT_SECTION — Coherencia

Verificar:
- Cada layer en `SECTION_KEYS[s]` existe en `layerObjs`
- `merged_geoms` está en SECTION_KEYS de todas las secciones que tienen canonicals
- Cada `layer_type` en `CANON_LT_SECTION` corresponde a secciones donde `merged_geoms` está en SECTION_KEYS

### 4. CANON_KIN — Cobertura de canonicals con merged_geom

Verificar que todos los canonicals de tipo `fault` y `subduction_zone` con merged_geom tienen entrada en `CANON_KIN` con `sym` + `flip`/`sub_flip` correctos.

```bash
# Canonicals fault/subduction sin entrada en CANON_KIN
grep -o "canon_[0-9a-z_]*" index.html | sort -u | grep -v "#\|//"
```

Cruzar con CANON_KIN para identificar faltantes.

### 5. COLORES CARTOGRÁFICOS

Buscar colores que NO pertenecen al sistema establecido:
- UI palette: `--bg`, `--bg2`, `--bg3`, `--accent:#cc785c`, `--text`, `--dim`
- Cartográficos válidos: `#111`/`#000` (estructural IUGS), `FACIES_COLOR` (S8), `PETROTECT_COLORS` (S7), depth-coded spectrum (S2), `#7060b0` purple (S3 mantle), `#8a6d00` (fold-thrust belt), `#60a5fa` (geomorfológico)

```bash
grep -n "color:.*#" index.html | grep "ol\.style\|Style\|stroke\|fill" | grep -v "var(--\|rgba(0,0,0\|rgba(255,255\|#111\|#000\|1a0533\|2e86c1\|1e8449\|5b2c6f\|8a6d00\|7060b0\|60a5fa\|6a7888\|c85040\|c89040\|4888cc\|ffdd2c\|e47820\|28b460\|3088dc\|ef4444\|f97316\|22c55e"
```

Reportar colores no reconocidos con contexto.

### 6. COVERED_BY_CANON — Supresión completa

Verificar que todos los feat_ids en `FEAT_TO_CANONICAL` tienen:
a) El canonical referenciado existe en `canonical_structures` DB
b) El layer que genera esa feature tiene chequeo `mergedGeomLayer.getVisible() && COVERED_BY_CANON.has(...)` en su style function

Layers a verificar: `keyFaultStyle`, `subductionStyle`, `newFaultStyleFn`, `jibranStyleFn`

### 7. mapa_plan.json — Tareas pendientes

```bash
grep -c '"estado": "pendiente"' mapa_plan.json
grep '"estado": "pendiente"' -A2 mapa_plan.json | grep '"id"'
```

### 8. LEGEND DEF — Coherencia con colores actuales

Verificar que `LEGEND_DEF` en index.html no referencia colores viejos (`#40e0b0`, `#ff8844`, etc.).

---

## Formato de reporte

```
=== AUDITORÍA MAPA TECTÓNICO — [fecha] ===

CRÍTICO (bloquea presentación):
  [ ] item

MAYOR (afecta calidad académica):
  [ ] item

MENOR (mejora visual/UX):
  [ ] item

OK:
  [x] item
```

Severidad:
- **CRÍTICO**: canonical sin fuentes, feat_type sin singleclick handler, color cartográfico incorrecto en capa principal
- **MAYOR**: merged_geom faltante para estructura clave (PKF, NST, etc.), SECTION_KEYS inconsistente, supresión COVERED_BY_CANON incompleta
- **MENOR**: leyenda desactualizada, tareas pendientes en plan, color secundario fuera de sistema

---

## Notas
- No modificar archivos durante la auditoría — solo diagnosticar
- Si el backend no está corriendo, indicarlo y auditar solo lo que sea accesible desde archivos estáticos
- Siempre terminar con el conteo: N críticos / M mayores / K menores
