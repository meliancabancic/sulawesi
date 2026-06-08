# SKILL: bibliography-compiler

## Activación
Trigger: "compilá la bibliografía", "generá las referencias", "qué papers van adjuntos", "lista de referencias", "referencias APA".

## Fuente de datos

Los metadatos bibliográficos de cada paper están en dos lugares:
1. `project_state.json` → campo `file`, `db_source`, `sections_relevant` por paper
2. `metadata.bibliography` de cada GeoJSON en `mapa/fuentes/` → cita APA completa, DOI, journal

Para compilar la bibliografía completa del proyecto, leer ambas fuentes y unificar.

## Formato APA (usado en la monografía)

```
Apellido, I., & Apellido2, I. (Año). Título del artículo. Nombre de la Revista, 
Volumen(Número), página_inicial–página_final. https://doi.org/XXXXX
```

Reglas:
- Hasta 20 autores: listar todos. Más de 20: primeros 19, ..., último.
- Cursiva en nombre de la revista y volumen.
- DOI como URL: `https://doi.org/XXXXX`
- Preprints: agregar `[Preprint]` antes del DOI. Ej: Pratama et al. (2025) → SSRN 6478359.
- Datasets: `[Dataset]` + URL de descarga.
- Sin numeración — ordenar alfabéticamente por primer autor.

## Papers del proyecto por sección

Leer `project_state.json` y filtrar por `sections_relevant` para saber qué papers
citar en cada sección de la monografía.

```python
import json
from pathlib import Path
from collections import defaultdict

state = json.loads(Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\project_state.json")
                   .read_text(encoding="utf-8"))

by_section = defaultdict(list)
for key, p in state["papers"].items():
    for s in p.get("sections_relevant", []):
        by_section[s].append(key)

for s in sorted(by_section):
    print(f"S{s}: {by_section[s]}")
```

## Papers adjuntos al PDF final

Los papers citados se adjuntan al final del PDF de la monografía.
Lista candidata → todos los papers con `cited_in_monografia: true` en `project_state.json`.
Actualizar ese campo al redactar cada sección.

El archivo de control: `monografia/papers_to_append.json` (lista de paths a los PDFs a anexar).
