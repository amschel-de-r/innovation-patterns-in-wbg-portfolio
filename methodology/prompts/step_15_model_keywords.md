# Step 15 — Generate Model Keyword Dictionaries: AI Prompts

**Methodology step**: Step 15 — Generate model keyword dictionaries and count mentions

**Purpose**: Use LLMs to generate keyword lists for each candidate model identified in Step 14. Authors curate and structure the output into `data/reference/keywords/top_models_keywords.json`. Python then applies these dictionaries to count and normalize per-project mention frequency.

**Human review**: Not formalized as a coded review task. Authors curated keyword lists before committing to `top_models_keywords.json`.

### Output handling
LLM-generated keyword lists were reviewed and edited by the authors before being structured into `top_models_keywords.json`. Retained keywords required:
1. Lexical specificity — likely to match genuine references, not generic terms
2. Coverage of common variants (hyphenated, abbreviated, proper nouns where relevant)
3. Minimal overlap with keywords already captured by the main innovation dictionary

Final output: `data/reference/keywords/top_models_keywords.json`

### Models
- **Model A**: ChatGPT (GPT-5) — approx. August–October 2025
- **Model B**: DeepSeek (V3) — approx. August–October 2025

---

## Coverage note

Sessions shown here are representative. Equivalent keyword-generation sessions were conducted for all 9 models in `top_models_keywords.json` but are not individually documented.

## Session 15.1 — E-procurement keyword generation

### User prompt
> Generate 15 concise tagging keywords for Electronic procurement (e-procurement) system. Aim for single-word (or tight compound-word) tags, not descriptive phrases or examples. Think lexical scanning.

### ChatGPT output
Here are 15 concise tagging keywords for an Electronic Procurement (e-procurement) system, optimized for lexical scanning and tagging:
1.	E-procurement
2.	Tendering
3.	Bid-submission
4.	Vendor-registration
5.	Contract-award
6.	Digital-signature
7.	Procurement-portal
8.	Document-tracking
9.	Workflow-approval
10.	Audit-trail
11.	Price-discovery
12.	Reverse-auction
13.	Sourcing
14.	E-invoicing
15.	Compliance-monitoring

### DeepSeek output
- sourcing
- purchasing
- requisition
- vendor
- catalog
- rfx
- po
- invoicing
- contracts
- compliance
- workflow
- automation
- spend-analytics
- e-catalog
- approval


### Output handling
Keywords retained from the above outputs were structured into `top_models_keywords.json`. See top-level output handling criteria above.
