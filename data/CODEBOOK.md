# Codebook: processed_dataset.xlsx

This file documents all columns in `data/processed/processed_dataset.xlsx`, the main analysis-ready dataset produced by `scripts/run_analysis.py`. One row per project (7,574 projects after de-duplication).

---

## Project Identifiers and Metadata

| Column | Type | Description |
|---|---|---|
| `project_id` | string | World Bank project identifier (P-code), e.g. `P001234`. Primary key. |
| `project_name` | string | Full project name as recorded in IEG data. |
| `wb_region` | string | World Bank administrative region (e.g. `Sub-Saharan Africa`, `South Asia`). |
| `country` | string | Borrowing country name. |
| `country_lending_group` | string | IDA, IBRD, or Blend classification of the borrowing country at time of project. |
| `fcs_status` | string | `"FCS"` if the country appeared on the FCS Harmonized List during the fiscal years covered by the project (see `FCS_START_FY`/`FCS_END_FY` in `run_analysis.py`); otherwise `"Non-FCS"`. |
| `practice_group` | string | World Bank practice group (broader organizational unit). |
| `global_practice` | string | World Bank global practice (sub-unit within the practice group). |
| `wb_agreement_type` | string | Type of World Bank agreement (e.g. Loan, Credit, Grant). |
| `wb_lending_instrument_type` | string | Lending instrument type (e.g. Investment Project Financing, Development Policy Financing). |

---

## Project Dates

| Column | Type | Description |
|---|---|---|
| `approval_fy` | integer | World Bank fiscal year of project approval. |
| `closing_fy` | integer | World Bank fiscal year of project closing. |
| `evaluation_fy` | integer | World Bank fiscal year of the IEG evaluation. |
| `cohort` | string | 5-year cohort label based on `evaluation_fy`. Values: `"1998-2002"`, `"2003-2007"`, `"2008-2012"`, `"2013-2017"`, `"2018-2022"`, `"2023-2025"`. |
| `decade` | string | Decade label based on `evaluation_fy`. Values: `"1998-2007"`, `"2008-2017"`, `"2018-2025"`. |

---

## Evaluation Metadata

| Column | Type | Description |
|---|---|---|
| `evaluation_type` | string | `ICRR` (Implementation Completion Report Review) or `PPAR` (Project Performance Assessment Report). Where both exist for a project, PPAR is preferred. |
| `project_volumn` | string | Project volume classification as recorded in IEG data. Note: column name contains a typo ("volumn") inherited from the source data. |
| `text_url` | string | URL to the HTML version of the IEG evaluation report. |
| `pdf_url` | string | URL to the PDF version of the IEG evaluation report. |
| `lessons` | string | Full text of the project's Lessons Learned section, as extracted from the IEG evaluation. This is the primary text field used for keyword matching. |

---

## IEG Ratings

Ratings are stored in both text and numeric form. The numeric scale maps as follows: Highly Satisfactory = 6, Satisfactory = 5, Moderately Satisfactory = 4, Moderately Unsatisfactory = 3, Unsatisfactory = 2, Highly Unsatisfactory = 1.

| Column | Type | Description |
|---|---|---|
| `ieg_outcome_ratings` | string | IEG outcome rating (text). |
| `ieg_outcome_ratings_num` | float | Numeric conversion of outcome rating (1–6 scale). |
| `ieg_quality_at_entry_ratings` | string | IEG quality at entry rating (text). |
| `ieg_quality_at_entry_ratings_num` | float | Numeric conversion of quality at entry rating. |
| `ieg_quality_of_supervision_ratings` | string | IEG quality of supervision rating (text). |
| `ieg_quality_of_supervision_ratings_num` | float | Numeric conversion of supervision quality rating. |
| `ieg_bank_performance_ratings` | string | IEG bank performance rating (text). |
| `ieg_bank_performance_ratings_num` | float | Numeric conversion of bank performance rating. |
| `ieg_monitoring_and_evaluation_quality_ratings` | string | IEG monitoring and evaluation quality rating (text). Not converted to numeric. |

---

## Innovation Index

| Column | Type | Description |
|---|---|---|
| `innovation_matched_keywords` | string (list) | Serialized list of distinct innovation keywords matched in the project's lessons text. |
| `innovation_distinct_hits` | integer | Count of distinct innovation keywords matched (duplicates within a document not counted). |
| `innovation_tier` | string | Three-tier classification: `High` (≥4 distinct hits), `Moderate` (2–3 hits), `Low` (0–1 hits). |
| `high_innovation` | integer (0/1) | `1` if `innovation_tier` is `'High'` or `'Moderate'` (i.e. ≥2 distinct keyword hits); `0` otherwise. |

---

## Innovation Model Tags

Binary flags indicating whether the project's lessons text mentions keywords associated with each innovation model. Applied to all projects (not just the innovative subset).

| Column | Type | Description |
|---|---|---|
| `digital_government_tag` | boolean | Mentions digital government / e-government keywords. |
| `e_procurement_tag` | boolean | Mentions e-procurement keywords. |
| `ppp_tag` | boolean | Mentions public-private partnership (PPP) keywords. |
| `cdd_tag` | boolean | Mentions community-driven development (CDD) keywords. |
| `cct_tag` | boolean | Mentions conditional cash transfer (CCT) keywords. |
| `e_learning_tag` | boolean | Mentions e-learning / distance learning keywords. |
| `mobile_banking_tag` | boolean | Mentions mobile banking / mobile money keywords. |
| `remote_sensing_tag` | boolean | Mentions remote sensing / satellite data keywords. |
| `biometric_id_tag` | boolean | Mentions biometric identification keywords. |

---

## Innovation Type Taxonomy

Four-category taxonomy classifying the type of innovation present. Multi-label: a project can be assigned multiple categories.

| Column | Type | Description |
|---|---|---|
| `operational_institutional_tag` | boolean | Innovation is primarily operational or institutional in nature. |
| `technological_tag` | boolean | Innovation is primarily technological in nature. |
| `collaborative_tag` | boolean | Innovation involves collaborative arrangements (e.g. partnerships, co-financing). |
| `financial_tag` | boolean | Innovation is primarily financial (e.g. new instruments, blended finance). |
| `has_no_category` | boolean | `True` if the project has no taxonomy category assigned (only applies within the innovative subset). |

---

## Feature Tags

Additional binary flags for hypothesis testing.

| Column | Type | Description |
|---|---|---|
| `pcm_tag` | boolean | Mentions project cycle management (PCM) keywords. |
| `pilot_tag` | boolean | Mentions pilot / pilot project keywords. |
| `scale_tag` | boolean | Mentions scale-up / scaling keywords. |
| `ifc_tag` | boolean | Mentions IFC (International Finance Corporation) keywords. |
| `pilot_category` | string | Pilot/scale classification combining `pilot_tag` and `scale_tag`. Values: `No Pilot` (no pilot or scale keyword match), `Pilot Only` (pilot keyword matched, no scale keyword), `Pilot + Scaled` (both pilot and scale keywords matched). |
