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
