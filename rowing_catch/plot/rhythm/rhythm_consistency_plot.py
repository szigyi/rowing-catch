"""Rhythm Consistency renderer.

Renders SPM vs drive phase percentage scatter plot with ideal curve and cycle labels.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_IDEAL_RATIO, COLOR_MAIN, COLOR_TEXT_SUB
from rowing_catch.plot.utils import setup_premium_plot


def render_rhythm_consistency(
    computed_data: dict[str, Any],
    return_fig: bool = False,
) -> matplotlib.figure.Figure | None:
    """Render rhythm consistency scatter plot with ideal drive% curve.

    Args:
        computed_data: Output from RhythmConsistencyComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data['has_data']:
        st.warning('No individual cycle data available for rhythm consistency.')
        st.info(f'**Performance Insight:** {coach_tip}')
        return None

    spm_vals = np.array(data['spm_vals'])
    drive_pct_vals = np.array(data['drive_pct_vals'])
    mean_spm = data['mean_spm']
    mean_drive_pct = data['mean_drive_pct']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(7, 4),
    )

    # Ideal drive% curve
    ax.plot(
        data['ideal_curve_spm'],
        data['ideal_curve_drive_pct'],
        color=COLOR_IDEAL_RATIO,
        linewidth=2.5,
        linestyle='-',
        alpha=0.8,
        label='Ideal',
        zorder=10,
    )

    # Mean crosshair lines
    if not np.isnan(mean_spm):
        ax.axvline(mean_spm, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            mean_spm, 58, 'Mean SPM', 
            color='#64748b', fontsize=8, ha='right', va='center', rotation=90,
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1)
        )
    if not np.isnan(mean_drive_pct):
        ax.axhline(mean_drive_pct, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            ax.get_xlim()[1] - 1, mean_drive_pct, 'Mean Drive%', 
            color='#64748b', fontsize=8, ha='right', va='bottom',
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1)
        )

    # Boxplot / Candlesticks
    # Group data by rounded integer SPM to show vertical distribution
    if len(spm_vals) > 0:
        df = pd.DataFrame({'spm': np.round(spm_vals).astype(float), 'drive': drive_pct_vals.astype(float)})
        # Use named aggregations to avoid inference issues
        stats = df.groupby('spm')['drive'].agg(
            min_val='min',
            max_val='max',
            q1=lambda x: x.quantile(0.25),
            q3=lambda x: x.quantile(0.75),
            median_val='median',
        )
        
        # Iterate and plot candlesticks
        for spm, row in stats.iterrows():
            spm_val = float(spm)  # type: ignore[arg-type]
            # Wick: min to max (thin line showing complete range)
            ax.vlines(spm_val, row['min_val'], row['max_val'], color=COLOR_MAIN, linewidth=1.0, alpha=0.6, zorder=5)
            # Body: Q1 to Q3 (interquartile range, where 50% of strokes land)
            ax.vlines(spm_val, row['q1'], row['q3'], color=COLOR_MAIN, linewidth=6.0, alpha=0.9, zorder=6)
            # Median: Small colored indicator
            ax.scatter([spm_val], [row['median_val']], color='#ffffff', edgecolors=COLOR_MAIN, s=15, zorder=7)
            # SPM Label for the candlestick
            ax.text(
                spm_val, row['max_val'] + 1, f'{int(spm_val)}', 
                color=COLOR_MAIN, fontsize=7, ha='center', va='bottom', weight='bold',
                alpha=0.8
            )

    # Raw Scatter points (made semi-transparent so candlesticks stand out)
    ax.scatter(spm_vals, drive_pct_vals, color=COLOR_MAIN, s=5, alpha=0.3, zorder=4, label='Strokes')

    # Fix Y-axis to a meaningful range for drive % (20–60%)
    ax.set_ylim(20, 60)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    st.pyplot(fig, width='stretch')
    plt.close(fig)

    if return_fig:
        return fig

    st.info(f'**Performance Insight:** {coach_tip}')
    return None
