"""Handle-Seat Distance renderer.

Renders compression distance plot with scenario comparison and phase annotations.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import COLOR_CATCH, COLOR_COMPARE, COLOR_FINISH, COLOR_HANDLE
from rowing_catch.plot.utils import apply_annotations, setup_premium_plot
from rowing_catch.plot_transformer.annotations import PhaseAnnotation


def render_handle_seat_distance(
    computed_data: dict[str, Any],
    active_annotations: set[str] | None = None,
    color_overrides: dict[str, str] | None = None,
    return_fig: bool = False,
) -> plt.Figure | None:
    """Render handle-seat distance plot.

    Args:
        computed_data: Output from HandleSeatDistanceComponent.compute()
        active_annotations: Set of annotation labels to show. None = show all.
        color_overrides: Optional label→hex colour map for annotation colours.
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']
    annotations = computed_data.get('annotations', [])

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
    )

    # Grey per-cycle distance overlays — behind main trace
    for cyc_dist in computed_data['data'].get('cycle_distances', []):
        ax.plot(data['x'][: len(cyc_dist)], cyc_dist, color='#AAAAAA', linewidth=0.8, alpha=0.15, zorder=1)

    # Main plot
    ax.plot(data['x'], data['distance'], color=COLOR_HANDLE, linewidth=2.5, label='Distance', zorder=5)
    ax.fill_between(data['x'], data['distance'], color=COLOR_HANDLE, alpha=0.1, zorder=4)

    # Scenario comparison if available
    if data['scenario_distance'] is not None:
        ax.plot(
            data['x'],
            data['scenario_distance'],
            color=COLOR_COMPARE,
            linestyle=':',
            alpha=0.5,
            label=f'Comparison: {metadata["scenario_name"]}',
            zorder=3,
        )

    # Apply annotations (phases, points, segments)
    apply_annotations(ax, annotations, active_labels=active_annotations, color_overrides=color_overrides)

    # Phase region text labels — rendered directly so they appear inside the shaded spans
    y_min, y_max = ax.get_ylim()
    y_label_pos = y_min + (y_max - y_min) * 0.06
    _phase_labels = {
        '[Ph1]': 'Drive Phase',
        '[Ph2]': 'Intra-Stroke\nCompression',
        '[Ph3]': 'Recovery',
    }
    for ann in annotations:
        if not isinstance(ann, PhaseAnnotation):
            continue
        if active_annotations is not None and ann.label not in active_annotations:
            continue
        label_text = _phase_labels.get(ann.label)
        if label_text:
            mid_x = (ann.x_start + ann.x_end) / 2
            ax.text(
                mid_x,
                y_label_pos,
                label_text,
                ha='center',
                va='bottom',
                fontsize=8,
                color='#666666',
                fontstyle='italic',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.7, pad=1.0),
                zorder=8,
            )

    # Mark catch and finish lines
    ax.axvline(data['catch_idx'], color=COLOR_CATCH, linestyle='--', linewidth=1.5, zorder=2)
    ax.axvline(data['finish_idx'], color=COLOR_FINISH, linestyle='--', linewidth=1.5, zorder=2)

    y_min, y_max = ax.get_ylim()
    y_top = y_max - (y_max - y_min) * 0.05

    ax.text(
        data['catch_idx'],
        y_top,
        'Catch',
        color=COLOR_CATCH,
        ha='center',
        va='top',
        fontsize=10,
        fontweight='bold',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5),
        zorder=6,
    )
    ax.text(
        data['finish_idx'],
        y_min,
        'Finish',
        color=COLOR_FINISH,
        ha='center',
        va='top',
        fontsize=10,
        fontweight='bold',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5),
        zorder=6,
    )

    ax.legend()

    if not return_fig:
        st.pyplot(fig)
        st.info(f'**Developing Advice:** {coach_tip}')
        plt.close(fig)
        return None

    return fig
