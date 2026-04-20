# HR-02 — Innovation Dictionary Validation

**Methodology step**: Step 2 — Develop an innovation keyword dictionary
**Corresponding prompts**: [step_02_dictionary.md](../prompts/step_02_dictionary.md) (Prompts 2.1, 2.2)
**Reviewer qualifications**: See [reviewers.md](../reviewers.md)

---

## Purpose

Validate and refine the combined LLM-generated keyword list through two sequential steps:

1. **Author review** — remove terms that are clearly irrelevant, ambiguous, or overly generic (words used primarily in a non-innovation sense within WBG documentation). Goal: a conservative, face-valid dictionary.
2. **Notebook-based refinement** — use Python notebooks to inspect matched text snippets, identify ambiguous matches in context, and surface plural/morphological variants via relaxed regex. Goal: improve precision and coverage without expanding the dictionary arbitrarily.

## Reviewers

- N: 2 (paper authors)
- Blinded: No (authors reviewed the list they had assembled)

## Materials provided to reviewers

- Combined keyword list from Prompts 2.1 and 2.2 (ChatGPT + DeepSeek outputs, duplicates removed)
- Operational definition of "innovation" as used in this analysis
- Verbal guidance consistent with the Purpose above: remove overly ambiguous or generic terms; retain only those with face validity for capturing innovation in WBG project evaluations. No separate written guidance document was prepared; reviewers' institutional familiarity with WBG operations and the IEG dataset substituted for a formal codebook.

## Decision rules

A term was **removed** if it met any of the following:
- Clearly irrelevant to innovation in the WBG project evaluation context
- Ambiguous (used in both innovation and non-innovation senses with similar frequency)
- Overly generic (e.g., common project management language not specific to innovative practice)

A term was **retained** if it had face validity against known innovation practices in international development.

**Addition rule**: No terms were added to the dictionary without explicit agreement by both reviewers.

## Disagreement resolution

Discussion to consensus between the two author-reviewers. No formal third reviewer or adjudication rule.

## Outcome

### Step 1 — Author review

Retained list archived at: `data/reference/old_keywords/innovation_keywords.json`

### Step 2 — Notebook-based refinement

| Change | Count |
|--------|-------|
| Terms entering step 2 | 152 |
| Variants / plurals added | +13 |
| Terms removed for ambiguity | 0 |
| Final dictionary | 165 |

Tool: Python notebook — `notebooks/match_method_sensitivity.ipynb` (see "Baseline and Alternative Runs" and "Other Dictionaries" sections; the `innovation_substring` vs baseline comparison surfaces terms gained by substring matching, used to identify candidate variants/plurals)

Final dictionary: `data/reference/keywords/innovation_keywords.json`
