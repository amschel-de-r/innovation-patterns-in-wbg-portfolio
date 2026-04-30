import sys
import shutil
import argparse
from pathlib import Path
import datetime
import matplotlib.pyplot as plt
import pandas as pd

# Add analysis root to path for src imports
_ANALYSIS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ANALYSIS_ROOT))

from src.clean_ieg_data import clean_data, load_fcs_countries
from src.create_kw_index import match_innovation_keywords
from src.create_table_replication import create_table_3_9, create_table_D_2a
from src.create_figure_replication import create_fig_3_1, create_fig_3_2, create_fig_3_4, create_fig_4_1, create_fig_D_1
from src.create_numbers_replication import create_numbers_summary, create_ifc_gp_table, create_ifc_country_table
from src._paths import DATA_ROOT, TABLES_DIR, OUTPUT_DIR
from src.table_config import TABLE_REPLICATION_MAP
from keyword_matcher import compare_runs, extract_snippets
from src.table_comparison import reconcile_for_comparison

# --- Pipeline configuration ---
DROP_NA_LESSONS = True
PREFER_PPAR_OVER_ICRR = True
RECALCULATE_FCS_STATUS = True
FCS_START_FY = 2015   # None = no lower bound; set e.g. to 2015 to restrict window
FCS_END_FY = 2025     # Countries on FCS list up to this fiscal year

RAW_FILE = DATA_ROOT / "raw" / "IEG_ICRR-PPAR_Lessons_2025-03-12.xlsx"

# Keyword sensitivity comparison: set to a processed_dataset.xlsx path to compare against,
# or None to skip. Defaults to the canonical processed output under data/processed/.
# Can also point to a prior sensitivity run, e.g.:
#   SENSITIVITY_OUTPUT_DIR / "20260303_143251" / "processed_dataset.xlsx"
BASELINE_PATH = DATA_ROOT / "processed" / "processed_dataset.xlsx"

SENSITIVITY_OUTPUT_DIR = OUTPUT_DIR / "sensitivity_analysis"


def load_data(file_path: Path) -> pd.DataFrame:
    """Load data from Excel file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_excel(file_path)


def write_figures(processed_df: pd.DataFrame, figures_dir: Path) -> None:
    fig = create_fig_3_1(processed_df)
    fig.savefig(figures_dir / "Fig3_1.svg", bbox_inches="tight")
    plt.close(fig)

    fig = create_fig_3_2(processed_df)
    fig.savefig(figures_dir / "Fig3_2.svg", bbox_inches="tight")
    plt.close(fig)

    fig = create_fig_3_4(processed_df, create_table_3_9(processed_df))
    fig.savefig(figures_dir / "Fig3_4.svg")
    plt.close(fig)

    fig = create_fig_4_1(create_table_D_2a(processed_df))
    fig.savefig(figures_dir / "Fig4_1.svg")
    plt.close(fig)

    fig = create_fig_D_1(processed_df)
    fig.savefig(figures_dir / "FigD_1.svg")
    plt.close(fig)


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
    for table_function, (table_path, use_first_col) in TABLE_REPLICATION_MAP.items():
        table = table_function(processed_df)
        paper_table = pd.read_excel(TABLES_DIR / "auto_extracted" / table_path)
        table, paper_table = reconcile_for_comparison(table, paper_table, use_first_col)
        try:
            table.compare(paper_table, result_names=("Proposed", "Current"), keep_shape=True, keep_equal=True).to_excel(run_dir / f"comparison_{table_path}")
        except ValueError as e:
            print(f"Comparison failed for {table_path}: {e}")


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


def run_promote(raw_df: pd.DataFrame, clean_df: pd.DataFrame, processed_df: pd.DataFrame) -> None:
    clean_df.to_excel(DATA_ROOT / "intermediate" / "cleaned_dataset.xlsx", index=False)
    processed_df.to_excel(DATA_ROOT / "processed" / "processed_dataset.xlsx", index=False)

    for table_function, (table_path, _) in TABLE_REPLICATION_MAP.items():
        table = table_function(processed_df)
        table.to_excel(TABLES_DIR / "generated" / table_path, index=False)

    write_supplementary_outputs(raw_df, processed_df, OUTPUT_DIR)
    write_figures(processed_df, OUTPUT_DIR / "figures")


def run_sensitivity(raw_df: pd.DataFrame, processed_df: pd.DataFrame) -> None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = SENSITIVITY_OUTPUT_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    processed_df.to_excel(run_dir / "processed_dataset.xlsx", index=False)

    if BASELINE_PATH is not None and BASELINE_PATH.exists():
        baseline_df = pd.read_excel(BASELINE_PATH)
        run_keyword_comparison(baseline_df, processed_df, run_dir)

    run_table_comparisons(processed_df, run_dir)
    append_sensitivity_config(timestamp)
    write_supplementary_outputs(raw_df, processed_df, run_dir)
    write_figures(processed_df, run_dir)


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

    fcs_countries_list = load_fcs_countries(start_fy=FCS_START_FY, end_fy=FCS_END_FY)
    raw_df = load_data(RAW_FILE)
    clean_df = clean_data(
        raw_df,
        drop_na_lessons=DROP_NA_LESSONS,
        prefer_ppar_over_icrr=PREFER_PPAR_OVER_ICRR,
        recalculate_fcs_status=RECALCULATE_FCS_STATUS,
        fcs_countries_list=fcs_countries_list,
    )
    processed_df = match_innovation_keywords(clean_df, keywords_dir=DATA_ROOT / "reference" / "keywords")

    if args.promote:
        run_promote(raw_df, clean_df, processed_df)
    else:
        run_sensitivity(raw_df, processed_df)


if __name__ == "__main__":
    main()
