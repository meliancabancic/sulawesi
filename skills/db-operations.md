# SKILL: db-operations

## Activación
Trigger: "crear canonical", "asignar canonical", "insertar feature", "actualizar DB", "auditar DB", "match", "features huérfanos", "sqlite".

---

## Schema de sulawesi.db

### geo_features
| columna | tipo | descripción |
|---------|------|-------------|
| id | INTEGER PK | autoincrement |
| canonical_id | TEXT | FK a canonical_structures.id — NULL = huérfano |
| source | TEXT | identificador del paper (ej. `baillie_2022_sulawesi`) |
| layer_type | TEXT | `fault` \| `subduction_zone` \| `structure` \| `fold_thrust_belt` \| `deformation_zone` \| `hazard_zone` |
| name | TEXT | nombre de la estructura en este paper |
| geometry | TEXT | GeoJSON como string JSON |
| properties | TEXT | JSON con campos extra del paper |
| confidence | REAL | 0.0-1.0, defecto 1.0 |
| year | INTEGER | año del paper |

### canonical_structures
| columna | tipo | descripción |
|---------|------|-------------|
| id | TEXT PK | ej. `canon_5`, `canon_bantimala` |
| layer_type | TEXT | mismo vocabulario que geo_features |
| name | TEXT | nombre canónico de la estructura |
| merged_geom | TEXT | geometría canónica definitiva (GeoJSON string) — **solo el usuario la define en el panel UI** |
| uncert_geom | TEXT | convex hull de todas las geometrías del grupo |
| source_count | INTEGER | número de papers fuente |
| sources | TEXT | JSON array de source IDs |
| properties | TEXT | JSON con metadatos adicionales |
| updated_at | TEXT | datetime |

### match_proposals
Estados: `pending` | `approved` | `rejected` | `split_needed`
Nunca modificar proposals con status != `pending` directamente — usar los endpoints del router.

---

## Conexión

```python
from backend.database import get_conn
conn = get_conn()  # sqlite3.Connection con row_factory=sqlite3.Row
# ...
conn.commit()
conn.close()
```

Desde scripts fuera del backend:
```python
import sqlite3
from pathlib import Path
DB = Path("backend/sulawesi.db")
conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
```

Ejecutar desde: `c:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\`

---

## Operaciones frecuentes

### Crear canonical nuevo (sin feature previo)
```python
conn.execute("""
    INSERT OR IGNORE INTO canonical_structures
        (id, layer_type, name, properties)
    VALUES (?, ?, ?, ?)
""", ("canon_bantimala", "structure",
      "Bantimala Complex (UHP)",
      json.dumps({"P_kbar": "27-28.5", "T_C": "615-640", "age_ma": 119,
                  "facies": "UHP/eclogite", "arm": "SW"})))
conn.commit()
```

### Asignar canonical_id a feature huérfano
```python
conn.execute(
    "UPDATE geo_features SET canonical_id=? WHERE id=?",
    ("canon_bantimala", fid)
)
conn.commit()
```

### Asignar canonical_id a grupo de features por source
```python
conn.execute(
    "UPDATE geo_features SET canonical_id=? WHERE source=? AND name LIKE ?",
    ("canon_bantimala", "baillie_2022_sulawesi", "%Bantimala%")
)
conn.commit()
```

### Actualizar properties de un canonical
```python
row = conn.execute("SELECT properties FROM canonical_structures WHERE id=?",
                   ("canon_bantimala",)).fetchone()
props = json.loads(row["properties"] or "{}")
props["nuevo_campo"] = "valor"
conn.execute("UPDATE canonical_structures SET properties=? WHERE id=?",
             (json.dumps(props), "canon_bantimala"))
conn.commit()
```

### Insertar feature nuevo desde GeoJSON
```python
conn.execute("""
    INSERT INTO geo_features
        (canonical_id, source, layer_type, name, geometry, properties, confidence, year)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    "canon_bantimala",
    "baillie_2022_sulawesi",
    "structure",
    "Bantimala Complex",
    json.dumps({"type": "Polygon", "coordinates": [[...]]}),
    json.dumps({"facies": "UHP", "P_kbar": 27.5, "T_C": 630}),
    0.9,
    2022
))
conn.commit()
```

---

## Queries de auditoría

```sql
-- Features sin canonical (huérfanos)
SELECT id, source, layer_type, name FROM geo_features
WHERE canonical_id IS NULL ORDER BY source, layer_type;

-- Conteo de huérfanos por source
SELECT source, COUNT(*) as n FROM geo_features
WHERE canonical_id IS NULL GROUP BY source ORDER BY n DESC;

-- Canonicals sin merged_geom (pendientes de resolución por usuario)
SELECT id, name, layer_type, source_count FROM canonical_structures
WHERE merged_geom IS NULL ORDER BY layer_type, id;

-- Features por canonical (para ver qué agrupa cada uno)
SELECT cs.id, cs.name, cs.layer_type, COUNT(gf.id) as n_feats,
       GROUP_CONCAT(DISTINCT gf.source) as fuentes
FROM canonical_structures cs
JOIN geo_features gf ON gf.canonical_id = cs.id
GROUP BY cs.id ORDER BY cs.layer_type, cs.id;

-- Verificar que un canonical específico existe y su estado
SELECT id, name, layer_type,
       CASE WHEN merged_geom IS NOT NULL THEN 'TIENE merged_geom' ELSE 'SIN merged_geom' END as geom_status,
       source_count, sources
FROM canonical_structures WHERE id LIKE 'canon_bantimala';
```

---

## Script de matching

```bash
cd c:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa
python -m backend.scripts.match_geodata --threshold 0.65
```

El script genera/actualiza `match_proposals`. No toca proposals con status != `pending`.
Threshold recomendado: 0.65 para alta precisión. Bajar a 0.40 para explorar candidatos dudosos.

---

## Reglas invariables

- `merged_geom` **nunca** se asigna por script — solo el usuario en el panel UI via `/api/geodata/canonical-groups/{id}/resolve`
- Al crear un canonical por script: dejar `merged_geom = NULL`
- El campo `sources` debe ser un JSON array (`json.dumps(["source1", "source2"])`)
- IDs de canonicals: `canon_<nombre_corto>` en snake_case (ej. `canon_bantimala`, `canon_eso`, `canon_mmc`)
- Taxonomy: ver CLAUDE.md sección "Taxonomía de tipos de datos en el proyecto" (Tipo A-H) antes de asignar layer_type
