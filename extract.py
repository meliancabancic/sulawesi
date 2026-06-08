#!/usr/bin/env python3
"""
extract.py — Geological Paper to GeoJSON Extractor
Uses Claude API (claude-sonnet-4-20250514) to extract geological data
from scientific papers and generate GeoJSON files.

Usage:
    python extract.py paper.pdf
    python extract.py paper.pdf --output my_output.geojson
    python extract.py paper.pdf --auto   # skip confirmation

Requirements:
    pip install anthropic
    Set ANTHROPIC_API_KEY environment variable
"""

import sys
import os
import json
import base64
import argparse
import re
from pathlib import Path
from datetime import date

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed.")
    print("Run: pip install anthropic")
    sys.exit(1)

# ─── SYSTEM PROMPT ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a geological data extraction specialist. Your task is to extract
structured geological data from scientific papers and output valid GeoJSON.

EXTRACTION PROTOCOL:

1. BUILD APA CITATION — Extract complete APA citation from the paper:
   Author, A. A., & Author, B. B. (Year). Title. Journal, Volume(Issue), pages. https://doi.org/XXXXX

2. IDENTIFY DATA CATEGORIES present in the paper:
   - fault: fault traces, slip rates, kinematics
   - earthquake: seismic catalog, focal mechanisms, Mw
   - structure: core complexes, ophiolites, metamorphic belts, anticlines
   - hazard_zone: seismic gaps, high-risk areas
   - volcano: active/inactive volcanoes
   - gps_vector: GPS/GNSS vectors, block velocities
   - tomography_profile: tomographic profiles, velocity anomalies
   - anisotropy: SKS fast axes, delay times, splitting parameters
   - geophysical_point: other geophysical point data (uplift rates, etc.)

3. EXTRACT COORDINATES for each structure:
   - Use explicit lat/lon if given in the paper
   - Georeference from figures with lat/lon grid
   - Use prior knowledge for well-known structures (PKF, NST, etc.)
   - Mark uncertainty: "accurate" | "approximate" | "inferred"

4. BUILD GEOJSON — Output a valid GeoJSON FeatureCollection.

MANDATORY PROPERTIES for EVERY feature:
{
  "id": "{category}_{first_author_lastname}_{year}_{nn}",
  "name": "Short tooltip name, max ~50 chars, pattern: 'Main name — descriptor'",
  "full_name": "Complete descriptive name for the map panel",
  "category": "fault|earthquake|structure|hazard_zone|volcano|gps_vector|anisotropy|geophysical_point",
  "source_apa": "Full APA citation",
  "source_short": "Author et al. (Year)",
  "paper_finding": "Specific finding from the paper about this structure",
  "coord_quality": "accurate|approximate|inferred",
  "extraction_notes": "How coordinates were obtained"
}

GEOMETRY TYPES:
- fault, tomography_profile → LineString
- hazard_zone, areal structure → Polygon
- earthquake, volcano, gps_vector, anisotropy, geophysical_point → Point
- linear structure → LineString

NAME CONVENTION (MANDATORY):
- name: short tooltip, max 50 chars → "Batui Thrust — activa NE-SW"
- full_name: complete for side panel → "Batui Thrust — active NE-SW thrust fault, ESO/Banggai-Sula boundary"
- Fault: "Fault Name — kinematic type"
- Earthquake: "Location Year — Mw X.X type"
- Hazard: "Zone Name — hazard type"
- Geophysical: "Parameter — location (value)"

OUTPUT FORMAT — Return ONLY valid JSON, no markdown, no preamble:
{
  "type": "FeatureCollection",
  "metadata": {
    "source_paper": "Full APA citation",
    "extraction_date": "YYYY-MM-DD",
    "extractor": "extract.py + Claude claude-sonnet-4-20250514",
    "region": "Region name",
    "coordinate_system": "EPSG:4326",
    "categories_present": ["list", "of", "categories"]
  },
  "bibliography": {
    "key": {
      "apa": "Full APA",
      "short": "Author et al. (Year)",
      "journal": "Journal name",
      "year": YYYY,
      "doi": "DOI",
      "topic": "Main topic",
      "region": "Region"
    }
  },
  "features": [ ... ]
}"""

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def print_separator(char="─", width=60):
    print(char * width)

def print_header(text):
    print_separator("═")
    print(f"  {text}")
    print_separator("═")

def print_section(text):
    print(f"\n{'─'*40}")
    print(f"  {text}")
    print(f"{'─'*40}")

def encode_pdf(pdf_path):
    """Encode PDF to base64."""
    with open(pdf_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def clean_json_response(text):
    """Strip markdown fences if present."""
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()

def validate_geojson(data):
    """Basic GeoJSON validation."""
    errors = []
    if data.get("type") != "FeatureCollection":
        errors.append("Missing 'type: FeatureCollection'")
    features = data.get("features", [])
    if not features:
        errors.append("No features extracted")
    for i, feat in enumerate(features):
        props = feat.get("properties", {})
        for field in ["id", "name", "full_name", "category", "source_apa", "source_short"]:
            if not props.get(field):
                errors.append(f"Feature {i}: missing '{field}'")
    return errors

# ─── EXTRACTION ───────────────────────────────────────────────────────────────

def extract_from_pdf(pdf_path, auto=False):
    """Main extraction function."""

    print_header("GEOLOGICAL PAPER EXTRACTOR")
    print(f"  Input:  {pdf_path}")
    print(f"  Model:  claude-sonnet-4-20250514")
    print(f"  Mode:   {'automatic' if auto else 'semi-automatic'}")

    # Init client
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: set ANTHROPIC_API_KEY=your_key_here  (Windows)")
        print("          or: export ANTHROPIC_API_KEY=your_key_here  (Linux/Mac)")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Encode PDF
    print("\n[1/4] Reading PDF...")
    pdf_b64 = encode_pdf(pdf_path)
    print(f"      Size: {len(pdf_b64) // 1024} KB (base64)")

    # Call Claude API
    print("\n[2/4] Sending to Claude API for extraction...")
    print("      This may take 30-60 seconds...")

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""Extract all geological data from this paper and return a valid GeoJSON FeatureCollection.

Today's date: {date.today().isoformat()}

Requirements:
1. Build complete APA citation from the paper header
2. Extract ALL geological structures, faults, earthquakes, GPS data, 
   geophysical measurements, and hazard zones mentioned
3. Every feature MUST have: id, name, full_name, category, source_apa, 
   source_short, paper_finding, coord_quality, extraction_notes
4. name = short tooltip (max 50 chars), pattern "Main — descriptor"
5. full_name = complete descriptive name for side panel
6. Coordinates in [longitude, latitude] order (EPSG:4326)
7. Include bibliography block

Return ONLY valid JSON. No markdown. No explanation."""
                        }
                    ]
                }
            ]
        )
    except anthropic.APIError as e:
        print(f"\nAPI ERROR: {e}")
        sys.exit(1)

    print("      Done.")

    # Parse response
    print("\n[3/4] Parsing response...")
    raw_text = response.content[0].text
    clean_text = clean_json_response(raw_text)

    try:
        geojson_data = json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"\nERROR: Could not parse JSON response: {e}")
        print("\nRaw response (first 500 chars):")
        print(raw_text[:500])
        # Save raw for debugging
        debug_path = pdf_path.stem + "_debug.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(raw_text)
        print(f"\nFull response saved to: {debug_path}")
        sys.exit(1)

    # Validate
    errors = validate_geojson(geojson_data)
    if errors:
        print(f"  Warnings:")
        for e in errors:
            print(f"    ⚠ {e}")

    # ─── SHOW SUMMARY ─────────────────────────────────────────────────────────
    print_section("EXTRACTION SUMMARY")

    metadata = geojson_data.get("metadata", {})
    features = geojson_data.get("features", [])

    print(f"  Paper:    {metadata.get('source_paper', 'Unknown')[:80]}...")
    print(f"  Region:   {metadata.get('region', 'Unknown')}")
    print(f"  Features: {len(features)}")

    # Count by category
    categories = {}
    for feat in features:
        cat = feat.get("properties", {}).get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\n  By category:")
    for cat, count in sorted(categories.items()):
        print(f"    {cat:25s} {count} feature(s)")

    print(f"\n  Features extracted:")
    print_separator()
    for i, feat in enumerate(features):
        props = feat.get("properties", {})
        geom_type = feat.get("geometry", {}).get("type", "?")
        coords = feat.get("geometry", {}).get("coordinates", [])
        coord_q = props.get("coord_quality", "?")

        # Coordinate preview
        if geom_type == "Point":
            coord_str = f"[{coords[0]:.3f}, {coords[1]:.3f}]"
        elif geom_type == "LineString" and coords:
            coord_str = f"{len(coords)} pts, start [{coords[0][0]:.3f},{coords[0][1]:.3f}]"
        elif geom_type == "Polygon" and coords:
            coord_str = f"{len(coords[0])} pts polygon"
        else:
            coord_str = "?"

        print(f"  {i+1:2d}. [{props.get('category','?'):15s}] {props.get('name','?')[:45]}")
        print(f"      ID: {props.get('id','?')}")
        print(f"      Geom: {geom_type} | Coords: {coord_str} | Quality: {coord_q}")
        print(f"      Finding: {props.get('paper_finding','?')[:80]}...")
        print()

    print_separator()

    # ─── CONFIRMATION ─────────────────────────────────────────────────────────
    if not auto:
        print("\n[4/4] Review the extraction above.")
        print("      Options:")
        print("        [y] Save GeoJSON")
        print("        [n] Cancel")
        print("        [e] Edit raw JSON before saving")

        while True:
            choice = input("\n  Your choice [y/n/e]: ").strip().lower()

            if choice == "n":
                print("\n  Cancelled. No file saved.")
                sys.exit(0)

            elif choice == "e":
                # Save temp file and open editor
                import tempfile
                import subprocess
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False, encoding="utf-8"
                ) as tmp:
                    json.dump(geojson_data, tmp, ensure_ascii=False, indent=2)
                    tmp_path = tmp.name

                editor = os.environ.get("EDITOR", "notepad" if os.name == "nt" else "nano")
                print(f"\n  Opening {editor}... Save and close to continue.")
                subprocess.call([editor, tmp_path])

                with open(tmp_path, encoding="utf-8") as f:
                    try:
                        geojson_data = json.load(f)
                        print("  JSON loaded successfully after edit.")
                    except json.JSONDecodeError as e:
                        print(f"  ERROR in edited JSON: {e}")
                        print("  Saving original extraction instead.")
                os.unlink(tmp_path)
                break

            elif choice == "y":
                break
            else:
                print("  Please enter y, n, or e.")

    # ─── SAVE ─────────────────────────────────────────────────────────────────
    return geojson_data

def save_geojson(data, output_path):
    """Save GeoJSON with formatting."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size_kb = os.path.getsize(output_path) / 1024
    print(f"\n  ✓ Saved: {output_path} ({size_kb:.1f} KB)")
    print(f"    Features: {len(data.get('features', []))}")

    # Also update/create bibliography.json
    bib_path = output_path.parent / "bibliography.json"
    new_bib = data.get("bibliography", {})
    if new_bib:
        if bib_path.exists():
            with open(bib_path, encoding="utf-8") as f:
                existing_bib = json.load(f)
            existing_bib.update(new_bib)
            merged_bib = existing_bib
        else:
            merged_bib = new_bib

        with open(bib_path, "w", encoding="utf-8") as f:
            json.dump(merged_bib, f, ensure_ascii=False, indent=2)
        print(f"    Bibliography updated: {bib_path}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def build_output_path(pdf_path, custom_output=None):
    """Generate output filename from PDF name."""
    if custom_output:
        return Path(custom_output)
    stem = pdf_path.stem.lower()
    stem = re.sub(r'[^\w]+', '_', stem)
    stem = re.sub(r'_+', '_', stem).strip('_')
    return pdf_path.parent / f"{stem}_extracted.geojson"

def main():
    parser = argparse.ArgumentParser(
        description="Extract geological data from scientific papers to GeoJSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract.py paper.pdf
  python extract.py paper.pdf --output my_faults.geojson
  python extract.py paper.pdf --auto
  python extract.py paper.pdf --output data/serhalawan_2024.geojson

Environment:
  ANTHROPIC_API_KEY   Your Anthropic API key (required)
        """
    )
    parser.add_argument("pdf", help="Path to the PDF paper")
    parser.add_argument("--output", "-o", help="Output GeoJSON path (default: auto-generated)")
    parser.add_argument("--auto", "-a", action="store_true",
                        help="Skip confirmation, save automatically")

    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)
    if pdf_path.suffix.lower() != ".pdf":
        print(f"WARNING: File does not have .pdf extension: {pdf_path}")

    output_path = build_output_path(pdf_path, args.output)

    # Run extraction
    geojson_data = extract_from_pdf(pdf_path, auto=args.auto)

    # Save
    save_geojson(geojson_data, output_path)

    print_separator("═")
    print("  DONE")
    print_separator("═")

if __name__ == "__main__":
    main()
