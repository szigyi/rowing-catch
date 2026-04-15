"""Rhythm Consistency renderer.

Renders SPM vs drive phase percentage scatter plot with ideal curve and cycle labels.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any, Literal

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from matplotlib.figure import Figure

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_MAIN, COLOR_RHYTHM_SPREAD
from rowing_catch.plot.utils import apply_annotations, setup_premium_plot
from rowing_catch.plot_transformer.annotations import PhaseAnnotation


def _reposition_s1_label(
    ax: matplotlib.axes.Axes,
    ideal_spm: np.ndarray[Any, Any],
    ideal_drive_pct: np.ndarray[Any, Any],
    mean_spm: float,
) -> None:
    """Move the [S1] text label to whichever end of the curve is furthest from mean_spm."""
    spm_left = float(ideal_spm[0])
    spm_right = float(ideal_spm[-1])
    ha: Literal['left', 'right']
    if abs(spm_left - mean_spm) >= abs(spm_right - mean_spm):
        x_label, idx_label, ha = spm_left, 0, 'left'
    else:
        x_label, idx_label, ha = spm_right, -1, 'right'
    y_label = float(ideal_drive_pct[idx_label])
    y_offset = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05
    for txt in ax.texts:
        if txt.get_text() == '[S1]':
            txt.set_position((x_label, y_label + y_offset))
            txt.set_horizontalalignment(ha)
            break


def _draw_z2_label(
    ax: matplotlib.axes.Axes,
    annotations: list[Any],
    active_annotations: set[str] | None,
    color_overrides: dict[str, str] | None,
) -> None:
    """Draw a [Z2] badge at the top of the SPM spread phase band."""
    for ann in annotations:
        if isinstance(ann, PhaseAnnotation) and ann.label == '[Z2]':
            if active_annotations is None or '[Z2]' in active_annotations:
                color = (color_overrides or {}).get('[Z2]') or ann.color or COLOR_RHYTHM_SPREAD
                x_mid = (ann.x_start + ann.x_end) / 2
                ax.text(
                    x_mid,
                    ax.get_ylim()[1],
                    '[Z2]',
                    fontsize=7,
                    fontweight='bold',
                    color=color,
                    ha='center',
                    va='top',
                    bbox=dict(boxstyle='round,pad=0.22', facecolor='#FFFFFF', edgecolor=color, linewidth=0.8, alpha=0.90),
                    zorder=12,
                )


def render_rhythm_consistency(
    computed_data: dict[str, Any],
    active_annotations: set[str] | None = None,
    color_overrides: dict[str, str] | None = None,
    return_fig: bool = False,
) -> Figure | None:
    """Render rhythm consistency scatter plot with ideal drive% curve and annotation table.

    Args:
        computed_data: Output from RhythmConsistencyComponent.compute()
        active_annotations: Optional set of toggled annotation labels to display.
        color_overrides: Optional label→hex colour map forwarded to apply_annotations.
                         Pass the same dict given to render_annotation_toggles so
                         on-plot colours and Streamlit badge colours stay in sync.
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
    ideal_spm = np.array(data['ideal_curve_spm'])
    ideal_drive_pct = np.array(data['ideal_curve_drive_pct'])
    mean_spm = data['mean_spm']
    mean_drive_pct = data['mean_drive_pct']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(7, 4),
    )

    # X limits come from the ideal curve range (already padded in the transformer).
    # Y limits span both scatter data and ideal curve with 10% padding.
    x_min = float(ideal_spm.min())
    x_max = float(ideal_spm.max())
    y_min = float(min(drive_pct_vals.min(), ideal_drive_pct.min()))
    y_max = float(max(drive_pct_vals.max(), ideal_drive_pct.max()))
    y_pad = (y_max - y_min) * 0.10
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min - y_pad, y_max + y_pad)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0f}%'))

    # Mean crosshair lines
    if not np.isnan(mean_spm):
        ax.axvline(mean_spm, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            mean_spm,
            0.95,
            'Mean SPM',
            color='#64748b',
            fontsize=8,
            ha='right',
            va='top',
            rotation=90,
            transform=ax.get_xaxis_transform(),
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1),
        )
    if not np.isnan(mean_drive_pct):
        ax.axhline(mean_drive_pct, color='#94a3b8', linewidth=1, linestyle='--', alpha=0.7)
        ax.text(
            0.01,
            mean_drive_pct,
            'Mean Drive%',
            color='#64748b',
            fontsize=8,
            ha='left',
            va='bottom',
            transform=ax.get_yaxis_transform(),
            bbox=dict(facecolor=BG_COLOR_AXES, alpha=0.6, edgecolor='none', pad=1),
        )

    # Raw Scatter points (now primary, along with annotations)
    ax.scatter(spm_vals, drive_pct_vals, color=COLOR_MAIN, s=6, alpha=0.4, zorder=4, label='Strokes')

    # Apply Annotations (drawings only)
    if annotations:
        apply_annotations(ax, annotations, active_labels=active_annotations, color_overrides=color_overrides)

    # Reposition [S1] to the end of the curve furthest from the mean point
    if not np.isnan(mean_spm):
        _reposition_s1_label(ax, ideal_spm, ideal_drive_pct, mean_spm)

    # Draw [Z2] badge at the top of the SPM spread phase band
    _draw_z2_label(ax, annotations, active_annotations, color_overrides)

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(f'**Performance Insight:** {coach_tip}')
        return None

    return fig
