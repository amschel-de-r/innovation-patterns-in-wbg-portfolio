# Methodology Documentation — PRWP 2025

This folder documents the non-automated steps in the 17-step analysis pipeline:
AI prompt records and human review protocols.

The Python-automated steps are covered by `scripts/run_analysis.py`.

---

## Step Index

| # | Description | Python | AI Prompts | Human Review | Notebooks |
|---|-------------|--------|------------|--------------|-----------|
| 1 | Normalize evaluation corpus | `run_analysis.py` | — | — | — |
| 2 | Develop innovation keyword dictionary | — | [prompts/step_02_dictionary.md](prompts/step_02_dictionary.md) | [human_review/hr_02_dictionary.md](human_review/hr_02_dictionary.md) | [match_method_sensitivity.ipynb](../notebooks/match_method_sensitivity.ipynb) |
| 3 | Tag each project by innovation content | `run_analysis.py` | — | — | — |
| 4 | Classify projects by innovation intensity and construct the Innovation Index | `run_analysis.py` | — | — | — |
| 5 | Human validation of Innovation Index | — | — | [human_review/hr_05_index.md](human_review/hr_05_index.md) | — |
| 6 | Build the innovative subset | `run_analysis.py` | — | — | — |
| 7 | Develop the innovation taxonomy | — | [prompts/step_07_taxonomy.md](prompts/step_07_taxonomy.md) | [human_review/hr_07_taxonomy.md](human_review/hr_07_taxonomy.md) | — |
| 8 | Human–machine reasoning | — | [prompts/step_08_reasoning.md](prompts/step_08_reasoning.md) | — | — |
| 9 | Formulate hypotheses | — | [prompts/step_09_hypotheses.md](prompts/step_09_hypotheses.md) | — | — |
| 10 | Operationalize each hypothesis | — | [prompts/step_10_operationalize.md](prompts/step_10_operationalize.md) | — | — |
| 11 | Apply feature tagging | `run_analysis.py` | — | — | [ifc_keyword_sensitivity.ipynb](../notebooks/ifc_keyword_sensitivity.ipynb) |
| 12 | Analyze the portfolio | `run_analysis.py` | — | — | — |
| 13 | Assess performance associations | `run_analysis.py` | — | — | — |
| 14 | Identify top innovation model candidates | — | [prompts/step_14_top_models.md](prompts/step_14_top_models.md) | — | — |
| 15 | Generate model keyword dictionaries and count mentions | `run_analysis.py` | [prompts/step_15_model_keywords.md](prompts/step_15_model_keywords.md) | — | — |
| 16 | Contextualize the narrative | — | [prompts/step_16_narration.md](prompts/step_16_narration.md) | — | — |
| 17 | Synthesize and report results | — | — | — <!-- Note: deliverable is the manuscript itself; no separate protocol file needed --> | — |

---

## Reviewer Qualifications

Shared across all human review tasks: [reviewers.md](reviewers.md)

---

## File Naming Conventions

- Prompt files: `prompts/step_NN_<label>.md` — one file per methodology step, one section per prompt call
- Human review files: `human_review/hr_NN_<label>.md` — one file per review task
- Prompt IDs follow the pattern `N.M` where `N` = methodology step, `M` = prompt sequence within that step
