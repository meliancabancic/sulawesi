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
