# Proyecto: Mapa Tectónico Geotectónico — Sulawesi

## Output final
**Mapa tectónico interactivo** (OpenLayers + GeoJSON por paper) → `mapa/`

El mapa cumple la función de una monografía académica. Su estructura S1–S8 organiza
las capas temáticas exactamente como capítulos de un trabajo académico:
- S1 Descripción general → capas de contexto regional
- S2 Sismicidad → epicentros, mecanismos focales, gaps
- S3 Estructura del manto → tomografía, slabs, anisotropía SKS
- S4 Campo gravitatorio → Bouguer, Free-air, geoide
- S5 Flujo calórico → CPD, volcanes PVMBG, manifestaciones geotérmicas
- S6 Estructura → inventario cinemático de fallas activas + deformación neotectónica (slip rates, regímenes de esfuerzo, GPS)
- S7 Petrotectónica → ofiolitas, arcos, terrenos, complejos de acreción
- S8 Metamorfismo → grado metamórfico, P-T, edad

**No hay documento de texto separado. El mapa es el producto final.**

## Estructura del proyecto
```
sulawesi-geotect/
  CLAUDE.md                       ← este archivo
  project_state.json              ← estado del proyecto (leer al inicio)
  papers/                         ← PDFs de los papers fuente
  mapa/
    index.html                      ← frontend único (no usar versiones anteriores)
    backend/                        ← FastAPI + SQLite
    fuentes/                        ← GeoJSONs por paper + datasets estáticos
    mapa_plan.json                  ← plan de trabajo del mapa (leer al inicio)
    data/
      georef_extents.json           ← extents calibrados de capas de referencia
      sections/                     ← figuras extraídas de papers + slices raster
  skills/
    geo-comprehension.md
    paper-extractor.md
    map-layer-manager.md
    frontend-design.md
    api-integration.md
    db-operations.md
    raster-georef.md
    data-pipeline.md
```

## Protocolo de incorporación de papers (obligatorio)

Al agregar un paper nuevo al corpus, seguir estos pasos en orden:

1. **Renombrar el PDF** antes de cualquier otra operación:
   `[S{n}] Autor et al. (año) - descripción corta.pdf`
   Para múltiples secciones: `[S1,S3,S7] Autor et al. (año) - descripción.pdf`
   **Nunca dejar nombres de descarga automática** (`1357-4638-3-PB.pdf`, `S0040195_main.pdf`, etc.)
2. **Agregar entrada en `project_state.json`**: clave snake_case, `file` con ruta actualizada, `status=pendiente`, `sections_relevant`, `nota`
3. **Actualizar tabla de papers en este CLAUDE.md**
4. **Extraer figura**: recortar o exportar la figura/mapa del paper → guardar en `mapa/data/sections/`
   Usar PyMuPDF (`skills/raster-georef.md`) o recorte manual. Nombre: `[autor_año]_figN.png`
5. **Calibrar figura en el mapa**: panel "Verificación — Figuras fuente" → ajustar extents hasta
   que la geometría del paper coincida con la base cartográfica → guardar en `mapa/data/georef_extents.json`
6. **Digitalizar trazando sobre la figura calibrada**: extraer features → GeoJSON → importar a `sulawesi.db`
7. **Asignar canonical**:
   - Si la estructura ya existe en DB: agregar `feat_id` a `FEAT_TO_CANONICAL` en `index.html`
   - Si es estructura nueva: crear canonical en DB, definir `merged_geom` con fe_15,
     agregar entrada en `CANON_HOST_LAYER` (index.html) según tabla de toggles anfitriones
8. **Actualizar `project_state.json`**: `status=digitalizado`, `features_en_db=N`
9. **Agregar tarea en `mapa_plan.json`** bajo la sección correspondiente (`s{n}_d{N}`)
10. **Marcar tarea como `implementado`** con `nota_completado` y fecha

### Tabla de toggles anfitriones para CANON_HOST_LAYER

| Tipo de estructura | Toggle (`layerObjs` key) |
|---|---|
| Falla activa / límite de placa | `tect_key` |
| Zona de subducción | `tect_sub` |
| Régimen de esfuerzo (Jibran) | `clusters` |
| Slab mantélico | `slab_layer` |
| Ofiolita | `faturrakhman` |
| Terreno / arco volcánico | `petrotect` |
| Complejo metamórfico | `core_complexes` |
| Volcán canónico | `volcanoes` |
| Cuenca sedimentaria | *(ninguno — toggle global `merged_geoms`)* |

## Protocolo de inicio de sesión (obligatorio)

Al comenzar cualquier sesión de trabajo en el mapa:

1. **Leer `mapa_plan.json`** → identificar tareas `pendiente`/`parcial` en `orden_ejecucion_recomendado`
2. **Leer `project_state.json`** → verificar estado actual de papers, canonicals, features
3. **Verificar backend**: `curl http://127.0.0.1:8000/api/volcanoes` → si falla, iniciar con `python -m uvicorn backend.main:app --port 8000` desde `mapa/`
4. **Proponer al usuario** las 3–5 tareas de mayor prioridad disponibles

## Checklist obligatorio ante cualquier cambio (obligatorio)

Ante **cada modificación al mapa** — nueva capa, estilo, corrección de DB, nuevo feature, cambio de nombre — verificar:

1. **Interactividad**: el elemento modificado tiene `feat_type` seteado y un case en `map.on('singleclick')` y en `map.on('pointermove')`. Si es clickeable debe abrir el panel correcto; si es hoverable debe mostrar tooltip y cursor en manito.
2. **Fuentes**: toda feature visible en el mapa tiene al menos una cita en `DB[id].papers` o en `properties.source`. Sin fuente citable no se agrega al mapa.
   - **Protocolo de citación**: citar siempre el paper del corpus directamente. No citar fuentes secundarias (citas de citas). Si la información proviene de un paper del corpus, ese paper va en `DB[id].papers[]` del feature correspondiente.
   - **`BIB_STATIC`** es exclusivamente para datasets externos y servicios (GEBCO, GVP, Bird 2003, Slab2, GPlates, WGM2012, etc.) que no son papers del corpus. Los papers del corpus **nunca** van en `BIB_STATIC` — deben estar en `DB[id].papers[]` de al menos un feature.
3. **Dirección de trazas IUGS**: fallas con cinemática definida tienen `sym` + `flip`/`sub_flip` explícitos en `CANON_KIN`. No usar heurísticas automáticas para estructuras con vergencia conocida.
4. **layerObjs + SECTION_KEYS**: toda capa nueva está mapeada en ambos. Verificar que activar la sección S1–S8 correspondiente la muestra.
5. **mapa_plan.json**: la tarea asociada al cambio existe y se marcó `implementado` con `nota_completado` y fecha.
6. **Coherencia visual**: todo elemento nuevo sigue la estética definida — paleta Claude (`--bg`, `--bg2`, `--bg3`, `--accent:#cc785c`, `--text`, `--dim`), tipografía `font-family:monospace`, tamaños en `rem` consistentes con el panel. Tooltips, modales y botones nuevos deben ser indistinguibles de los existentes en diseño. Ningún color, borde o estilo ad-hoc que rompa la unidad visual.

## Plan de trabajo — protocolo estricto

**`mapa_plan.json` es la fuente de verdad del proyecto. TODA modificación al mapa debe quedar registrada ahí, sin excepción.**

- **Solo implementar tareas que están en `mapa_plan.json`** con estado `pendiente` o `parcial`
- Si el usuario propone algo fuera del plan: evaluar si encaja en tarea existente; si no, **agregar la tarea al plan antes de implementar**
- Si una tarea resulta inviable técnicamente: marcar `descartado` con razón en `nota`, proponer alternativa del plan
- **Al completar CUALQUIER tarea** — sin importar si fue pedida explícitamente, surgió como corrección, o fue parte de una auditoría — actualizar `estado` → `implementado` + `nota_completado` + fecha YYYY-MM-DD
- Si la modificación no existía como tarea previa: **crear la tarea y marcarla implementado en el mismo paso**
- **Prohibido sin aprobación explícita**: cambiar estilos visuales de capas existentes, agregar features no planificados, remover funcionalidades

## Papers del proyecto (`papers/`) — lista completa

| Paper | Secciones | Estado DB |
|---|---|---|
| Baillie & Decker (2022) — tectónica estructural | S1,S6,S7 | digitalizado |
| Socquet et al. (2006) — GPS cinemática SE Asia | S1,S2 | digitalizado |
| Walpersdorf et al. (1998) — GPS norte Sulawesi | S1 | digitalizado |
| Natawidjaja et al. (2020) — ruptura PKF 2018 | S1,S2 | digitalizado |
| Natawidjaja et al. (2021) — PKF supershear LiDAR | S2 | digitalizado |
| Lukman et al. (2016) — Falla Matano | S2,S6 | digitalizado |
| Cipta et al. (2016) — PSHA Sulawesi | S2 | digitalizado |
| Greenfield et al. (2021) — deformación NST | S2,S4,S6 | digitalizado |
| Chen & Serhalawan (2024) — sismotectónica Sulawesi | S2 | digitalizado |
| Jibran et al. (2025) — regímenes tectónicos Sulawesi | S2 | digitalizado |
| Jayadi et al. (2023) — tomografía PKF | S2 | digitalizado |
| Di Leo et al. (2012) — flujo mantélico Indonesia, SKS | S3 | digitalizado |
| Cao et al. (2024) — anisotropía mantélica, slabs | S3 | digitalizado |
| Yuan et al. (2024) — Mar de Molucas, flujo mantélico | S3 | digitalizado |
| Hua et al. (2023) — tomografía Banda | S3 | digitalizado |
| Kesumastuti et al. (2025) — slabs múltiples Sulawesi | S3 | digitalizado |
| Heryandoko et al. (2024) — ANT corteza Sulawesi | S3 | digitalizado |
| Supendi et al. (2024) — slabs Sulawesi (9 slices) | S3 | digitalizado |
| Liu et al. (2026) — tomografía S-wave Indonesia | S3 | digitalizado |
| Yang et al. (2025) — espesor cortical PKF (OBS) | S3,S6 | digitalizado |
| Lestari et al. (2021) — tomografía P-wave Makassar | S3 | digitalizado |
| Shih et al. (2026) — gravimetría aérea Sulawesi | S4 | digitalizado |
| Pratama et al. (2025) — PFA geotérmica Sulawesi | S5,S4 | digitalizado |
| Faturrakhman et al. (2024) — ESO Asera | S7 | digitalizado |
| Faturrakhman et al. (2025) — Tanjung Api H2 | S5,S7 | digitalizado |
| Husein et al. (2014) — estructuras Luwuk | S1,S6,S7 | digitalizado |
| Hikmy / Isbram (2025) — brazo este Sulawesi | S2,S6 | digitalizado |
| Surono (2012) — tectonoestratigrafía E Sulawesi | S1,S7 | digitalizado |
| Satyana & Purwaningsih (2011) IPA — colisión microplacas | S1,S7 | digitalizado |
| Satyana et al. (2011) IAGI — evolución tectónica | S1,S7 | digitalizado |

Actualizar esta tabla cada vez que se digitalice un paper nuevo.

## Contexto de presentación (crítico)

El mapa es un **trabajo académico con entrega y presentación oral**. La audiencia (oyentes) interactuará con el mapa en vivo. Esto implica:

- Todo elemento visual debe tener fuente citable (paper, dataset, o servicio con referencia APA)
- El mapa debe poder comunicar **conclusiones científicas por sección**, no solo mostrar datos
- La **bibliografía completa** debe ser accesible desde el mapa (modal con todas las fuentes)
- La UI debe ser legible a distancia (proyector) y navegable por alguien que no lo construyó
- Las **geometrías canónicas** (merged_geom) deben estar definidas para las estructuras principales antes de la presentación — sin merged_geom, las estructuras clave (PKF, Matano, Sorong) aparecen como trazas múltiples sin consenso

**Tres tareas obligatorias antes de la presentación:**
1. `fe_15` — Herramienta de dibujo de merged_geom (actualmente el bloqueador más crítico)
2. `fe_16` — Panel de conclusiones por sección S1–S8
3. `fe_17` — Modal de bibliografía completa en APA

## Usuario
Estudiante avanzado Cs. Geológicas, orientación geoinformática. Nivel técnico
universitario avanzado. No simplificar conceptos salvo pedido explícito.
Fundamentar con papers cuando corresponda. Señalar debates e incertidumbres.
Idioma de respuesta: español. Términos técnicos del dominio en inglés sin traducir.

## Formato de respuesta (estricto)
- Sin introducción ni cierre conversacional
- Sin repetir el enunciado de la pregunta
- Sin bullets/headers/negritas decorativas salvo pedido explícito
- Sin disclaimers ni definiciones de abreviaturas del dominio
- Incertidumbre: una palabra ("aproximadamente"), no un párrafo
- No ofrecer continuar ni preguntar si fue útil
- Para archivos: no confirmar recepción, no describir lo que se va a hacer, hacerlo directamente

## Interacción con archivos
- Leer solo la sección o columnas necesarias; nunca el archivo completo salvo que sea imprescindible
- Para archivos grandes: usar `wc -l` / `stat` antes de leer; preferir `head`/`grep` selectivo
- No confirmar recepción ni describir lo que se va a hacer
- Si el archivo fue referenciado en el mismo contexto, no volver a leerlo

## Gestión de contexto (obligatorio — reducir tokens)

`index.html` tiene 6200+ líneas y es el mayor consumidor de contexto. Protocolo estricto:
1. **Nunca** hacer `Read` de `index.html` sin `offset`+`limit` acotado (máx 80 líneas)
2. Flujo obligatorio para editar `index.html`: `Grep` → `Read offset+limit` → `Edit`. Sin excepciones.
3. Outputs de Bash: siempre agregar `| head -30` (o menos) a greps y queries SQLite
4. Scripts Python inline: imprimir solo lo necesario; nunca volcar tablas completas
5. Verificaciones post-Edit: no releer el archivo editado ni hacer curl de confirmación salvo que la lógica sea no trivial
6. `mapa_plan.json`: no leer nunca el archivo completo; usar `python -c "re.search(...)"` para extraer solo la tarea relevante
7. Al inicio de sesión: leer solo `orden_ejecucion_recomendado` del plan, no el plan entero

## Skills — activación

| Trigger | Skill |
|---|---|
| papers, figuras, tomografías, beachballs, P-T, SKS, GPS, preguntas tectónicas | `skills/geo-comprehension.md` |
| "extraé", "GeoJSON", "pasá al mapa", "digitalizá", "qué estructuras", "hay cortes" | `skills/paper-extractor.md` |
| "actualizá el mapa", "agregá la capa", "implementá el popup", mapa OpenLayers | `skills/map-layer-manager.md` |
| desarrollo web, CSS, JS, HTML del mapa, Chart.js, panel, slider | `skills/frontend-design.md` |
| "integrar API", "nuevo endpoint", "proxy", ISC, IRIS, GPlates, ICGEM, WorldHeatFlow, NGL | `skills/api-integration.md` |
| "crear canonical", "asignar canonical", "insertar feature", "auditar DB", sqlite, match | `skills/db-operations.md` |
| "extraé figura", "georreferenciá", ImageStatic, rasterio, PyMuPDF, slice tomográfico, CPD, calibrar | `skills/raster-georef.md` |
| "filtrar CSV", "convertir a GeoJSON", GVP, NGL, IHFC, WorldHeatFlow, pipeline de datos | `skills/data-pipeline.md` |
| "auditar", "auditoría", "audit", "chequear todo", "revisar el mapa", "correr auditor" | `skills/map-auditor.md` |
| "agente geólogo", "revisar cartografía", "auditar S1–S8", "validar posición", "revisar georef", "chequear extents" | Agente geólogo-cartógrafo (spawn Agent con prompt de auditoría científica S1–S8) |
| "agente UX", "revisar UI", "auditar dispositivos", "revisar experiencia", "multi-device" | Agente UX/multi-dispositivo (spawn Agent con prompt de auditoría UX y touch targets) |
| "agente demo", "recorrido primera visita", "QA usuario", "simular oyente", "probar navegación" | Agente de recorrido demo (spawn Agent: simula primera visita, verifica welcome overlay, capas iniciales, paneles, backend) |
| "agente conclusiones", "revisar fe_16", "validar conclusiones", "chequear contenido científico" | Agente de conclusiones S1–S8 (spawn Agent: audita contenido científico de CONCLUSIONS, verifica correctitud y citas) |
| "agente bibliografía", "revisar fe_17", "verificar APA", "papers faltantes", "BIB_STATIC" | Agente de bibliografía APA (spawn Agent: verifica completitud del modal fe_17 vs corpus de 30 papers) |
| "agente raster", "verificar extents", "alineación raster", "georef_extents", "chequear S3 S4" | Agente de alineación raster S3–S4 (spawn Agent: verifica que todos los extents en georef_extents.json son geográficamente coherentes) |
| "agente merged_geom", "auditar merged_geom", "canonicals sin geom", "priorizar geometrías" | Agente de merged_geom críticos (spawn Agent: audita DB para identificar canonicals sin merged_geom y prioriza por importancia) |

## Contexto geodinámico mínimo
Triple unión: Indo-Australiana + Pacífica/Filipinas + Euroasiática.
Convergencia IA hacia N: ~70 mm/año. Sistema Sorong: ~120 mm/año.
PKF slip: ~35-45 mm/año. Subducción NST inicio: ~8-9 Ma. Colisión Banggai-Sula: ~5-6 Ma.
Estructuras clave: NST/Minahassa Trench, PKF, Matano, Sorong, doble subducción
Molucas (Sangihe+Halmahera), arco Banda rollback, PMC/MMC, Bantimala UHP (119 Ma).
Marco de referencia completo → `skills/geo-comprehension.md`.
