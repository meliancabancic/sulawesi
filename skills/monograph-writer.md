# SKILL: monograph-writer

## Activación
Trigger: "escribí la sección", "redactá", "armá la monografía", "draft de S1", nombre de sección + "escribir/redactar".

## Antes de redactar

1. Leer `project_state.json` → verificar qué papers están `"digitalizado"` para la sección
2. Leer `mapa_plan.json` → sección correspondiente → `cobertura_actual` y `nota`
3. Leer los GeoJSON relevantes en `mapa/fuentes/` → `metadata.comprehension_summary` y `metadata.bibliography`
4. Verificar `paginas_acumuladas` — no superar 30 pp. totales

## Especificaciones

- Estilo: prosa técnica fluida estilo journal internacional en **español**
- Fuente destino: Times New Roman 12pt, 1.5 interlineado (se aplica en docx.md)
- Sin resumen/abstract
- Sin bullets en cuerpo del texto
- Negritas solo para términos técnicos en primera aparición
- Citas: `(Autor et al., año)` inline; lista completa solo al final del texto principal
- Figuras: solo de papers citados — caption: `Figura N. Título. Fuente: Autor et al., año, p. X.`
- Tablas: solo para comparaciones entre autores o datos tabulares reales

## Estructura fija y extensión objetivo

| Sección | Título | Páginas objetivo |
|---------|--------|-----------------|
| 1 | Descripción general del área | 3-4 |
| 2 | Distribución de la sismicidad | 3-4 |
| 3 | Estructura del manto | 3-4 |
| 4 | Campo gravitatorio | 2-3 |
| 5 | Flujo calórico | 2-3 |
| 6 | Estructura [a definir] | 3-4 |
| 7 | Asociaciones petrotectónicas | 3-4 |
| 8 | Metamorfismo | 2-3 |
| Referencias | — | ~2 |
| **Total** | | **25 pp. objetivo / 30 pp. máx.** |

## Protocolo por sección

### S1 — Descripción general
Cubrir: ubicación, morfología (4 brazos), marco de placas (IA, Filipinas, Euroasiática),
historia de ensamblaje (Oligoceno-Mioceno), estructuras principales (PKF, NST, Matano,
Sorong, MST, ESO), contexto geodinámico regional.
Papers base: Hall (2011/2015), Socquet 2006, Baillie 2022, Bird 2003.

### S2 — Sismicidad
Cubrir: distribución epicentral (GCMT + USGS), profundidades (superficial/intermedia/profunda),
mecanismos focales (regímenes por zona — Jibran 2025), gap sísmico NST, ruptura PKF 2018
(Natawidjaja 2020/2021), Batui Thrust (Isbram 2025 pendiente).
Vincular distribución en profundidad con geometría de slabs (Slab2).

### S3 — Estructura del manto
Cubrir: losas subductadas (Mar de Célebes, Sangihe, Halmahera, Banda, Sula),
anisotropía sísmica SKS (Di Leo 2012, Cao 2024, Yuan 2024), flujo toroidal/corner flow,
tomografía P y S (Hua 2023, Kesumastuti 2025, Liu 2026, Supendi 2024),
espesor cortical (Yang 2025, Heryandoko 2024).

### S4 — Campo gravitatorio
Cubrir: WGM2012 (Bouguer + Aire Libre), anomalías regionales, correlación con
estructura cortical y tectónica activa (NST, PKF, MST, cuencas).
Si Shih 2026 digitalizado: incorporar datos de gravimetría aérea.

### S5 — Flujo calórico
Cubrir: datos IHFC/WorldHeatFlow (escasos en Sulawesi), Curie Point Depth (Pratama 2025),
volcanes activos (clasificación PVMBG A/B/C), campos geotérmicos (Lahendong, Leilem),
manifestaciones superficiales. Vincular con subducción NST y PKF.

### S7 — Asociaciones petrotectónicas
Cubrir: ESO (123 Ma, obducción sobre Banggai-Sula), WSIP (Paleógeno), arco Norte activo,
Bantimala UHP (119 Ma), complejos PMC/MMC, microcontinente Banggai-Sula (colisión ~5-6 Ma),
MSCC. Organizar por tipo: ofiolita → arco → metamórfico → terreno continental → acreción.

### S8 — Metamorfismo
Cubrir: Bantimala UHP (27-28.5 kbar / 615-640°C / 119 Ma), trayectorias P-T,
facies en CSMB/PMC/MMC (greenschist a anfibolita). Reconocer gap bibliográfico.
Extensión reducida (~2-3 pp.) dado el corpus disponible.

## Formato de salida

Entregar el texto como bloque de prosa listo para copiar al .docx.
Marcar figuras entre `[FIGURA N: descripción — de paper X, fig. Y]` para inserción posterior.
Al terminar cada sección: actualizar `project_state.json` → `monografia.secciones.SN.status = "draft"`,
`paginas` (estimado), `draft_file`.
