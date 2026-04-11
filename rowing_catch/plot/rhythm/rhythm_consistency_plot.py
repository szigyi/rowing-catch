"""Rhythm Consistency renderer.

Renders SPM vs drive phase percentage scatter plot with ideal curve and cycle labels.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_IDEAL_RATIO, COLOR_MAIN, COLOR_TEXT_SUB
from rowing_catch.plot.utils import setup_premium_plot


def render_rhythm_consistency(computed_data: dict[str, Any]) -> None:
    """Render rhythm consistency scatter plot with ideal drive% curve.

    Args:
        computed_data: Output from RhythmConsistencyComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data['has_data']:
        st.warning('No individual cycle data available for rhythm consistency.')
        st.info(f'**Performance Insight:** {coach_tip}')
        return

    spm_vals = np.array(data['spm_vals'])
    drive_pct_vals = np.array(data['drive_pct_vals'])
    cycle_nums = data['cycle_nums']
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
        zorder=4,
    )

    # Mean crosshair lines
    if not np.isnan(mean_spm):
        ax.axvline(mean_spm, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7, label='Mean SPM')
    if not np.isnan(mean_drive_pct):
        ax.axhline(mean_drive_pct, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7, label='Mean Drive%')

    # Scatter points
    ax.scatter(spm_vals, drive_pct_vals, color=COLOR_MAIN, s=80, zorder=5)

    # Cycle labels
    for cx, cy, label in zip(spm_vals, drive_pct_vals, cycle_nums, strict=False):
        ax.annotate(str(label), (cx, cy), textcoords='offset points', xytext=(6, 4), fontsize=8, color=COLOR_TEXT_SUB)

    # Fix Y-axis to a meaningful range for drive % (20–60%)
    ax.set_ylim(20, 60)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    st.pyplot(fig, width='stretch')
    plt.close(fig)

    st.info(f'**Performance Insight:** {coach_tip}')
