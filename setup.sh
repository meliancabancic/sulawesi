#!/bin/bash
# setup.sh — Inicialización del proyecto Sulawesi Geotectónica
# Ejecutar una vez desde la raíz del proyecto: bash setup.sh

set -e

echo "=== Sulawesi Geotectónica — Setup ==="
echo ""

# ── 1. Estructura de directorios ──────────────────────────────────────────────
echo "[1/5] Creando estructura de directorios..."
mkdir -p papers
mkdir -p mapa/data/sections
mkdir -p monografia
mkdir -p skills/references
mkdir -p skills/scripts
mkdir -p tmp

echo "      OK"

# ── 2. Dependencias del sistema ───────────────────────────────────────────────
echo "[2/5] Verificando dependencias del sistema..."

check_cmd() {
  if command -v "$1" &>/dev/null; then
    echo "      ✓ $1"
  else
    echo "      ✗ $1 — NO encontrado: $2"
    MISSING=1
  fi
}

MISSING=0
check_cmd "pdfinfo"    "instalar: sudo apt install poppler-utils"
check_cmd "pdftotext"  "instalar: sudo apt install poppler-utils"
check_cmd "pdftoppm"   "instalar: sudo apt install poppler-utils"
check_cmd "pdfimages"  "instalar: sudo apt install poppler-utils"
check_cmd "libreoffice" "instalar: sudo apt install libreoffice"
check_cmd "pandoc"     "instalar: sudo apt install pandoc"
check_cmd "convert"    "instalar: sudo apt install imagemagick"
check_cmd "node"       "instalar: sudo apt install nodejs"
check_cmd "npm"        "instalar: sudo apt install npm"
check_cmd "python3"    "instalar: sudo apt install python3"
check_cmd "pip3"       "instalar: sudo apt install python3-pip"

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo "  ⚠️  Instalar dependencias faltantes antes de continuar."
  echo "  Comando rápido (Ubuntu/Debian):"
  echo "  sudo apt update && sudo apt install -y poppler-utils libreoffice pandoc imagemagick nodejs npm python3 python3-pip"
  echo ""
fi

# ── 3. Dependencias Python ────────────────────────────────────────────────────
echo "[3/5] Instalando dependencias Python..."

pip3 install --quiet \
  pypdf \
  pdfplumber \
  pyproj \
  pandas \
  python-docx \
  && echo "      pypdf, pdfplumber, pyproj, pandas, python-docx — OK" \
  || echo "      ⚠️  Error instalando dependencias Python — correr manualmente"

# ── 4. Dependencias Node.js ───────────────────────────────────────────────────
echo "[4/5] Instalando dependencias Node.js..."

npm install --silent docx \
  && echo "      docx — OK" \
  || echo "      ⚠️  Error instalando docx — correr: npm install docx"

# ── 5. Scripts de utilidad para docx ─────────────────────────────────────────
echo "[5/5] Creando scripts de utilidad..."

cat > skills/scripts/unpack.py << 'PYEOF'
#!/usr/bin/env python3
"""Unpack .docx to directory for XML editing."""
import zipfile, sys, os, shutil
from pathlib import Path

def unpack(docx_path, out_dir):
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    with zipfile.ZipFile(docx_path) as z:
        z.extractall(out)
    print(f"Unpacked {docx_path} → {out_dir}/")

if __name__ == "__main__":
    unpack(sys.argv[1], sys.argv[2])
PYEOF

cat > skills/scripts/pack.py << 'PYEOF'
#!/usr/bin/env python3
"""Repack directory to .docx."""
import zipfile, sys, os
from pathlib import Path

def pack(src_dir, out_path, original=None):
    src = Path(src_dir)
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in src.rglob('*'):
            if f.is_file():
                z.write(f, f.relative_to(src))
    print(f"Packed {src_dir} → {out_path}")

if __name__ == "__main__":
    original = sys.argv[4] if len(sys.argv) > 4 else None
    pack(sys.argv[1], sys.argv[2], original)
PYEOF

cat > skills/scripts/validate.py << 'PYEOF'
#!/usr/bin/env python3
"""Basic .docx validation using python-docx."""
import sys
try:
    from docx import Document
    doc = Document(sys.argv[1])
    print(f"Valid: {len(doc.paragraphs)} paragraphs, {len(doc.sections)} sections")
except Exception as e:
    print(f"Invalid: {e}")
    sys.exit(1)
PYEOF

chmod +x skills/scripts/*.py
echo "      OK"

# ── Resumen ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Setup completo ==="
echo ""
echo "Próximos pasos:"
echo "  1. Copiar los PDFs de papers a papers/"
echo "  2. Copiar los skills a skills/ (ver MIGRATION_CHECKLIST.md)"
echo "  3. Abrir Claude Code en este directorio: claude"
echo ""
echo "Estructura lista:"
find . -type d | grep -v node_modules | grep -v __pycache__ | sort
