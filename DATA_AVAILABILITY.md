# Data Availability Statement

## Summary

All data used in this analysis are publicly available. The primary dataset is distributed by the Independent Evaluation Group (IEG) of the World Bank Group and can be downloaded from the IEG website. Reference data on Fragile and Conflict-affected Situations (FCS) are published by the World Bank. No restricted or embargoed datasets are used.

**Rights statement:** All datasets listed below were obtained through publicly available channels. The authors confirm they have the right to use and redistribute these data for research purposes under the terms of the original data sources.

---

## Datasets

### 1. IEG ICRR-PPAR Project Lessons

| Field | Value |
|---|---|
| **Filename** | `data/raw/IEG_ICRR-PPAR_Lessons_2025-03-12.xlsx` |
| **Description** | Lessons learned text and evaluation metadata from IEG's Implementation Completion Report Reviews (ICRRs) and Project Performance Assessment Reports (PPARs). Covers World Bank lending projects evaluated from approximately 1995 to the present, with fields for project identifier, lessons text, outcome ratings, Global Practice, region, and evaluation dates. |
| **Source** | Independent Evaluation Group (IEG), World Bank Group |
| **URL** | https://ieg.worldbankgroup.org/page/ieg-data-world-bank-project-lessons |
| **Direct download** | https://ieg.worldbankgroup.org/sites/default/files/Data/IEG_ICRR-PPAR_Lessons_2025-03-12.xlsx |
| **Retrieved** | 2025-03-12 |
| **Citation** | Independent Evaluation Group (IEG), World Bank Group. (2025). *IEG Data: World Bank Project Lessons* [Dataset]. File: IEG_ICRR-PPAR_Lessons_2025-03-12.xlsx. Retrieved March 12, 2025, from https://ieg.worldbankgroup.org/page/ieg-data-world-bank-project-lessons |
| **Access** | Publicly available; included in this repository |
| **License** | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) with additional World Bank terms. Users may copy, distribute, adapt, display, or include the data in commercial and non-commercial products at no cost. Attribution must be provided in the format: "The World Bank: [Dataset name]: [Data source]." Full terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets |
| **Format** | Excel (.xlsx) |

#### Source data patch (applied programmatically)

Three rows in the source file have `NaN` lesson values because Excel misparses cell content that starts with `-` as a formula error. The corrected values are stored in `data/raw/IEG_ICRR-PPAR_Lessons_2025-03-12_patches.csv` and applied programmatically by `src/clean_ieg_data.py`, so the original downloaded file is the sole data input and no manually-edited variant is needed.

- **Project IDs:** P010525, P057531, P066749
- **Field:** `Lessons`
- **Root cause:** Cell values beginning with `-` are interpreted as formula errors by Excel and read as `NaN` by pandas; the lesson text itself is unchanged.
- **Fix applied:** 2026-01-15

---

### 2. FCS Country List

| Field | Value |
|---|---|
| **Filename** | `data/reference/FCS/FCS.xlsx` and `data/reference/FCS/FCSList-FY06toFY25.pdf` |
| **Description** | World Bank Harmonized List of Fragile and Conflict-affected Situations (FCS), published annually. Used to classify projects by the FCS status of the borrowing country. The analysis uses fiscal years 2015–2025 (`FCS_START_FY = 2015`, `FCS_END_FY = 2025` in `scripts/run_analysis.py`). Both files are included in this repository — no separate download is required. |
| **Source** | World Bank Group |
| **URL** | https://www.worldbank.org/en/topic/fragilityconflictviolence/brief/harmonized-list-of-fragile-situations |
| **Retrieved** | January 2026 |
| **Citation** | World Bank Group. (2025). *Harmonized List of Fragile and Conflict-Affected Situations: FY06 to FY25* [Dataset]. Retrieved January 2026, from https://www.worldbank.org/en/topic/fragilityconflictviolence/brief/harmonized-list-of-fragile-situations |
| **Access** | Publicly available; included in this repository |
| **License** | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) with additional World Bank terms. Users may copy, distribute, adapt, display, or include the data in commercial and non-commercial products at no cost. Attribution must be provided to The World Bank and its data providers. Full terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets |
| **Format** | Excel (.xlsx) and PDF |

---

## Data Integrity

SHA256 checksums for all input files (raw data and reference keyword dictionaries) are provided in [`DATA_CHECKSUMS.sha256`](DATA_CHECKSUMS.sha256) at the repository root. To verify:

```bash
shasum -a 256 --check DATA_CHECKSUMS.sha256
```
