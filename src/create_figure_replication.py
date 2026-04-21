"""Figure generation functions for PRWP 2025 analysis."""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import seaborn as sns


def _plot_innovation_panel(
    ax,
    data,
    comparison_data,
    label: str,
    n_cols: int,
    idx: int,
    line_color: str,
    benchmark_label_fontsize: int,
    main_label_fontsize: int,
    title_pad: int,
    title_y: float | None,
    ylim: tuple,
    xlim: tuple,
    spine_color: str,
    face_color: str,
    show_ylabel: bool,
) -> None:
    """Render one subplot panel for the small-multiples innovation figures.

    Plots a benchmark (dashed gray) line and a main (colored) line across
    three decade x-positions, with value labels positioned to avoid overlap.

    Args:
        ax: Matplotlib Axes object to draw on.
        data: Series with values for the three decades (main line).
        comparison_data: Series with values for the three decades (benchmark).
        label: Panel title text.
        n_cols: Number of columns in the grid (used to decide when to show y-label).
        idx: Panel index (0-based) in the flattened axes array.
        line_color: Hex color for the main data line.
        benchmark_label_fontsize: Font size for benchmark value labels.
        main_label_fontsize: Font size for main-line value labels.
        title_pad: Padding above the panel title.
        title_y: Vertical position of the title (None = matplotlib default).
        ylim: (min, max) for y-axis.
        xlim: (min, max) for x-axis.
        spine_color: Edge color for panel spines.
        face_color: Background color for panel.
        show_ylabel: If True, show y-axis label on leftmost column panels.
    """
    x_pos = [0, 1, 2]
    decades = ['1998-2007', '2008-2017', '2018-2025']

    # Benchmark line
    ax.plot(x_pos, comparison_data.values, linestyle='--', linewidth=1.5, color='#afb4c1', alpha=0.8)
    ax.scatter(x_pos, comparison_data.values, s=60, c='#CCCCCC', edgecolor='none', alpha=0.8, zorder=0)

    # Benchmark value labels
    for i, x in enumerate(x_pos):
        y = comparison_data.values[i]
        below = 1 if y <= data.values[i] else -1
        if not np.isnan(y):
            ax.text(
                x, y - below * 1.8, f'{y:.1f}%',
                ha='center', va='top' if below == 1 else 'bottom',
                fontsize=benchmark_label_fontsize, color='#333333', alpha=0.8,
            )

    # Main line
    ax.plot(x_pos, data.values, marker='o', linewidth=2, markersize=8, color=line_color)

    # Main-line value labels
    for i, x in enumerate(x_pos):
        y = data.values[i]
        above = 1 if y >= comparison_data.values[i] else -1
        ax.text(
            x, y + above * 2, f'{y:.0f}%',
            ha='center', va='bottom' if above == 1 else 'top',
            fontsize=main_label_fontsize, fontweight='bold',
        )

    # Panel title
    title_kwargs = dict(fontsize=11, fontweight='bold', pad=title_pad, loc='center', color='#016dbf')
    if title_y is not None:
        title_kwargs['y'] = title_y
    ax.set_title(label, **title_kwargs)

    ax.set_ylim(*ylim)
    ax.set_xlim(*xlim)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(decades, fontsize=7, rotation=0)
    ax.set_yticks([])

    if show_ylabel and idx % n_cols == 0:
        ax.set_ylabel('% Projects that are Innovative', fontsize=9)

    for spine in ax.spines.values():
        spine.set_edgecolor(spine_color)
        spine.set_linewidth(0.5)
        spine.set_visible(True)

    ax.set_facecolor(face_color)
    ax.grid(False)
    ax.tick_params(axis='x', length=0)


def create_fig_3_1(df: pd.DataFrame):

    overall_share = (
        df
        .groupby('decade')['high_innovation']
        .mean()
        .mul(100)
    )

    # Calculate percentage of HM projects by region and cohort
    # Denominator: all projects in that cohort & region (all innovation statuses)
    # Numerator: HM projects in that cohort & region

    plot_data = (
        df
        .query("wb_region != 'Other'")
        .assign(wb_region=lambda x: x.wb_region.str.replace(" and ", " & "))
        .groupby(['wb_region', 'decade', 'high_innovation'], observed=True)
        .size()
        .reset_index(name='count')
    )

    # Calculate totals per region/decade (all innovation statuses)
    totals = (
        plot_data
        .groupby(['wb_region', 'decade'], observed=True)['count']
        .sum()
        .reset_index(name='total')
    )

    # Calculate HM percentages
    plot_data_pct = (
        plot_data
        .query("high_innovation == 1")
        .merge(totals, on=['wb_region', 'decade'])
        .assign(pct_hm = lambda x: (x['count'] / x['total']) * 100)
        .replace({'wb_region': {
            'East Asia & Pacific': 'EAP',
            'South Asia': 'SAR',
            'Eastern & Southern Africa': 'AFE',
            'Europe & Central Asia': 'ECA',
            'Middle East & North Africa': 'MNA',
            "Western & Central Africa": 'AFW',
            'Latin America & Caribbean': 'LAC',
        }})
        .pivot(index='wb_region', columns='decade', values='pct_hm')
        .fillna(0)
        [['1998-2007', '2008-2017', '2018-2025']]  # Ensure column order
    )

    # Define custom region order
    region_order = [
        'EAP',
        "SAR",
        "AFE",
        'ECA',
        'MNA',
        "AFW",
        'LAC',
    ]

    # Get regions in custom order (only those that exist in the data)
    regions = [r for r in region_order if r in plot_data_pct.index]
    n_regions = len(regions)

    # Create small multiples layout
    n_cols = 2
    n_rows = (n_regions + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(6.5, n_rows * 2), dpi=150)
    axes = axes.flatten()

    # Plot each region
    for idx, region in enumerate(regions):
        _plot_innovation_panel(
            ax=axes[idx],
            data=plot_data_pct.loc[region],
            comparison_data=overall_share,
            label=region,
            n_cols=n_cols,
            idx=idx,
            line_color='#00274c',
            benchmark_label_fontsize=7,
            main_label_fontsize=8,
            title_pad=0,
            title_y=0.85,
            ylim=(0, 33),
            xlim=(-0.1, 2.1),
            spine_color='#dbe8f3',
            face_color='#fafdff',
            show_ylabel=False,
        )

    legend_text_main = "Region-specific"
    legend_text_compare =  "Global average"

    legend_elements = [
        Line2D([0], [0], color='#1D486F', linewidth=2, marker='o', markersize=5, label=legend_text_main),
        Line2D([0], [0], color='#afb4c1', linewidth=1.5, linestyle='--', marker='o', markersize=5, 
            markerfacecolor='#CCCCCC', markeredgewidth=0, alpha=0.8, label=legend_text_compare)
    ]
    fig.legend(handles=legend_elements, loc='lower right', bbox_to_anchor=(0.99, 0.1),                                                                               
              frameon=False, fontsize=8)

    # Hide empty subplots
    for idx in range(n_regions, len(axes)):
        axes[idx].set_visible(False)

    # Overall title
    fig.suptitle("% of Projects that are Innovative (by Region and Cohort)", 
                fontsize=9, fontweight='bold', x=0.5, ha='center', color='#016dbf')

    fig.patch.set_facecolor('white')
    fig.subplots_adjust(
        left=0.04,    # smaller left margin
        right=0.98,   # smaller right margin
        hspace=0.25,   # increase vertical gap between subplot rows
        wspace=0.25,
        bottom=0.12,   # keep x labels visible
        top=0.93       # reserve space for suptitle/legend
    )

    return fig


def create_fig_3_3(df: pd.DataFrame, t39_df: pd.DataFrame):

    t39 = t39_df[['GP', '% of Sectoral Portfolio']]
    top_share_gps = t39[0:9]

    at_least_1 = (
        pd.DataFrame(
            df.loc[df['high_innovation'] == 1]
            .pivot_table(values='project_id', index='global_practice', columns='decade', aggfunc=pd.Series.nunique)
            .dropna()
        )
        .reset_index()['global_practice']
    )

    t39 = t39.loc[t39['GP'].isin(at_least_1)][['GP','% of Sectoral Portfolio']]
    top_share_gps = t39[0:9]

    # Calculate overall share across all GPs
    overall_share = (
        df
        .groupby('decade')['high_innovation']
        .mean()
        .mul(100)
    )

    # Calculate percentage of HM projects by GP and decade
    # Denominator: all projects in that decade & GP (all innovation statuses)
    # Numerator: HM projects in that decade & GP

    plot_data = (
        df.loc[df['global_practice'].isin(top_share_gps['GP'])]
        .assign(
            global_practice = lambda x: x.global_practice.str.replace("the Blue Economy", "\nBlue Economy")
        )
        .groupby(['global_practice', 'decade', 'high_innovation'], observed=True)
        .size()
        .reset_index(name='count')
    )

    # Calculate totals per region/decade (all innovation statuses)
    totals = (
        plot_data
        .groupby(['global_practice', 'decade'], observed=True)['count']
        .sum()
        .reset_index(name='total')
    )

    # Calculate HM percentages
    plot_data_pct = (
        plot_data
        .query("high_innovation == 1")
        .merge(totals, on=['global_practice', 'decade'])
        .assign(pct_hm = lambda x: (x['count'] / x['total']) * 100)
        .pivot(index='global_practice', columns='decade', values='pct_hm')
        .fillna(0)
        [['1998-2007', '2008-2017', '2018-2025']]  # Ensure column order
    )

    gp_order = [
        'Social Protection and Jobs',
        'Agriculture and Food',
        'Energy and Extractives',
        'Environment',
        'Urban, Resilience and Land',
        'Health, Nutrition and Population',
        'Transport',
        'Water',
        'Education',
    ]

    # Get regions in custom order (only those that exist in the data)
    regions = [r for r in gp_order if r in plot_data_pct.index]
    n_regions = len(regions)

    # Create small multiples layout
    n_cols = 3
    n_rows = (n_regions + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 3), dpi=150)
    axes = axes.flatten()

    # Plot each GP
    for idx, region in enumerate(regions):
        _plot_innovation_panel(
            ax=axes[idx],
            data=plot_data_pct.loc[region],
            comparison_data=overall_share,
            label=region,
            n_cols=n_cols,
            idx=idx,
            line_color='#1D486F',
            benchmark_label_fontsize=8,
            main_label_fontsize=10,
            title_pad=10,
            title_y=None,
            ylim=(-3, 35),
            xlim=(-0.3, 2.3),
            spine_color='white',
            face_color='white',
            show_ylabel=True,
        )

    legend_text_main = "GP-specific"
    legend_text_compare =  "Global average"
    legend_elements = [
        Line2D([0], [0], color='#1D486F', linewidth=2, marker='o', markersize=6, label=legend_text_main),
        Line2D([0], [0], color='#afb4c1', linewidth=1.5, linestyle='--', marker='o', markersize=6, 
            markerfacecolor='#CCCCCC', markeredgewidth=0, alpha=0.8, label=legend_text_compare)
    ]
    fig.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0.02, 0.99), 
            frameon=False, fontsize=9)

    # Hide empty subplots
    for idx in range(n_regions, len(axes)):
        axes[idx].set_visible(False)

    # Overall title
    fig.suptitle("% of Projects that are Innovative (by GP and Cohort)", 
                fontsize=14, fontweight='bold', x=0.5, ha='center', color='#016dbf')

    fig.patch.set_facecolor('white')
    plt.tight_layout(rect=[0, 0, 1, 0.97], h_pad=2.5, w_pad=2)
    return fig

def create_fig_4_1(d1_df: pd.DataFrame):

    d1 = d1_df.assign(
        Projects=lambda x: x['Projects'].replace({
            'Low Innovation': '"Standard" Projects',
            'High + Moderate Innovative Projects': 'Projects with Innovation',
        })
    )

    all_val = d1.loc[d1["Projects"] == "All", "Average Rating"].iloc[0]
    bars_df = d1.loc[d1["Projects"] != "All", ["Projects", "Difference from Overall"]].sort_values(by='Difference from Overall')

    fig, ax = plt.subplots()

    bars = ax.bar(
        bars_df["Projects"],
        bars_df["Difference from Overall"],
        color=["#afb4c1", "#00a7ea"],
        width=0.5
    )

    line = ax.axhline(
        y=0,
        color="#7f8c8d",
        linestyle="--",
        linewidth=1.5
    )
    ax.text(
        0.57, 0.48, "Average =",
        transform=ax.transAxes,
        ha='right', va='top',
        fontsize=10, color='#7f8c8d'  # matches axis label defaults
    )
    ax.set_xlabel("Innovation Level")
    ax.set_ylabel("Difference from Overall")
    ax.set_title('Compared to Average IEG Project Rating',
                fontsize=12, fontweight='bold', pad=20, color='#016dbf')
    ax.grid(True, axis="y", alpha=0.2, linestyle="--")
    ax.set_ylim(-0.1, 0.15)

    # Bar value labels (white, inside bars)
    for rect in bars:
        h = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2,
            h/2,
            f"{h:.2f}",
            ha="center", va="center",
            color="black", fontsize=9
        )

    x0, x1 = ax.get_xticks()[0], ax.get_xticks()[1]
    x_mid = (x0 + x1) / 2
    ax.text(
        x_mid, 0 ,
        f"{all_val:.2f}",
        color="#7f8c8d",
        ha="center", va="bottom", fontsize=9
    )

    return fig

def create_fig_D_1(df: pd.DataFrame):

    rating_all = (
        df.groupby("decade")["ieg_outcome_ratings_num"]
        .mean()
        .round(2)
        .to_frame()
        .reset_index()
        .assign(hm_group="All Projects")
    )

    rating_hm = (
        df.assign(hm_group=lambda x: x.high_innovation.map({1: "High + Moderate Innovative", 0: "Low Innovative"}))
        .groupby(["decade", "hm_group"])["ieg_outcome_ratings_num"]
        .mean()
        .round(2)
        .to_frame()
        .reset_index()
    )

    T_Fig_D1 = pd.concat([rating_all, rating_hm], ignore_index=True, sort=False)

    fig, ax = plt.subplots()

    # Explicit order for consistent layering/legend
    groups = ["All Projects", "High + Moderate Innovative", "Low Innovative"]

    style_map = {
        # Match global average style in create_fig_3_1
        "All Projects": dict(
            color="#afb4c1",
            linestyle="--",
            linewidth=1.5,
            marker="o",
            markersize=6,
            markerfacecolor="#CCCCCC",
            markeredgewidth=0,
            alpha=0.8,
            zorder=1,
        ),
        # Match "Innovative" style in projects_by_innovationgrouped
        "High + Moderate Innovative": dict(
            color="#00a7ea",
            linestyle="-",
            linewidth=2,
            marker="o",
            markersize=7,
            alpha=1.0,
            zorder=3,
        ),
        # Match "Standard" style in projects_by_innovationgrouped
        "Low Innovative": dict(
            color="#00274c",
            linestyle="-",
            linewidth=2,
            marker="o",
            markersize=7,
            alpha=1.0,
            zorder=2,
        ),
    }

    for group in groups:
        group_data = T_Fig_D1[T_Fig_D1["hm_group"] == group]
        ax.plot(
            group_data["decade"],
            group_data["ieg_outcome_ratings_num"],
            label=group,
            **style_map[group],
        )

    # Custom legend handles to preserve marker-face styling
    legend_elements = [
        Line2D(
            [0], [0],
            color="#afb4c1", linewidth=1.5, linestyle="--", marker="o",
            markersize=6, markerfacecolor="#CCCCCC", markeredgewidth=0, alpha=0.8,
            label="All Projects",
        ),
        Line2D(
            [0], [0],
            color="#00a7ea", linewidth=2, linestyle="-", marker="o",
            markersize=7, label="High + Moderate Innovative",
        ),
        Line2D(
            [0], [0],
            color="#00274c", linewidth=2, linestyle="-", marker="o",
            markersize=7, label="Low Innovative",
        ),
    ]
    ax.legend(handles=legend_elements, title="")

    ax.set_title(
        "Average IEG Outcome Ratings by Innovation Tier and Decade",
        fontsize=12,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Decade", fontsize=12, fontweight="bold")
    ax.set_ylabel("Average Rating", fontsize=12, fontweight="bold")

    ax.grid(True, alpha=0.3, linestyle="--")

    sns.despine()
    return fig