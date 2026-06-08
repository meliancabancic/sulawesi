# SKILL: pdf-reading

## Activación
Trigger: "leer el paper", "abrí el PDF", "leé este paper", "qué dice", nombre de un paper del proyecto.

## Paths

PDFs en: `C:\Users\PC\Desktop\Geo\Tectonica\Monografia\Papers\`
Filename exacto → consultar `project_state.json` campo `file` del paper.

## Leer texto con pdfplumber

```python
import pdfplumber
from pathlib import Path

PAPERS = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\Papers")

def read_pdf_text(filename: str, pages: list[int] = None) -> str:
    """pages: lista 0-indexed. None = todas."""
    with pdfplumber.open(PAPERS / filename) as pdf:
        target = [pdf.pages[i] for i in pages] if pages else pdf.pages
        return "\n\n".join(p.extract_text() or "" for p in target)
```

Para papers escaneados sin OCR (ej. `sulawesicentralIJES2002.pdf`): el texto extraído
será vacío o basura — notificar al usuario. No intentar OCR automáticamente.

## Extraer figura específica

Ver `skills/raster-georef.md` sección 1 (PyMuPDF).

## Verificar disponibilidad

```python
import json
from pathlib import Path

state = json.loads(Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\project_state.json")
                   .read_text(encoding="utf-8"))
paper = state["papers"]["nombre_clave"]
pdf_path = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia") / paper["file"]
print(pdf_path.exists(), pdf_path)
```

## Convención de lectura selectiva

- Leer solo las páginas necesarias — no el PDF completo salvo que sea imprescindible.
- Para papers largos: leer introducción + figuras + conclusiones primero.
- Si se necesita una sección específica: buscar por página estimada, no leer todo.
