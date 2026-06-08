# SKILL: pdf

## Activación
Trigger: "compilar el PDF", "merge PDF", "adjuntar papers", "generar el PDF final", "exportar a PDF".

## Paths

```
monografia/monografia_sulawesi.docx        ← fuente
monografia/monografia_sulawesi_FINAL.pdf   ← salida final
monografia/papers_to_append.json           ← lista de PDFs a anexar
Papers/                                    ← PDFs de papers para anexar
```

## Flujo de compilación final

```
monografia_sulawesi.docx
    ↓ convertir a PDF
monografia_sulawesi.pdf
    ↓ merge con papers citados
monografia_sulawesi_FINAL.pdf
```

## Convertir .docx → .pdf

```python
import subprocess
from pathlib import Path

MONO = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\monografia")

# LibreOffice headless (requiere LibreOffice instalado)
subprocess.run([
    "soffice", "--headless", "--convert-to", "pdf",
    "--outdir", str(MONO),
    str(MONO / "monografia_sulawesi.docx")
], check=True)
```

## Merge PDFs con pypdf

```python
from pypdf import PdfWriter, PdfReader
import json
from pathlib import Path

BASE = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia")
MONO = BASE / "monografia"
PAPERS = BASE / "Papers"

writer = PdfWriter()

# 1. Agregar monografía
writer.append(str(MONO / "monografia_sulawesi.pdf"))

# 2. Agregar papers citados
to_append = json.loads((MONO / "papers_to_append.json").read_text(encoding="utf-8"))
for pdf_rel_path in to_append:
    pdf_path = BASE / pdf_rel_path
    if pdf_path.exists():
        writer.append(str(pdf_path))
    else:
        print(f"FALTA: {pdf_path}")

with open(MONO / "monografia_sulawesi_FINAL.pdf", "wb") as f:
    writer.write(f)

print(f"Final: {len(writer.pages)} páginas")
```

## Actualizar `papers_to_append.json`

```python
import json
from pathlib import Path

state = json.loads(Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\project_state.json")
                   .read_text(encoding="utf-8"))

to_append = [
    p["file"] for p in state["papers"].values()
    if p.get("cited_in_monografia") and Path(
        r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia", p["file"]
    ).exists()
]

Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\monografia\papers_to_append.json")\
    .write_text(json.dumps(to_append, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(to_append)} papers a adjuntar")
```
