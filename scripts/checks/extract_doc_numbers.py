"""
extract_doc_numbers.py
----------------------
Extract all stat-like numbers from PRWP paragraph text and check each
against numbers_manifest.xlsx.

Outputs a report showing:
  COVERED   — found in manifest
  UNCOVERED — in doc but not in manifest (review: add to manifest or ignore)

Pair with check_numbers.py (manifest → doc) for full bi-directional coverage.

Run: python analyses/prwp_2025/scripts/extract_doc_numbers.py
"""
import re
from docx import Document
from _doc_utils import REPO_ROOT, DOCX_PATH, MANIFEST_PATH, get_para_text_accepted, build_doc_paragraphs, load_manifest


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

# Numbers to actively capture
STAT_PATTERNS = [
    # Ranges with percent: "40–46 percent", "11–13%", "4–6%"
    r'(?<!\w)\d[\d.,]*\s*[–\-]\s*\d[\d.,]*\s*(?:percent(?:\s+of\b)?|%)',
    # Approximate / qualified percentages: "~18%", ">75%", "about 18 percent"
    r'(?:~|>|<|≈|about|approximately|around|above|below|over|more than|less than)\s*\d[\d.,]*\s*(?:percent(?:\s+of\b)?|%)',
    # Plain percentages: "6.7 percent", "72.7%"
    r'(?<!\w)\d[\d.,]*\s*(?:percent(?:\s+of\b)?|%)',
    # Labelled counts: "7,574 projects", "8,569 reviews", "59 operations"
    r'\d[\d,]+\s*(?:projects?|reviews?|operations?|ICRRs?|PPARs?)',
    # Percentage points: "25 pp", "+19 percentage points"
    r'[+\-−]?\d[\d.,]*\s*(?:pp\b|percentage points?)',
    # Multipliers: "3.2 times", "3.2×", "3.2-fold"
    r'\d[\d.,]*\s*(?:times\b|×|-fold\b)',
    # Outcome deltas: "0.13 points (3.2%)", "-0.02 points"
    r'[+\-−]?0\.\d+\s*points?\s*(?:\([^)]+\))?',
    # Signed deltas with pts: "+0.13 pts", "−0.02 pts"
    r'[+\-−]\d[\d.,]*\s*pts?\b',
]

STAT_RE = re.compile(
    "|".join(f"(?:{p})" for p in STAT_PATTERNS),
    re.IGNORECASE,
)

# Patterns that, if they span/contain the match position, mean it's not a stat
EXCLUSION_PATTERNS = [
    re.compile(r'\b(?:Table|Figure|Box|Step|Appendix|Chart|Section|Annex)\s*[\w.]+', re.IGNORECASE),
    re.compile(r'\b1[89]\d{2}\b'),                    # years 1800–1999
    re.compile(r'\b20[012]\d\b'),                      # years 2000–2029
    re.compile(r'\b\d{4}\s*[–\-]\s*\d{4}\b'),         # year ranges 1998–2002
    re.compile(r'\b\d{4}\s*[–\-]\s*\d{2}\b'),         # year ranges 2018–22
    re.compile(r'\(\s*[A-Z][^)]*,\s*20\d{2}\s*\)'),   # citations (Author, 2022)
    re.compile(r'\b(?:one|two|three|four|five|six|seven|eight|nine|ten)\b', re.IGNORECASE),
]

# Headings styles to skip (tables in docx are already separate objects)
SKIP_STYLES = {"Heading 1", "Heading 2", "Heading 3", "Heading 4", "Title"}


def is_excluded(match_text: str, para_text: str, match_start: int) -> bool:
    """Return True if this match should be skipped."""
    # Check exclusion patterns against the surrounding context (±60 chars)
    window_start = max(0, match_start - 30)
    window = para_text[window_start: match_start + len(match_text) + 30]

    for pat in EXCLUSION_PATTERNS:
        for m in pat.finditer(window):
            # If the exclusion pattern overlaps the match position within the window
            excl_start = window_start + m.start()
            excl_end = window_start + m.end()
            if excl_start <= match_start + len(match_text) and excl_end >= match_start:
                return True
    return False


def extract_stats(paragraphs: list[str], doc: Document) -> list[dict]:
    """Extract all stat-like matches from non-heading paragraphs."""
    results = []
    for i, (text, para) in enumerate(zip(paragraphs, doc.paragraphs)):
        if not text.strip():
            continue
        if para.style.name in SKIP_STYLES:
            continue

        for m in STAT_RE.finditer(text):
            if is_excluded(m.group(), text, m.start()):
                continue

            # Build a short context string centred on the match
            ctx_start = max(0, m.start() - 40)
            ctx_end = min(len(text), m.end() + 40)
            context = ("…" if ctx_start > 0 else "") + text[ctx_start:ctx_end].strip() + ("…" if ctx_end < len(text) else "")

            results.append({
                "para_idx": i,
                "extracted": m.group().strip(),
                "context": context,
            })
    return results


# ---------------------------------------------------------------------------
# Manifest matching
# ---------------------------------------------------------------------------

def primary_values(s: str) -> set[float]:
    """
    Extract the set of numeric values from a stat string.
    Strips %, commas, ×, pp, pts, leading modifiers before parsing.
    E.g.: "~18%"         → {18.0}
          "40–46%"       → {40.0, 46.0}
          "7,574"        → {7574.0}
          "+25 pp"       → {25.0}
          "0.13 pts"     → {0.13}
          "3.2 times"    → {3.2}
    """
    cleaned = re.sub(r"[%×,]", "", str(s))
    cleaned = re.sub(r"\b(?:percent|pp|pts?|times|fold|projects?|reviews?|operations?|ICRRs?|PPARs?)\b", "", cleaned, flags=re.IGNORECASE)
    nums = re.findall(r"\d+(?:\.\d+)?", cleaned)
    return {float(n) for n in nums if float(n) > 0}


def values_match(a: set[float], b: set[float]) -> bool:
    """True if any value in a is within 0.1% of any value in b."""
    for va in a:
        for vb in b:
            if va == vb:
                return True
            # relative tolerance for large numbers
            if max(va, vb) > 0 and abs(va - vb) / max(va, vb) < 0.001:
                return True
    return False


def match_to_manifest(extracted: str, manifest: list[dict]) -> dict | None:
    """
    Return the best-matching manifest entry by numeric value comparison.
    Uses exact numeric equality (within floating point tolerance), not substring matching.
    """
    ext_vals = primary_values(extracted)
    if not ext_vals:
        return None

    best = None
    best_score = 0  # prefer entries with more values matching

    for entry in manifest:
        stat_vals = primary_values(str(entry["stat"]))
        if not stat_vals:
            continue
        if values_match(ext_vals, stat_vals):
            # Score: number of shared values (prefer more specific match)
            shared = sum(
                1 for ev in ext_vals for sv in stat_vals
                if ev == sv or (max(ev, sv) > 0 and abs(ev - sv) / max(ev, sv) < 0.001)
            )
            if shared > best_score:
                best_score = shared
                best = entry

    return best


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    doc = Document(DOCX_PATH)
    paragraphs = build_doc_paragraphs(doc)
    manifest = load_manifest()

    extracted = extract_stats(paragraphs, doc)
    covered, uncovered = [], []

    for item in extracted:
        match = match_to_manifest(item["extracted"], manifest)
        if match:
            item["manifest_stat"] = str(match["stat"])
            item["table_ref"] = match.get("table_ref") or "—"
            covered.append(item)
        else:
            uncovered.append(item)

    # --- Report ---
    print("=" * 70)
    print("DOC → MANIFEST: extracted stats vs manifest coverage")
    print("=" * 70)
    print(f"\nTotal stat-like matches extracted: {len(extracted)}")
    print(f"  COVERED   (in manifest): {len(covered)}")
    print(f"  UNCOVERED (not in manifest): {len(uncovered)}")

    print("\n" + "─" * 70)
    print("UNCOVERED — review each: add to manifest, or harmless prose number")
    print("─" * 70)

    # Group uncovered by paragraph for readability
    prev_para = None
    for item in uncovered:
        if item["para_idx"] != prev_para:
            print(f"\n  [para {item['para_idx']}]")
            prev_para = item["para_idx"]
        print(f"    {item['extracted']!r:30s}  {item['context'][:65]}")

    print("\n" + "─" * 70)
    print("COVERED — extracted stat → manifest entry")
    print("─" * 70)
    prev_para = None
    for item in covered:
        if item["para_idx"] != prev_para:
            print(f"\n  [para {item['para_idx']}]")
            prev_para = item["para_idx"]
        print(f"    {item['extracted']!r:30s}  → manifest: {item['manifest_stat']}  (table: {item['table_ref']})")


if __name__ == "__main__":
    main()
