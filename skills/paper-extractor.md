---
name: paper-extractor
description: >
  Skill integrada de comprensión geológica + extracción de datos hacia GeoJSON.
  Usar SIEMPRE cuando el usuario pida extraer, digitalizar, o estructurar información
  de un paper geológico para incorporar al mapa tectónico. También activar ante:
  "extraé los datos de este paper", "convertí este paper a GeoJSON", "qué estructuras
  tiene este paper", "digitalizá las fallas de este estudio", "pasá esto al mapa",
  "qué puedo sacar de este paper para el mapa", "analizá este paper y extraé",
  "hay cortes en este paper", "digitalizá este perfil sísmico".
  Esta skill integra comprensión científica del paper ANTES de decidir qué extraer,
  ajusta la profundidad del análisis según la escala del estudio, consulta el archivo
  de referencia de categorías on-demand según las estructuras identificadas, extrae
  imágenes de secciones automáticamente si el PDF está disponible, y actualiza el
  bibliography del paper incluida en cada GeoJSON. Claude Code la lee directamente.
---
 
# Paper Extractor v4 — Comprensión Geológica + Extracción a GeoJSON
 
## Estructura de la skill
 
Esta skill usa dos archivos:
 
| Archivo | Cuándo leerlo |
|---|---|
| `skills/paper-extractor.md` (este archivo) | Al inicio de cada extracción — siempre |
| `skills/references/categories.md` | En Fase 1.4, **solo para las categorías identificadas** en ese paper |
 
El archivo de referencia NO se carga completo. En Fase 1.4, una vez identificadas
las categorías presentes, leer únicamente las secciones correspondientes de
`skills/references/categories.md` buscando la sección por nombre de categoría.

**Skills complementarias a consultar según necesidad:**
- `skills/pdf-reading.md` — para leer el PDF del paper desde `Papers/`
- `skills/db-operations.md` — para la carga de features en `sulawesi.db` (Fase 3)
- `skills/raster-georef.md` — si el paper tiene imágenes de secciones a georreferenciar
 
---
 
## PASO 0 — Clasificación de escala
 
Antes de iniciar Fase 1, clasificar el paper:
 
| Escala | Ejemplos | Fase 1 |
|---|---|---|
| **SÍNTESIS** | Revisiones regionales, modelos tectónicos de placa, tomografías globales | Completa — todas las secciones en profundidad |
| **REGIONAL** | Tomografías locales, anisotropía, geodesia, sismicidad de una zona | Completa — profundidad media |
| **LOCAL** | Geoquímica de afloramiento, morfometría, estudios de formaciones únicas | Abreviada — solo 1.1, 1.3, 1.4, 1.5 |
| **DATASET** | KMZ, shapefiles, catálogos sin paper asociado | Saltar Fase 1 — ir directo a Fase 2 con nota de fuente |
 
---
 
## FASE 1 — Comprensión científica
 
### 1.1 — Marco geodinámico y contexto
*(todas las escalas — 2-3 oraciones para LOCAL, párrafo para SÍNTESIS/REGIONAL)*
 
- ¿Qué región y qué proceso tectónico estudia el paper?
- ¿Qué escala temporal y espacial abarca?
- ¿Cómo encaja en el contexto regional del proyecto?
  (Sulawesi: placas Indo-Australiana, Filipinas, Euroasiática; sistema PKF-Matano-Sorong;
  rollback Mar de Célebes; doble subducción Molucas; ESO; Makassar Rift)
### 1.2 — Metodología y datos
*(solo REGIONAL y SÍNTESIS)*
 
- ¿Qué tipo de datos usa?
- ¿Cuáles son las limitaciones clave? (resolución, cobertura, incertidumbre)
- Esta evaluación determina la confiabilidad de la georeferenciación de estructuras.
### 1.3 — Resultados clave
*(todas las escalas — tabla cuantitativa para REGIONAL/SÍNTESIS, lista corta para LOCAL)*
 
Expresar cuantitativamente siempre que sea posible: tasas, magnitudes, profundidades,
edades, velocidades, parámetros geoquímicos, índices morfométricos.
 
### 1.4 — Decisión de extracción + consulta de categorías
 
**Paso A — Identificar categorías presentes:**
 
Recorrer el paper e identificar qué tipos de estructuras son mapeables. Hacer tabla:
 
| Categoría | ¿Presente? | Calidad | Figura clave |
|---|---|---|---|
| ... | sí/no | alta/media/baja | Fig. X |
 
Si aparece una estructura cuya categoría no está segura → usar el decision tree
al final de `references/categories.md` antes de asignar.
 
**Paso B — Leer secciones relevantes de `references/categories.md`:**
 
Una vez identificadas las categorías, leer **solo las secciones de esas categorías**
del archivo de referencia. Esto garantiza que las propiedades específicas y los
criterios de asignación estén frescos antes de construir el GeoJSON.
 
Ejemplo: si el paper tiene `fault`, `cross_section` y `anisotropy`:
```
Read C:\Users\PC\Desktop\Geo\Tectonica\Monografia\skills\references\categories.md
→ buscar sección "fault", "cross_section", "anisotropy"
→ NO cargar las demás secciones innecesariamente
```
 
**Paso C — Señalar aporte diferencial al mapa:**
 
Comparar con bibliografía ya incorporada (Hall 2011/2012, Bellier 2001/2006,
Socquet 2006, Hayes 2018, Di Leo 2012, Hua 2023, Godang 2025, etc.) y señalar
qué agrega este paper que no esté ya cubierto.
 
### 1.5 — Conclusiones vinculables a estructuras
 
Para cada conclusión que refiere a una estructura geográfica específica:
```
Conclusión: [texto cuantitativo del paper]
→ vinculada a: [feature_id tentativo]
→ tipo: slip_rate | kinematics | hazard_assessment | coupling | age | depth |
         velocity | flow_direction | genesis | tectonic_setting |
         fossil_anisotropy | slab_geometry | other
→ implicancia geodinámica: [vinculación al sistema regional más amplio]
→ confidence: high | medium | low
```
 
Conclusiones sin vínculo geográfico preciso → van a `metadata.main_conclusions`.
 
**Regla para `conclusions` en el GeoJSON:**
- Obligatorio en TODAS las features sin excepción.
- Si el paper no concluye nada sobre esa estructura específica:
  `"conclusions": []` + nota en `extraction_notes` explicando por qué.
- Para estructuras solo referenciadas (no estudiadas directamente):
  `"conclusions": []` con nota: "Estructura referenciada como contexto — sin
  conclusiones propias del paper sobre esta entidad."
### 1.6 — Figuras a procesar
 
```
Figuras necesarias para extracción (georeferenciables):
- Fig. X: descripción — para qué estructura
 
Figuras de sección/corte (requieren trazar línea + imagen):
- Fig. X: tipo de sección, label del perfil
 
Figuras de apoyo (interpretación, no extracción directa):
- Fig. X: descripción
 
Figuras no relevantes:
- Fig. X: razón
```
 
Si faltan figuras necesarias → pedirlas explícitamente al usuario antes de continuar.
 
---
 
## FASE 2 — Extracción a GeoJSON
 
### Paso 1 — Cita APA
```
Apellido, I. I., & Apellido2, I. I. (Año). Título. Revista, Vol(N), pp–pp.
https://doi.org/XXXXX
```
Va en cada feature como `source_apa` y en el metadata.
 
### Paso 2 — Coordenadas
 
**Protocolo por tipo de fuente:**
 
**A. Coordenadas directas WGS84 en el paper** → `"coord_quality": "accurate"`
 
**B. Figura con ejes lat/lon WGS84** → leer contra ejes → `"coord_quality": "approximate"`
 
**C. Figura en CRS proyectado con zona identificable (e.g., "UTM Zone 50S"):**
```python
from pyproj import Transformer
 
# Determinar EPSG según hemisferio y zona
# Norte: EPSG 326{zona} (e.g., Zone 50N → 32650)
# Sur:   EPSG 327{zona} (e.g., Zone 50S → 32750)
t = Transformer.from_crs(f'EPSG:{epsg_origen}', 'EPSG:4326', always_xy=True)
lon, lat = t.transform(easting, northing)
 
# VALIDACIÓN OBLIGATORIA — usar bbox conocida de la región del paper
# Si falla la validación: NO usar el resultado, ir a opción D
bbox = (lon_min, lat_min, lon_max, lat_max)  # región esperada
if not (bbox[0] <= lon <= bbox[2] and bbox[1] <= lat <= bbox[3]):
    raise ValueError(f"Conversión inválida: ({lon}, {lat}) fuera de bbox {bbox}")
```
Si la validación falla → documentar el error y usar opción D.
`"coord_quality": "approximate"` + nota detallada en `extraction_notes`.
 
**D. Estimación geográfica manual** (cuando C falla o CRS no identificable):
- Usar referencia geográfica conocida del mismo paper (ciudad, volcán, otro punto)
- Documentar la referencia usada y la precisión estimada (±X km)
- `"coord_quality": "approximate"` + nota en `extraction_notes`
**E. Estructura bien conocida en literatura** (PKF, NST, ESO, etc.):
→ `"coord_quality": "inferred"` + citar fuente de las coordenadas
 
**F. Centroide regional** → último recurso → `"coord_quality": "inferred"` + explicación
 
**Regla absoluta: nunca inventar coordenadas. Nunca usar resultado de pyproj
sin validar contra bbox de la región.**
 
### Paso 2b — Campo `source` y mapeo a `layer_type` de DB

**El campo `source`** identifica el paper en la DB. Debe coincidir exactamente con el
valor `db_source` del paper en `project_state.json`. Consultarlo antes de construir
el GeoJSON:

```python
# Formato: {primer_autor}_{año}_{tema_corto}
# Ejemplos reales del proyecto:
"baillie_2022_sulawesi"
"natawidjaja_2020_palu_rupture"
"husein_2014_luwuk"
```

**Mapeo `category` → `layer_type` de DB** (campo requerido en `geo_features`):

| category (GeoJSON) | layer_type (DB) |
|---|---|
| fault, suture_zone | `fault` |
| subduction_zone | `subduction_zone` |
| fold_thrust_belt | `fold_thrust_belt` |
| deformation_zone, coupling_zone | `deformation_zone` |
| basin, terrane, ophiolite, metamorphic_complex, volcanic_complex, structure, igneous_body | `structure` |
| hazard_zone, seismicity_cluster | `hazard_zone` |
| anisotropy, gps_vector, geophysical_point, cross_section, earthquake, volcano | `structure` |

### Paso 3 — Propiedades estándar (todas las features)
 
```json
{
  "id": "tipo_autor_año_n",
  "name": "Nombre corto — descriptor (~50 chars)",
  "full_name": "Nombre técnico completo para panel lateral del mapa",
  "category": "ver skills/references/categories.md",
  "layer_type": "fault|subduction_zone|fold_thrust_belt|deformation_zone|structure|hazard_zone",
  "source": "db_source del paper (ej. baillie_2022_sulawesi — ver project_state.json)",
  "depth_class": "superficial|cortical|mantélica|mayor",
  "source_apa": "Cita APA completa",
  "source_short": "Apellido et al. (Año)",
  "paper_finding": "Hallazgo cuantitativo específico del paper sobre esta estructura",
  "conclusions": [],
  "coord_quality": "accurate|approximate|inferred",
  "extraction_notes": "Cómo se obtuvieron las coordenadas y cualquier advertencia"
}
```
 
**`depth_class` — criterios de asignación:**
 
| Valor | Definición | Categorías típicas |
|---|---|---|
| `superficial` | Estructura que aflora o se expresa en superficie | fault (traza), ophiolite, volcanic_complex, volcano, terrane, deformation_zone superficial |
| `cortical` | Proceso cortical no aflorante, confinado a la corteza | basin, metamorphic_complex, coupling_zone, seismicity_cluster, hazard_zone, geophysical_point, igneous_body |
| `mantélica` | Proceso del manto o que involucra flujo/estructura mantélica | **anisotropy** (siempre), slab gaps, estructuras de flujo astenosférico |
| `mayor` | Atraviesa múltiples dominios (superficie → corteza → manto) | **subduction_zone, suture_zone** (siempre), fold_thrust_belt de escala litosférica, structure con slab_tear/slab_hole |
 
**Reglas fijas:**
- `anisotropy` → siempre `"mantélica"` sin excepción
- `subduction_zone` → siempre `"mayor"` sin excepción
- `suture_zone` → siempre `"mayor"` sin excepción
- Para el resto: asignar según el dominio principal documentado en el paper
- En caso de duda: preferir `"cortical"` sobre `"superficial"` si no hay exposición directa documentada
**Esquema de cada entrada en `conclusions`:**
```json
{
  "text": "Conclusión parafraseada, cuantitativa cuando sea posible",
  "type": "slip_rate|kinematics|hazard_assessment|coupling|age|depth|velocity|
           flow_direction|genesis|tectonic_setting|fossil_anisotropy|slab_geometry|other",
  "geodyn_implication": "Implicancia geodinámica regional",
  "confidence": "high|medium|low",
  "figure_ref": "Fig. X"
}
```
 
**Convención de nombres (`name`):**
 
| Categoría | Patrón | Ejemplo |
|---|---|---|
| fault | `"Nombre — tipo cinemático"` | `"Lasolo Fault — strike-slip neotectónica"` |
| subduction_zone | `"Nombre slab — régimen"` | `"Banda Slab — rollback 180° curved"` |
| earthquake | `"Lugar año — Mw X tipo"` | `"Palu 2018 — Mw 7.6 strike-slip"` |
| hazard_zone | `"Nombre — tipo"` | `"Slab hole Java Este — 250-500 km"` |
| anisotropy | `"Tipo flujo — ubicación"` | `"Flujo semi-toroidal — borde N Banda"` |
| cross_section | `"Perfil X-X' — tipo"` | `"Perfil A-A' — tomografía Molucas"` |
| basin | `"Nombre — tipo"` | `"Makassar Strait — failed rift"` |
| ophiolite | `"Nombre — edad"` | `"ESO Asera — Cretácico"` |
| volcanic_complex | `"Nombre — setting"` | `"Adang — extensión continental"` |
| terrane | `"Nombre — afinidad"` | `"Sula Spur — continental"` |
| metamorphic_complex | `"Nombre — grado"` | `"PMC — core complex MCC"` |
 
### Paso 4 — Propiedades específicas por categoría
 
**Leer la sección correspondiente en `references/categories.md`** (ya cargada en Fase 1.4.B)
y aplicar el schema exacto definido allí. No improvisar campos.
 
### Paso 5 — Protocolo cross_section
 
*(detallado en `references/categories.md` sección 6)*
 
**Extracción de imagen si PDF disponible en disco:**
```python
import fitz  # pymupdf
from pathlib import Path

def extract_section_figure(pdf_path: str, page_num: int, out_path: str, dpi: int = 200):
    doc = fitz.open(pdf_path)
    page = doc[page_num]  # 0-indexed
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    pix.save(out_path)
    doc.close()
```
Guardar en `mapa/data/sections/{primer_autor}_{año}/`.
 
Si la página tiene múltiples figuras mezcladas:
- Exportar la página completa con el nombre esperado
- Agregar en `extraction_notes`: "Imagen es página completa — recortar manualmente
  la figura X antes de usar en el mapa"
- Notificar al usuario
---
 
## Formato de salida GeoJSON
 
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "source_paper": "Cita APA completa",
    "extraction_date": "YYYY-MM-DD",
    "extractor": "Claude paper-extractor v4",
    "paper_scale": "LOCAL|REGIONAL|SYNTHESIS|DATASET",
    "region": "región",
    "coordinate_system": "EPSG:4326",
    "categories_present": [],
    "custom_categories": {},
    "figures_used": [],
    "sections_present": [],
    "comprehension_summary": "2-3 oraciones del hallazgo principal",
    "main_conclusions": [],
    "total_features": 0
  },
  "features": []
}
```
 
### Geometría por categoría (resumen rápido)
 
| Geometría | Categorías |
|---|---|
| **LineString** | fault (traza discreta), subduction_zone, suture_zone, fold_thrust_belt, volcanic_arc (lineal), cross_section |
| **Polygon** | fault (zona difusa), hazard_zone, basin, terrane, ophiolite, metamorphic_complex, volcanic_complex, volcanic_arc (areal), deformation_zone, coupling_zone, seismicity_cluster |
| **Point** | earthquake, volcano, gps_vector, anisotropy, geophysical_point, igneous_body (puntual) |
| **LineString o Polygon** | structure, igneous_body (areal) |
 
*Para criterios de asignación entre geometrías del mismo tipo → ver `references/categories.md`.*
 
---
 
## Paso 6 — Bibliografía dentro del GeoJSON
 
El bloque de bibliografía del paper va en `metadata.bibliography` del mismo GeoJSON.
**El GeoJSON es el único output.** No se genera ningún archivo externo de bibliografía —
el backend puede leer `metadata.bibliography` de cada GeoJSON directamente.
 
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "source_paper": "Cita APA completa",
    "bibliography": {
      "primer_autor_año": {
        "apa": "Cita APA completa",
        "short": "Apellido et al. (Año)",
        "journal": "Nombre de la revista",
        "year": 2024,
        "doi": "10.xxxx/xxxxx",
        "paper_scale": "LOCAL|REGIONAL|SYNTHESIS|DATASET",
        "topic": "tema principal del paper",
        "region": "región de estudio",
        "categories_extracted": ["fault", "ophiolite"],
        "sections_extracted": [],
        "geojson_file": "autor_año_region.geojson",
        "section_images": []
      }
    }
  },
  "features": [...]
}
```
 
---
 
## FASE 3 — Carga en DB y actualización de estado

Después de generar el GeoJSON, seguir estos pasos. Ver `skills/db-operations.md` para
los snippets de código completos.

### Paso 1 — Guardar GeoJSON en `mapa/fuentes/`

Nombre del archivo: `{db_source}.geojson` (ej. `husein_2014_luwuk.geojson`).

### Paso 2 — Insertar features en `geo_features`

```python
import json, sqlite3
from pathlib import Path

DB = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\backend\sulawesi.db")
geojson_path = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\fuentes\{db_source}.geojson")

conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
data = json.loads(geojson_path.read_text(encoding="utf-8"))

for feat in data["features"]:
    p = feat["properties"]
    conn.execute("""
        INSERT INTO geo_features (source, layer_type, name, geometry, properties, confidence, year)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        p["source"],
        p["layer_type"],
        p.get("name", ""),
        json.dumps(feat["geometry"]),
        json.dumps({k: v for k, v in p.items()
                    if k not in ("source", "layer_type", "name")}),
        p.get("confidence", 1.0),
        p.get("year")
    ))

conn.commit()
n = conn.execute("SELECT COUNT(*) FROM geo_features WHERE source=?",
                 (data["features"][0]["properties"]["source"],)).fetchone()[0]
conn.close()
print(f"Insertados: {n} features")
```

### Paso 3 — Actualizar `project_state.json`

```python
import json
from pathlib import Path

STATE = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\project_state.json")
state = json.loads(STATE.read_text(encoding="utf-8"))

# Encontrar la entrada del paper (usar la clave de project_state.papers)
paper_key = "husein_2014"  # ← clave en project_state.papers
state["papers"][paper_key]["status"] = "digitalizado"
state["papers"][paper_key]["db_source"] = "husein_2014_luwuk"
state["papers"][paper_key]["features_en_db"] = n  # del paso anterior

STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
```

### Paso 4 — Correr matching (opcional pero recomendado)

```bash
cd C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa
python -m backend.scripts.match_geodata --threshold 0.65
```

Genera `match_proposals` para los features nuevos contra los ya existentes.

---

## Reglas de calidad
 
1. **Clasificar escala (Paso 0)** antes de cualquier otra cosa.
2. **Leer este skill completo** al inicio de cada extracción.
3. **Consultar `references/categories.md` on-demand** — solo las secciones de
   las categorías identificadas en Fase 1.4, no el archivo completo.
4. **Fase 1 antes que Fase 2** — nunca saltear, incluso para papers simples.
5. **`conclusions` obligatorio en todas las features** — `[]` con nota si vacío,
   nunca omitir el campo.
6. **Validar conversiones CRS** — si pyproj da resultado fuera del bbox esperado,
   usar estimación manual documentada.
7. **Nunca inventar coordenadas** — documentar siempre cómo se obtuvieron.
8. **Cita APA en cada feature** — sin excepciones.
9. **IDs únicos** — `{tipo}_{primer_autor}_{año}_{n}`.
10. **Un paper = un GeoJSON** — no mezclar papers.
11. **Nombre de GeoJSON** — `{primer_autor}_{año}_{region}.geojson`.
12. **Bibliografía dentro del GeoJSON** — el bloque `bibliography` va en `metadata.bibliography`.
13. **Intentar extraer imágenes de secciones** — si PDF disponible en `Papers/`;
    documentar si falla o si la imagen necesita recorte manual.
14. **Advertir problemas científicos** — circularidad, over-interpretation,
    inconsistencias con literatura, CRS ambiguo, secciones sin ubicación en mapa.
15. **`depth_class` obligatorio en todas las features** — `anisotropy` siempre `"mantélica"`,
    `subduction_zone`/`suture_zone` siempre `"mayor"`. Para el resto, asignar según el
    dominio principal documentado en el paper.
---
 
## Señales de alerta científica
 
Documentar en `extraction_notes` y avisar al usuario:
 
- **Circularidad**: modelo valida sus propios datos (e.g., Hall & Spakman 2015).
- **Over-interpretation**: conclusiones que exceden lo que los datos permiten.
- **Inconsistencia**: contradicción con literatura incorporada al proyecto.
- **Limitaciones de resolución**: smearing tomográfico, catálogos incompletos.
- **CRS no estándar**: figura en UTM sin zona identificada — no convertir.
- **Coordenadas ambiguas**: figura sin grilla lat/lon o con distorsión.
- **Sección sin ubicación**: perfil sin traza en mapa — pedirla al usuario.
- **Discriminación geoquímica ambigua**: cuando dos settings producen la misma firma.
---
 
## Paths del proyecto

| Recurso | Path |
|---------|------|
| PDFs fuente | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\Papers\` |
| GeoJSON salida | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\fuentes\{db_source}.geojson` |
| Imágenes de sección | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\data\sections\{autor}_{año}\` |
| Base de datos | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\backend\sulawesi.db` |
| Estado del proyecto | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\project_state.json` |
| Categorías de referencia | `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\skills\references\categories.md` |

## Integración con el mapa
 
```javascript
// properties.layer_type      → determina el layer destino en layers.js
// properties.source          → vincula con db_source del paper
// properties.source_apa      → panel de bibliografía por feature
// properties.conclusions     → panel lateral al clickear feature
// properties.image_file      → imagen de sección (solo cross_section)
// metadata.comprehension_summary → tooltip del layer
// metadata.paper_scale       → badge LOCAL/REGIONAL/SYNTHESIS
// metadata.bibliography      → bloque de bibliografía del paper
```
