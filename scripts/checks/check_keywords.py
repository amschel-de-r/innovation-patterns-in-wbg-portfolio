"""
check_keywords.py
-----------------
Compare Appendix B of the PRWP working draft against the canonical keyword JSON files.

Outputs:
  - Keywords in JSON but missing from Appendix B
  - Keywords in Appendix B but missing from JSON

Run: python analyses/prwp_2025/scripts/check_keywords.py
"""
import json
import re
from docx import Document
from _doc_utils import REPO_ROOT, DOCX_PATH

KW_DIR = REPO_ROOT / "data" / "reference" / "keywords"
OLD_KW_DIR = REPO_ROOT / "data" / "reference" / "old_keywords"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def flatten_keywords(data: dict | list) -> set[str]:
    """Recursively extract all leaf string values from a JSON keyword structure."""
    result = set()
    if isinstance(data, str):
        result.add(data.strip().lower())
    elif isinstance(data, list):
        for item in data:
            result |= flatten_keywords(item)
    elif isinstance(data, dict):
        for v in data.values():
            result |= flatten_keywords(v)
    return result


def load_all_json_keywords() -> dict[str, set[str]]:
    """Load every .json file in KW_DIR, return {filename: flat set of keywords}."""
    result = {}
    for path in sorted(KW_DIR.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        result[path.name] = flatten_keywords(data)
    return result


def extract_appendix_b(doc: Document) -> str:
    """Return the full text of Appendix B as a single lowercase string."""
    paras = list(doc.paragraphs)
    in_b = False
    parts = []
    for p in paras:
        if "Appendix B" in p.text and "Heading" in p.style.name:
            in_b = True
            continue
        if in_b and "Heading 1" in p.style.name and p.text.strip():
            break  # next H1 = end of Appendix B
        if in_b and p.text.strip():
            parts.append(p.text.strip())
    return "\n".join(parts).lower()


def tokenize_appendix(text: str) -> set[str]:
    """
    Extract individual keyword tokens from Appendix B text.
    Splits on commas, semicolons, and line boundaries.
    Strips punctuation artifacts.
    """
    # Remove common prose phrases that aren't keywords
    text = re.sub(r"the keyword list includes.*?\.", "", text)
    tokens = re.split(r"[,;\n]+", text)
    result = set()
    for t in tokens:
        t = t.strip().strip(".")
        if 2 <= len(t) <= 60 and not t.startswith("appendix"):
            result.add(t)
    return result



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    doc = Document(DOCX_PATH)
    appendix_b_text = extract_appendix_b(doc)
    appendix_tokens = tokenize_appendix(appendix_b_text)
    json_keywords = load_all_json_keywords()

    # Combine all JSON keywords into one flat set
    all_json_kws = set()
    for kws in json_keywords.values():
        all_json_kws |= kws

    print("=" * 60)
    print("KEYWORD CHECK: JSON vs Appendix B")
    print("=" * 60)
    print(f"\nTotal unique keywords in JSON files: {len(all_json_kws)}")
    print(f"Total tokens extracted from Appendix B: {len(appendix_tokens)}")

    # JSON keywords NOT found anywhere in Appendix B text
    missing_from_doc = set()
    for kw in sorted(all_json_kws):
        if kw not in appendix_b_text:
            missing_from_doc.add(kw)

    # Appendix tokens NOT found in any JSON file
    # (approximate — tokens are fuzzier than JSON keys)
    missing_from_json = set()
    for token in sorted(appendix_tokens):
        if not any(token in kw or kw in token for kw in all_json_kws):
            missing_from_json.add(token)

    print(f"\n--- JSON keywords absent from Appendix B text ({len(missing_from_doc)}) ---")
    for kw in sorted(missing_from_doc):
        print(f"  MISSING: {kw}")

    print(f"\n--- Appendix B tokens not matched in any JSON ({len(missing_from_json)}) ---")
    print("  (may include prose — review manually)")
    for token in sorted(missing_from_json):
        print(f"  UNMATCHED: {token}")

    # Per-file breakdown
    print("\n--- Per JSON file: keywords absent from Appendix B ---")
    for fname, kws in sorted(json_keywords.items()):
        absent = sorted(kw for kw in kws if kw not in appendix_b_text)
        if absent:
            print(f"\n  [{fname}] {len(absent)} missing:")
            for kw in absent:
                print(f"    {kw}")
        else:
            print(f"\n  [{fname}] all present ✓")


if __name__ == "__main__":
    main()
