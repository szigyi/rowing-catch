"""Rhythm Consistency renderer.

Renders SPM vs drive phase percentage scatter plot with ideal curve and cycle labels.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.figure import Figure

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_IDEAL_RATIO, COLOR_MAIN
from rowing_catch.plot.utils import apply_annotations, setup_premium_plot


def render_rhythm_consistency(
    computed_data: dict[str, Any],
    active_annotations: set[str] | None = None,
    return_fig: bool = False,
) -> Figure | None:
    """Render rhythm consistency scatter plot with ideal drive% curve and annotation table.

    Args:
        computed_data: Output from RhythmConsistencyComponent.compute()
        active_annotations: Optional set of toggled annotation labels to display.
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']
    annotations = computed_data.get('annotations', [])

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

    # Mean crosshair lines
    if not np.isnan(mean_spm):
        ax.axvline(mean_spm, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            mean_spm,
            58,
            'Mean SPM',
            color='#64748b',
            fontsize=8,
            ha='right',
            va='center',
            rotation=90,
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1),
        )
    if not np.isnan(mean_drive_pct):
        ax.axhline(mean_drive_pct, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            ax.get_xlim()[1] - 1,
            mean_drive_pct,
            'Mean Drive%',
            color='#64748b',
            fontsize=8,
            ha='right',
            va='bottom',
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1),
        )

    # Raw Scatter points (now primary, along with annotations)
    ax.scatter(spm_vals, drive_pct_vals, color=COLOR_MAIN, s=6, alpha=0.4, zorder=4, label='Strokes')

    # Apply Annotations (drawings only)
    if annotations:
        # Override [I1] to use the specific teal color intended for the ideal ratio
        apply_annotations(ax, annotations, active_labels=active_annotations, color_overrides={'[I1]': COLOR_IDEAL_RATIO})

    # Fix Y-axis to a meaningful range for drive % (20–60%)
    ax.set_ylim(20, 60)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(f'**Performance Insight:** {coach_tip}')
        return None

    return fig
