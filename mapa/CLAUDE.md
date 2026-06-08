# CLAUDE.md — Proyecto Sulawesi

## INTERACCIÓN CON ARCHIVOS
- No confirmar recepción del archivo. No describir lo que se va a hacer, hacerlo directamente.
- Leer solo la sección o columnas necesarias, nunca el archivo completo salvo que sea imprescindible.
- No reproducir fragmentos del archivo en la respuesta salvo pedido explícito.
- Si el archivo fue referenciado en el mismo contexto, no volver a leerlo.

## PROYECTO
**El mapa tectónico interactivo ES el output final.** Cumple la función de una
monografía académica a través de su estructura S1–S8:

Pipeline: paper PDF → comprensión científica → GeoJSON → capas HTML organizadas por sección

S1 Descripción general | S2 Sismicidad | S3 Estructura del manto | S4 Campo gravitatorio
S5 Flujo calórico | S6 Estructura | S7 Petrotectónica | S8 Metamorfismo

No hay documento de texto separado.

## USUARIO
Estudiante avanzado Cs. Geológicas, orientación geoinformática. Nivel técnico
universitario avanzado. No simplificar conceptos salvo pedido explícito. Fundamentar
con papers cuando corresponda. Señalar debates o incertidumbres en la literatura.
Idioma de respuesta: español. Términos técnicos estándar del dominio en inglés sin traducir.

## FORMATO DE RESPUESTA (estricto)
- Sin introducción ni cierre conversacional
- Sin repetir el enunciado de la pregunta
- Sin bullets/headers/negritas decorativas salvo pedido explícito
- Sin disclaimers ni definiciones de abreviaturas del dominio
- Incertidumbre: una palabra ("aproximadamente"), no un párrafo
- No ofrecer continuar ni preguntar si fue útil

---

## CONTEXTO GEODINÁMICO

### Marco de placas
Sulawesi ocupa la intersección de tres placas mayores: Indo-Australiana (convergencia
~70 mm/año hacia N), Pacífica/Filipinas (subducción oblicua desde NE) y Euroasiática/
Sunda (bloque estable al oeste). El resultado es una isla con forma de orquídea —
cuatro brazos — que registra múltiples colisiones desde el Oligoceno.

### Historia de ensamblaje (Hall 2011, Baillie & Decker 2022)
- Brazo Oeste: afinidad Sundaland, margen continental con cinturón plegado (WSFB)
- Brazo Norte: arco volcánico activo, ligado a subducción NST; inicio ~8-9 Ma
- Brazo Este: ofiólita (ESO, ~123 Ma), obductada sobre Banggai-Sula en el Neógeno
- Brazo SE: colisión del microcontinente Banggai-Sula (~5-6 Ma), terreno de afinidad
  australiana; es la colisión más reciente y la que cierra el brazo este
- Bantimala Complex (SW): UHP metamórfico, 119 Ma, evidencia de subducción profunda
  pre-colisión; único registro UHP regional confirmado

### Estructuras clave — naturaleza y cinemática
**PKF (Palu-Koro Fault):** falla sinistral (left-lateral) N-S, ~35-45 mm/año
  (Socquet et al. 2006, Walpersdorf et al. 1998). Conecta NST (norte, junction
  [119.30, 1.21]) con Falla Matano (sur, junction [120.54, -3.32]). Segmentada:
  Saluki → Palu → Donggala → Tanimbaya (Natawidjaja et al. 2020/2021). La ruptura
  Mw 7.5 de 2018 fue supershear y multisegmento.

**NST (North Sulawesi Trench / Minahassa Trench):** megathrust; subducción del Mar
  de Célebes bajo el brazo norte. Inicio ~8-9 Ma. Plano de Benioff south-dipping.
  junction oeste con PKF [119.30, 1.21]; junction este con Sangihe [125.76, 1.84].

**Matano Fault:** falla dextral E-W, conecta PKF (oeste) con el sistema Sorong
  (este) en la triple junction [122.05, -3.34]. Junto con PKF define el límite sur
  del bloque del brazo norte.

**Sistema Sorong:** falla dextral mayor E-W, ~120 mm/año, límite entre placa del
  Mar de Banda (sur) y bloque Bird's Head/Pacífico (norte). Se divide en rama
  principal (Sorong s.s.) y rama sur; conecta con Matano en [122.05, -3.34].

**Doble subducción del Mar de Molucas (Sangihe + Halmahera):**
  - Sangihe (oeste): subducción oeste-dipping; arco Sangihe activo al oeste
  - Halmahera (este): subducción este-dipping; back-arc basin entre ambos arcos
  - Entre ambos: Molucca Sea Collision Complex (acreción/colisión en progreso)
  - Esta doble subducción opuesta es única globalmente

**MST (Makassar Strait Thrust):** thrust compresivo al oeste de Sulawesi,
  límite entre Sunda y el bloque de Sulawesi. Segmentado: Norte (canon_286),
  Central-Norte (canon_287), Mamuju (canon_288), Somba (canon_289).

**SST (South Sulawesi Transform):** límite sur de la microplaca de Sulawesi/
  Banda; conecta Matano [122.05, -3.34] con el arco de Banda al SE.

**Banda Slab:** subducción de litosfera oceánica australiana 180° curvada bajo
  el arco de Banda (rollback desde ~15 Ma). Feature mantélica, no traza de superficie.

**WSFB (West Sulawesi Fold Belt):** cinturón de pliegues y cabalgamientos en el
  brazo oeste; deformación compresiva del margen continental de Sundaland.

**Batui Thrust:** cabalgamiento activo NE-SW en el extremo NE del brazo este,
  área de Luwuk; asociado a la colisión con Banggai-Sula.

### Taxonomía de tipos de datos en el proyecto

**TIPO A — Trazas de límite de placa/microplaca** (deben tener canonical obligatorio):
  Fallas de desgarre principales (PKF, Matano, Sorong, EWF, WWF), zonas de
  subducción (NST, Sangihe, Halmahera, MST, Flores-Banda, SST), transforms
  (N Halmahera, Sula/NE Sulawesi). Son LineStrings en superficie. Múltiples papers
  las mapean: se unifican en un canonical cuando son la misma estructura.

**TIPO B — Estructuras secundarias / regionales** (canonical propio, no mezclar con Tipo A):
  Batui Thrust, WSFB, NSFTB, Hamilton Fault, Buton Thrust, Tomini Gulf FZ,
  Selayar FZ, Balantak, West Buru FZ, Pasini Thrust, Lobu-Balolang FZ.
  Son estructuras reales con expresión en superficie pero dentro de microplacas,
  no límites entre ellas.

**TIPO C — Geometrías mantélicas / slabs** (canonical propio tipo slab, nunca mezclado con A/B):
  Banda Slab, Sula Slab, Celebes Slab, slabs tomográficos. Son cuerpos en el
  manto, no trazas en superficie. Los papers que los reportan (Hall & Spakman 2015,
  Hua 2023, Kesumastuti 2025, Liu 2026, Cao 2024, Yuan 2024) aportan datos de
  profundidad y forma de slab, no trazas de falla.

**TIPO D — Zonas de régimen tectónico** (canonical propio tipo structure, Jibran et al.):
  Los 10 clusters de Jibran (2025) definen zonas de stress homogéneo por clustering
  de mecanismos focales. No son fallas. No representan el mismo objeto que ninguna
  estructura Tipo A/B. Cada cluster tiene su propio canonical (canon_jib_01 a 10).

**TIPO E — Datos geofísicos puntuales o vectoriales** (no necesitan canonical de falla):
  Vectores de flujo mantélico (SKS splitting: Di Leo 2012, Cao 2024, Yuan 2024),
  estaciones GPS/GNSS (Socquet 2006, Walpersdorf 1998), perfiles OBS (Yang 2025),
  modelos de geoide (Shih et al. 2026), polos de Euler. Son observaciones, no
  estructuras mapeables como límites.

**TIPO F — Zonas de amenaza / gaps sísmicos** (asociar al canonical estructural, panel):
  Brechas sísmicas, seismic gaps, hazard zones. "Gap sísmico" = zona SIN sismos
  recientes = área de acumulación de stress, no una falla diferente. Se asocian
  al canonical de la falla/subducción que los contiene, como dato del panel lateral.
  NUNCA crear un canonical nuevo para un gap sísmico.

**TIPO G — Eventos sísmicos** (asociar al canonical de la falla que rupturó):
  Trazas de ruptura coseísmica (Palu 2018 Mw 7.5). Son trazas del evento, no de la
  estructura permanente. Se asignan al canonical de la falla (PKF = canon_5) como
  documentación del evento, no como definición de la geometría canónica.

**TIPO H — Unidades geológicas** (canonical propio tipo structure/geological_unit):
  Molucca Sea Collision Complex, East Sulawesi Ophiolite, Bantimala Complex,
  Banggai-Sula microcontinent. Son cuerpos geológicos, no límites activos.

### Regla de oro para canonical matching
Antes de asignar feature X al canonical Y, responder:
1. ¿Son ambos del mismo TIPO (A-H)? Si no → NO agrupar.
2. ¿Representan la misma estructura física individual? Si no → NO agrupar.
3. ¿Vienen de distintos papers (sources distintos)? Si vienen del mismo source → revisar.
4. ¿Se solapan geográficamente o son continuos? Si están en regiones distintas → revisar split.
Solo si las 4 respuestas son afirmativas: agrupar en el mismo canonical.

La proximidad geográfica sola NO es criterio suficiente.
El nombre similar solo NO es criterio suficiente.
Un cluster que "describe" una zona de falla NO es la misma cosa que la falla.

---

## MAPA — ARQUITECTURA TÉCNICA

**Stack:** OpenLayers 6 + FastAPI + SQLite (`backend/sulawesi.db`)
**Directorio:** `c:\Users\PC\Desktop\Geo\Tectonica\Monografia\mapa\`
**Backend:** `python -m uvicorn backend.main:app --port <puerto>` desde `mapa/`
  Routers activos: earthquakes, annotations, catalog_proxy (USGS live + ISC),
  volcanoes, slabs, faults, geodata, stations
**Frontend:** `index.html` (único archivo frontend — NO usar versiones anteriores)
**Datos estáticos:** `fuentes/` — GeoJSONs por paper + GPS, GPS placas, heat flow, geotérmicos
**Plan de trabajo:** leer `mapa_plan.json` al inicio de cada sesión. Actualizar al finalizar cada tarea.

## CONTEXTO DE PRESENTACIÓN

El mapa es entrega académica con presentación oral ante audiencia. Tres requerimientos no negociables:

1. **Todo elemento visual tiene cita APA** — papers, datasets, servicios de tiles. Sin cita no va al mapa.
2. **Conclusiones por sección** — cada S1–S8 debe tener un panel de síntesis científica (fe_16). Sin conclusiones el mapa muestra datos pero no comunica.
3. **Bibliografía completa accesible** — modal con todas las fuentes en APA (fe_17). Requerimiento académico.

La **herramienta de dibujo de merged_geom (fe_15)** es el bloqueador crítico para la presentación: sin geometrías canónicas definidas, PKF, Matano, Sorong y las unidades H aparecen como trazas múltiples sin consenso.

## MAPA — PLAN DE TRABAJO (protocolo obligatorio)

**Toda tarea de mapa debe estar en `mapa_plan.json`. No implementar nada fuera del plan sin aprobación explícita.**

- Leer `mapa_plan.json` al inicio de cada sesión — identificar tareas `pendiente`/`parcial` según `orden_ejecucion_recomendado`
- Al completar: actualizar `estado` → `implementado` + `nota_completado` + fecha en el plan
- Si una tarea resulta inviable: marcar `descartado` con razón técnica, proponer alternativa del plan
- **Prohibido sin aprobación**: cambiar estilos de capas existentes, agregar features no planificados, remover funcionalidades

## MAPA — PRINCIPIOS DE DISEÑO FRONTEND (no negociables)

1. **Todo elemento visual debe tener cita APA** — sin cita, no va al mapa. Esto incluye
   features individuales, polígonos hardcodeados, vectores, y capas raster. El botón ⓘ
   en capas raster abre un panel bibliográfico aunque la capa no sea clickeable como feature.

2. **Una sola capa por concepto** — si dos fuentes miden lo mismo (ej. sismicidad de GCMT
   y de ISC), se unifica en una capa con filtros, no dos capas separadas.

3. **Capas temáticas OFF por defecto** — al abrir el mapa solo están activas:
   Sentinel-2 (fondo) + zonas de subducción IUGS + fallas límite de placa IUGS.
   Todo lo demás inicia apagado.

4. **Mutex de fondos** — hay tres opciones de base layer: Sentinel-2, ESRI Hybrid y GEBCO.
   Siempre debe haber al menos uno activo. Al activar ESRI Hybrid → Sentinel se apaga.
   Al desactivar cualquier fondo alternativo → si no queda otro activo, Sentinel vuelve a ON.

5. **Panel de capas organizado por secciones S1–S8** — cada capa tiene su toggle
   individual dentro de su sección temática. No agrupar capas de distintas secciones.

6. **Panel canónico con debate explícito** — al clickear una estructura, el panel muestra:
   (a) autores que apoyan la geometría del mapa + imagen de su figura,
   (b) autores con interpretación alternativa + imagen de su figura.
   No colapsar contradicciones en una sola descripción.

7. **Zoom diferenciado** — Tipo A (límites de placa) visibles desde zoom 4. Tipo B
   (estructuras secundarias) y catálogos sísmicos solo desde zoom 7–8.

8. **Seguir `mapa_plan.json`** — leerlo al inicio de cada sesión de trabajo en el mapa.
   Actualizar el estado de las tareas al completarlas.

---

## MAPA — BASE DE DATOS: CONCEPTOS CLAVE

### geo_features
Cada fila es una traza digitalizada de un paper. Columnas relevantes:
- `source`: identificador del paper (ej. `baillie_2022_sulawesi`)
- `canonical_id`: FK a `canonical_structures` — NULL si aún sin asignar
- `layer_type`: `fault` | `subduction_zone` | `structure` | `fold_thrust_belt` | `hazard_zone`
- `geometry`: GeoJSON LineString/Polygon/Point

### canonical_structures
Cada fila es una estructura tectónica única (la entidad real, no la traza de un paper).
- `merged_geom`: geometría canónica definitiva — **SIEMPRE la define el usuario
  manualmente en el panel UI, nunca auto-asignar, nunca proponer coordenadas.**
- `layer_type`: mismo vocabulario que geo_features

### match_proposals
Pares de features comparados por similitud geométrica + nombre.
Estados: `pending` | `approved` | `rejected` | `split_needed`
Script: `python -m backend.scripts.match_geodata [--threshold 0.20]`

---

## MAPA — REGLAS DE MATCHING

Un canonical agrupa features que representan la misma estructura tectónica real
digitalizadas desde distintos papers. "Unificar repetidos", NO "agrupar por agrupar".

### Reglas invariables
- `merged_geom` la define el usuario en el panel UI. Nunca auto-asignar ni proponer.
- Gaps sísmicos NO son límites de placa. Panel lateral de la estructura asociada.
- Clusters de régimen (Jibran) son zonas de stress, no fallas. Canonical propio.
- Trazas de ruptura sísmica (eventos) se asignan a la falla que rupturó, pero NO
  definen la geometría canónica de esa falla.
- Slabs/features mantélicos tienen canonical propio, nunca mezclado con fallas de superficie.
- Todas las trazas Tipo A (límites de placa/microplaca) deben tener canonical asignado.
- GPlates define los junction nodes topológicos; son la referencia de verdad para
  conectividad. Los canonicals deben poder conectar en esos nodos.

### Topología GPlates — junction nodes críticos
- `[119.2994, 1.2092]`: NST oeste ↔ PKF norte
- `[125.7632, 1.8364]`: NST este ↔ Sangihe oeste
- `[120.5354, -3.3186]`: PKF sur ↔ Matano oeste
- `[122.0471, -3.3383]`: Matano este ↔ Sorong ↔ SST (triple junction)

### Qué contribuye cada fuente principal
- **GPlates topology:** circuito topológico de referencia. Verdad para conectividad.
- **GEM Global Active Faults:** trazas de fallas activas mayores (Tipo A/B). Confiables.
- **Bird 2003:** límites globales de placa. Muchos segmentos fuera del área core.
- **Jibran 2025:** clustering de mecanismos focales → zonas de régimen (Tipo D).
- **Natawidjaja 2020/2021:** ruptura 2018 Palu (Tipo G) + segmentación PKF (Tipo A).
- **Yang 2025:** datos OBS, espesor cortical a lo largo de PKF (Tipo E, no trazas).
- **Cao 2024, Yuan 2024, Di Leo 2012:** flujo mantélico/anisotropía SKS (Tipo E).
- **Hall & Spakman 2015, Hua 2023, Kesumastuti 2025, Liu 2026:** slabs (Tipo C).
- **Socquet 2006, Walpersdorf 1998:** GPS/velocidades (Tipo E) + trazas PKF (Tipo A).
- **Baillie & Decker 2022:** tectónica estructural completa; aporta Tipos A, B y H.
- **Serhalawan 2024:** sismotectónica activa; aporta Tipos A, B, F.
- **Hikmy 2025:** estructuras brazo este (Batui, Pasini, Lobu-Balolang) → Tipo B.

---

## MAPA — ESTADO DE CANONICALS CLAVE (2026-05-31)

**Actualizar esta tabla cada vez que cambie merged_geom o el conteo de features.**
Fuente de verdad: `SELECT id, name, layer_type, merged_geom IS NOT NULL, COUNT(gf.id) FROM canonical_structures cs LEFT JOIN geo_features gf ON gf.canonical_id=cs.id GROUP BY cs.id`

### Tipo A — Límites de placa/microplaca
| Canonical | Estructura | Feats | merged_geom |
|-----------|-----------|-------|-------------|
| canon_5 | PKF | 20 | **pendiente usuario** |
| canon_19 | Matano Fault Zone | 6 | **pendiente usuario** |
| canon_364 | NST / North Sulawesi Megathrust | 11 | sí |
| canon_369 | Sangihe Subduction Zone | 7 | sí |
| canon_805 | Halmahera Subduction Zone | 5 | sí |
| canon_286 | MST Norte | 4 | sí |
| canon_287 | MST Centro-Norte | 1 | sí |
| canon_288 | MST Mamuju | 4 | sí |
| canon_289 | MST Somba | 1 | sí |
| canon_1920 | South Sulawesi Transform | 2 | pendiente |
| canon_1921 | Sorong Fault Zone West | 4 | pendiente |
| canon_1922 | Sula/NE Sulawesi Transform | 3 | pendiente |
| canon_1923 | Flores Back-arc Thrust | 1 | pendiente |
| canon_1934 | Banda Subduction Zone | 4 | pendiente |
| canon_1924 | N Halmahera Transform | 1 | pendiente |

### Tipo B — Estructuras secundarias
| Canonical | Estructura | Feats | merged_geom |
|-----------|-----------|-------|-------------|
| canon_205 | Batui Thrust | 5 | pendiente |
| canon_1925 | WSFB | 1 | pendiente |
| canon_1926 | NSFTB | 1 | pendiente |
| canon_1927 | EWF | 1 | pendiente |
| canon_1928 | Buton Thrust | 2 | pendiente |
| canon_1929 | Hamilton Fault | 1 | pendiente |
| canon_1930 | Tomini Gulf FZ | 2 | pendiente |
| canon_1932 | Selayar FZ | 1 | pendiente |
| canon_1933 | Balantak | 2 | pendiente |
| canon_1934 | West Buru FZ | 1 | pendiente |
| canon_1935 | Pasini Thrust | 1 | pendiente |
| canon_1936 | Lobu-Balolang FZ | 1 | pendiente |

### Tipo C — Slabs mantélicos
| Canonical | Estructura | Feats | merged_geom |
|-----------|-----------|-------|-------------|
| canon_slab_banda | Banda Slab | 2 | pendiente |
| canon_slab_sula | Sula Slab | 1 | pendiente |

### Tipo D — Zonas de régimen (Jibran)
canon_jib_01 a canon_jib_10 — 1 feat c/u — geometría = cluster original ✓

### Tipo H — Unidades geológicas
| Canonical | Estructura | Feats | merged_geom |
|-----------|-----------|-------|-------------|
| canon_eso | East Sulawesi Ophiolite | 4 | **pendiente usuario** |
| canon_bantimala | Bantimala Complex UHP | 0 | **pendiente usuario** |
| canon_mekongga_rumbia | Mekongga-Rumbia blueschist | 1 | pendiente |
| canon_csmb | CSMB / Pompangeo Schist | 1 | pendiente |
| canon_mmc | Malino/Mekongga Complex | 1 | pendiente |
| canon_pmc | Palu Metamorphic Complex | 2 | pendiente |
| canon_terrane_bsm | Banggai-Sula Microcontinent | 3 | pendiente |
| canon_terrane_btb | Buton-Tukang Besi | 3 | pendiente |
| canon_terrane_wsp | West Sulawesi Province | 1 | pendiente |
| canon_nsarc | North Arm Volcanic Arc | 2 | pendiente |
| canon_wsip | WSIP | 2 | pendiente |
| canon_adang | Adang Volcanic Complex | 1 | pendiente |

## MAPA — PAPERS EN DB (2026-05-31)
baillie_2022, socquet_2006, walpersdorf_1998, natawidjaja_2020/2021, lukman_2016,
cipta_2016, greenfield_2021, serhalawan_chen_2024, jibran_2025, di_leo_2012,
cao_2024, yuan_2024, hua_2023, kesumastuti_2025, heryandoko_2024, supendi_2024,
liu_2026, yang_2025, faturrakhman_2024/2025, hussein_2014, isbram_2025, surono_2012,
satyana_ipa/iagi_2011, hikmy_2025, lestari_2021, shih_2026, pratama_2025, jayadi_2023.

Actualizar esta lista al agregar cada paper nuevo a la DB.

## BACKEND — ENDPOINTS DISPONIBLES

Iniciar con: `python -m uvicorn backend.main:app --port 8000` desde `mapa/`
Swagger UI completo: `http://127.0.0.1:8000/api/docs`

| Endpoint | Método | Params clave | Descripción |
|---|---|---|---|
| `/api/earthquakes` | GET | `minMag`=5.5, `maxMag`, `startYear`, `endYear`, `minDepth`, `maxDepth`, `faultTypes`=T,N,S,O, `sources`=cmt,usgs | Catálogo sísmico DB |
| `/api/catalog/live` | GET | `minMag`=5.0, `days`=30 | Eventos recientes USGS FDSN (proxy) |
| `/api/catalog/isc` | GET | `minMag`=4.5, `maxMag`=5.4, `days`=365, `minDepth`, `maxDepth` | Catálogo ISC (proxy) |
| `/api/stations` | GET | — | Estaciones sismológicas BMKG/GEOFON vía IRIS FDSN |
| `/api/volcanoes` | GET | — | Volcanes GVP + PVMBG |
| `/api/slabs/slab2` | GET | — | Contornos Slab2 Hayes 2018 (GeoJSON) |
| `/api/faults/gem` | GET | `faultType` | Fallas GEM filtradas por tipo |
| `/api/gravity/profile` | POST | `{coords:[[lon,lat],...], n_points:100}` | Perfil Bouguer+Free-air desde TIFFs WGM2012 |
| `/api/annotations` | GET/POST/DELETE | — | Anotaciones del usuario persistidas |
| `/api/geodata/features` | GET | `source`, `layerType`, `unmatched` | Features de geo_features |
| `/api/geodata/canonical` | GET | `layerType` | Canonicals estructurales |
| `/api/geodata/canonical-groups` | GET | — | Grupos para selección de merged_geom |
| `/api/geodata/canonical-groups/{id}/resolve` | POST | `chosenId` (query) | Asignar merged_geom al canonical |
| `/api/geodata/features/{id}` | PATCH | `{geometry}` (body) | Actualizar geometría de feature |
| `/api/geodata/matches` | GET | `status`=pending | Match proposals |
| `/api/geodata/matches/run` | POST | `threshold`=0.20 | Ejecutar algoritmo matching |

Actualizar esta tabla al agregar nuevos endpoints.
