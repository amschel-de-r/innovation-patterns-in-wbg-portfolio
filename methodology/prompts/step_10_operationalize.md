# Step 10 — Operationalize Each Hypothesis: AI Prompts

**Methodology step**: Step 10 — Operationalize each hypothesis

**Purpose**: For each retained hypothesis from Step 9, define measurable indicators and generate keyword expansions (pilot/scale lexicon, IFC/PCM lexicon, technology markers) to enable consistent text mining across hypotheses.

**Human review**: Not formalized as a coded review task. Author judgment applied in curating and structuring the generated keyword lists into the final lexicon files.

### Output handling
LLM-generated keyword lists were reviewed and curated by the authors. Final lexicons were structured into JSON files under `data/reference/keywords/`:
- `pilot_scale_keywords.json` — pilot and scale-up terminology
- `ifc_keywords.json` — IFC collaboration references (case-sensitive matching)
- `pcm_keywords.json` — participatory/community-driven methodology references
- `top_models_keywords.json` — innovation model keywords (see also Step 15)

### Models
- **Model A**: ChatGPT (GPT-4o) — approx. June–August 2025

---

<!-- NOTE: Sessions shown here are representative. Equivalent keyword-generation sessions were conducted for each retained hypothesis and lexicon file; not all sessions are individually documented. -->

## Session 10.1 — Pilot and scale-up lexicon

### User prompt
> Generate 5-10 concise tagging keywords for each of two groups: (1) pilot / trial terms — indicating that an approach was introduced as a pilot, prototype, or trial; (2) scale-up / replication terms — indicating that an approach was scaled up, replicated, or mainstreamed. Aim for single-word (or tight compound-word) tags, not descriptive phrases or examples. Think lexical scanning.

### LLM output

Group 1 — Pilot / trial:
1. Pilot
2. Prototype
3. Trial
4. Demonstration
5. Proof-of-concept
6. Experimental
7. Small-scale

Group 2 — Scale-up / replication:
1. Scale
2. Scaling
3. Scaled-up
4. Replication
5. Replicate
6. Mainstream
7. Dissemination

### Output handling
Keywords were reviewed by the authors and structured into `data/reference/keywords/pilot_scale_keywords.json`. Generic terms without sufficient specificity (e.g., "test", "experiment") were excluded. The final dictionary preserves morphological variants for robust substring matching.
