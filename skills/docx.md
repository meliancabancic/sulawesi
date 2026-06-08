# SKILL: docx

## Activación
Trigger: "crear el docx", "editar el docx", "agregar sección al documento", "escribir en el docx", "formatear".

## Paths

```
monografia/monografia_sulawesi.docx   ← documento principal
monografia/monografia_sulawesi_FINAL.pdf
monografia/papers_to_append.json
skills/scripts/unpack.py              ← desempacar .docx a directorio XML
skills/scripts/pack.py                ← reempacar directorio → .docx
skills/scripts/validate.py            ← validar .docx
```

## Especificaciones del documento

- **Fuente**: Times New Roman 12pt cuerpo, 14pt títulos de sección
- **Márgenes**: 2.5 cm todos los lados
- **Interlineado**: 1.5
- **Citas**: APA inline — `(Autor et al., año)` en el texto; lista completa al final
- **Extensión**: objetivo 25 pp., máximo absoluto 30 pp. (sin contar papers adjuntos)
- **Sin abstract/resumen**
- **Idioma**: español (texto) / inglés (términos técnicos, citas textuales, figuras)

## Crear/editar con python-docx

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path

DOCX = Path(r"C:\Users\PC\Desktop\Geo\Tectonica\Monografia\monografia\monografia_sulawesi.docx")

# Abrir existente o crear nuevo
doc = Document(DOCX) if DOCX.exists() else Document()

# Agregar sección
doc.add_heading("1. Descripción general del área", level=1)
p = doc.add_paragraph("Texto de la sección...")
p.style.font.name = "Times New Roman"
p.style.font.size = Pt(12)

doc.save(DOCX)
```

## Edición XML directa (para formato complejo)

```bash
python skills/scripts/unpack.py monografia/monografia_sulawesi.docx tmp/docx_unpacked/
# editar archivos XML en tmp/docx_unpacked/word/document.xml
python skills/scripts/pack.py tmp/docx_unpacked/ monografia/monografia_sulawesi.docx
python skills/scripts/validate.py monografia/monografia_sulawesi.docx
```

## Figuras

Formato de caption obligatorio:
```
Figura N. Título descriptivo de la figura. Fuente: Autor et al., año, p. X.
```
Insertar como imagen inline, ancho máximo 14 cm, centrada.
Solo figuras de papers citados — no generar figuras propias.

## Estructura de secciones (índice fijo)

```
1. Descripción general del área
2. Distribución de la sismicidad
3. Estructura del manto
4. Campo gravitatorio
5. Flujo calórico
6. Estructura [enfoque a definir]
7. Asociaciones petrotectónicas
8. Metamorfismo
Referencias
```
