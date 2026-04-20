import os
import sys
import shutil
import argparse
from pathlib import Path
import datetime
import pandas as pd

# Add analysis root to path for src imports
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ANALYSIS_ROOT))

from src.clean_ieg_data import clean_data, load_fcs_countries
from src.create_kw_index import match_innovation_keywords
from src.create_table_replication import (
    create_table_3_1, create_table_3_2, create_table_3_3, create_table_3_5,
    create_table_3_6, create_table_3_7, create_table_3_8, create_table_3_9,
    create_table_3_11, create_table_3_12, create_table_3_13,
    create_table_3_15, create_table_3_16,
    create_table_4_1,
    create_table_D_1,
    create_table_D_2a, create_table_D_2b, create_table_D_2c, create_table_D_2d,
    create_table_E_1, create_table_E_2, create_table_E_5,
    create_table_E_10,
    create_table_F_1, create_table_F_2, create_table_F_3, create_table_F_4,
    create_table_F_5
)
from src.create_figure_replication import (
    create_fig_3_1, create_fig_3_3, create_fig_4_1, create_fig_D_1
)
from src.create_numbers_replication import (
    create_numbers_summary, create_ifc_gp_table, create_ifc_country_table
)
from src._paths import DATA_ROOT, TABLES_DIR, OUTPUT_DIR
from keyword_matcher import compare_runs, extract_snippets
from src.table_comparison import reconcile_for_comparison

SENSITIVITY_OUTPUT_DIR = OUTPUT_DIR / "sensitivity_analysis"

# Default pipeline parameters
DROP_NA_LESSONS = True
PREFER_PPAR_OVER_ICRR = True
RECALCULATE_FCS_STATUS = True
FCS_START_FY = 2015   # None = no lower bound; set e.g. to 2015 to restrict window
FCS_END_FY = 2025     # Countries on FCS list up to this fiscal year

# Keyword sensitivity comparison: set to a processed_dataset.xlsx path to compare against,
# or None to skip. Defaults to the canonical processed output under data/processed/.
# Can also point to a prior sensitivity run, e.g.:
#   SENSITIVITY_OUTPUT_DIR / "20260303_143251" / "processed_dataset.xlsx"
BASELINE_PATH = DATA_ROOT / "processed" / "processed_dataset.xlsx"

RAW_FILE = DATA_ROOT / "raw" / "IEG_ICRR-PPAR_Lessons_2025-03-12.xlsx"
FCS_COUNTRIES_LIST = load_fcs_countries(start_fy=FCS_START_FY, end_fy=FCS_END_FY)

def load_data(file_path: Path) -> pd.DataFrame:
    """Load data from Excel file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_excel(file_path)

TABLE_REPLICATION_MAP = {
    create_table_3_1: ["Table_3.1._Evolution_of_Innovation_Intensity_in_Bank_Group_Projects_(5-Year_Cohorts,_1998–2025).xlsx", True],
    create_table_3_2: ["Table_3.2._Contextualizing_the_Innovation_Intensity_of_Bank_Group_Projects_Over_Time.xlsx", True],
    create_table_3_3: ["Table_3.3._Innovation_Scaling_Patterns_in_World_Bank_Lending.xlsx", True],
    create_table_3_5: ["Table_3.5._Prevalence_of_Innovation_Types_in_the_Innovation_PortfolioT.xlsx", True],
    create_table_3_6: ["Table_3.6._Prevalence_of_Innovation_Types_by_Decade.xlsx", True],
    create_table_3_7: ["Table_3.7._Innovation_Intensity_by_Region.xlsx", True],
    create_table_3_8: ["Table_3.8._Innovation_in_FCS_Contexts.xlsx", True],
    create_table_3_9: ["Table_3.9._Sectoral_Patterns_of_Innovation_in_GPs.xlsx", True],
    create_table_3_11: ["Table_3.11._Technology_Premium_Across_Projects.xlsx", True],
    create_table_3_12: ["Table_3.12._Technology_Premium_in_Projects_by_GP_(High_+_Moderate_Projects).xlsx", True],
    create_table_3_13: ["Table_3.13._Projects_with_IFC_Collaboration.xlsx", True],
    create_table_3_15: ["Table_3.15._PCM_Projects.xlsx", True],
    create_table_3_16: ["Table_3.16._Sectors_with_Active_PCM.xlsx", True],
    create_table_4_1: ["Table_4.1._Importance_of_Context-Appropriate_Innovation.xlsx", True],
    create_table_D_1: ["Table_D.1._Distribution_of_Innovation_in_WBG_portfolio.xlsx", True],
    create_table_D_2a: ["Table_D.2a._Innovation_Premium_Across_Projects_-.xlsx", True],
    create_table_D_2b: ["Table_D.2b._Innovation_Premium_Across_Projects_–_Bank_Performance_Rating.xlsx", True],
    create_table_D_2c: ["Table_D.2c._Innovation_Premium_Across_Projects_–_Quality_of_Supervision_Rating.xlsx", True],
    create_table_D_2d: ["Table_D.2d._Innovation_Premium_Across_Projects_–_Quality_at_Entry_Rating.xlsx", True],
    create_table_E_1: ["Table_E.1._Selected_Examples_of_Innovation_Models_Generated_Based_on_the_Analytics.xlsx", True],
    create_table_E_2: ["Table_E.2._Top_Four_Innovation_Models_by_Decade.xlsx", True],
    create_table_E_5: ["Table_E.5._Diffusion_of_PPP_Model_Over_Time.xlsx", True],
    create_table_E_10: ["Table_E.10._Diffusion_of_CDD_Model_Over_Time.xlsx", True],
    create_table_F_1: ["Table_F.1._Diffusion_of_Innovation_Models_in_FCS_vs._Non-FCS.xlsx", False],
    create_table_F_2: ["Table_F.2._Diffusion_of_Innovation_Models_in_FCS_vs._Non-FCS_Conditional_Cash_Transfers.xlsx", True],
    create_table_F_3: ["Table_F.3._Diffusion_of_Innovation_Models_in_FCS_vs._Non-FCS_PPP.xlsx", True],
    create_table_F_4: ["Table_F.4._Diffusion_of_Innovation_Models_in_FCS_vs._Non-FCS_E-Procurement.xlsx", True],
    create_table_F_5: ["Table_F.5._Diffusion_of_Innovation_Models_in_FCS_vs._Non-FCS_CDD.xlsx", True],
}


def write_supplementary_outputs(raw_df: pd.DataFrame, processed_df: pd.DataFrame, dest_dir: Path) -> None:
    with pd.ExcelWriter(dest_dir / "numbers_summary.xlsx", engine="openpyxl") as writer:
        create_numbers_summary(raw_df, processed_df).to_excel(writer, sheet_name="Summary", index=False)
        create_ifc_gp_table(processed_df).to_excel(writer, sheet_name="IFC by GP")
        create_ifc_country_table(processed_df).to_excel(writer, sheet_name="IFC by Country")


def run_keyword_comparison(baseline_df: pd.DataFrame, processed_df: pd.DataFrame, run_dir: Path) -> None:
    kw_comparison = compare_runs(baseline_df, processed_df, join_key="project_id")
    kw_comparison.summary.to_excel(run_dir / "kw_diff_summary.xlsx", index=False)
    kw_comparison.changes.to_excel(run_dir / "kw_diff_changes.xlsx")
    if len(kw_comparison.added):
        pd.DataFrame({"project_id": kw_comparison.added}).to_excel(run_dir / "kw_diff_added.xlsx", index=False)
    if len(kw_comparison.removed):
        pd.DataFrame({"project_id": kw_comparison.removed}).to_excel(run_dir / "kw_diff_removed.xlsx", index=False)


def run_table_comparisons(processed_df: pd.DataFrame, run_dir: Path) -> None:
    for table_function, [table_path, use_first_col] in TABLE_REPLICATION_MAP.items():
        table = table_function(processed_df)
        paper_table = pd.read_excel(TABLES_DIR / "auto_extracted" / table_path)
        table, paper_table = reconcile_for_comparison(table, paper_table, use_first_col)
        try:
            table.compare(paper_table, result_names=("Proposed", "Current"), keep_shape=True, keep_equal=True).to_excel(run_dir / f"comparison_{table_path}")
        except ValueError:
            print(table_path)
            print(paper_table)
            print(table)


def append_sensitivity_config(timestamp: str) -> None:
    sensitivity_config = pd.DataFrame({
        'RUN': timestamp,
        "DROP_NA_LESSONS": DROP_NA_LESSONS,
        "PREFER_PPAR_OVER_ICRR": PREFER_PPAR_OVER_ICRR,
        "RECALCULATE_FCS_STATUS": RECALCULATE_FCS_STATUS,
    }, index=[0])
    config_path = SENSITIVITY_OUTPUT_DIR / "sensitivity_config.xlsx"
    if config_path.exists():
        config_table = pd.read_excel(config_path)
        sensitivity_config = pd.concat([config_table, sensitivity_config], ignore_index=True)
    sensitivity_config.to_excel(config_path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true", help="Write results directly to canonical locations")
    parser.add_argument("--clean", action="store_true", help="Delete all sensitivity analysis folders")
    args = parser.parse_args()

    if args.clean:
        for folder in SENSITIVITY_OUTPUT_DIR.iterdir():
            if folder.is_dir():
                shutil.rmtree(folder)
        print("Cleaned sensitivity analysis folders.")
        if not args.promote:
            return

    raw_df = load_data(RAW_FILE)

    clean_df = clean_data(
        raw_df,
        drop_na_lessons=DROP_NA_LESSONS,
        prefer_ppar_over_icrr=PREFER_PPAR_OVER_ICRR,
        recalculate_fcs_status=RECALCULATE_FCS_STATUS,
        fcs_countries_list=FCS_COUNTRIES_LIST
    )

    processed_df = match_innovation_keywords(clean_df, keywords_dir=DATA_ROOT / "reference" / "keywords")

    if args.promote:
        clean_df.to_excel(DATA_ROOT / "intermediate" / "cleaned_dataset.xlsx", index=False)
        processed_df.to_excel(DATA_ROOT / "processed" / "processed_dataset.xlsx", index=False)

        for table_function, [table_path, _] in TABLE_REPLICATION_MAP.items():
            table = table_function(processed_df)
            table.to_excel(TABLES_DIR / "generated" / table_path, index=False)

        write_supplementary_outputs(raw_df, processed_df, OUTPUT_DIR)
        figures_dir = OUTPUT_DIR / "figures"

    else:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = SENSITIVITY_OUTPUT_DIR / timestamp
        os.makedirs(run_dir)

        clean_df.to_excel(run_dir / "cleaned_dataset.xlsx", index=False)
        processed_df.to_excel(run_dir / "processed_dataset.xlsx", index=False)

        if BASELINE_PATH is not None and BASELINE_PATH.exists():
            baseline_df = pd.read_excel(BASELINE_PATH)
            run_keyword_comparison(baseline_df, processed_df, run_dir)

        run_table_comparisons(processed_df, run_dir)
        append_sensitivity_config(timestamp)
        write_supplementary_outputs(raw_df, processed_df, run_dir)
        figures_dir = run_dir

    create_fig_3_1(processed_df).savefig(figures_dir / "Fig3_1.png", bbox_inches="tight")
    create_fig_3_3(processed_df, create_table_3_9(processed_df)).savefig(figures_dir / "Fig3_3.svg")
    create_fig_4_1(create_table_D_2a(processed_df)).savefig(figures_dir / "Fig4_1.svg")
    create_fig_D_1(processed_df).savefig(figures_dir / "FigD_1.svg")


if __name__ == "__main__":
    main()
