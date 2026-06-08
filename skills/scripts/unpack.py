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
