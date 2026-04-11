"""Trunk Angle Separation renderer.

Renders trunk angle vs seat position plot with scenario comparison.
"""

from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import (
    BG_COLOR_FIGURE,
    COLOR_CATCH,
    COLOR_COMPARE,
    COLOR_FINISH,
    COLOR_TRUNK,
    SPINE_COLOR,
)
from rowing_catch.plot.utils import apply_annotations, render_annotation_legend_on_figure
from rowing_catch.plot_transformer.annotations import assign_annotation_colors


def render_trunk_angle_separation(
    computed_data: dict[str, Any],
    active_annotations: set[str] | None = None,
    return_fig: bool = False,
) -> matplotlib.figure.Figure | None:
    """Render trunk angle separation plot.

    Args:
        computed_data: Output from TrunkAngleSeparationComponent.compute()
        active_annotations: Set of annotation labels to show. None means show all.
                            Empty set means hide all.
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.

    Returns:
        matplotlib Figure if return_fig=True, else None.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']
    annotations = computed_data.get('annotations', [])

    # Pre-count active annotation rows for dynamic legend sizing
    _auto = assign_annotation_colors(list(annotations))
    if active_annotations is not None:
        _visible = [a for a in _auto if a.label in active_annotations]
    else:
        _visible = _auto
    n_legend_rows = len(_visible)

    # Build figure with GridSpec: [main plot, legend]
    legend_ratio = max(0.35 * n_legend_rows, 0.0)
    fig = plt.figure(figsize=(10, 5 + legend_ratio * 0.5), constrained_layout=True)
    gs = fig.add_gridspec(
        2,
        1,
        height_ratios=[4, legend_ratio] if n_legend_rows > 0 else [4, 0.001],
    )
    ax = fig.add_subplot(gs[0])
    ax_legend = fig.add_subplot(gs[1])

    # Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor('#FFFFFF')
    ax_legend.set_facecolor(BG_COLOR_FIGURE)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(SPINE_COLOR)
    ax.spines['bottom'].set_color(SPINE_COLOR)
    ax.grid(axis='y', linestyle='-', linewidth=0.5, color='#F0F0F0', zorder=0)

    # Main trace
    ax.plot(
        data['seat_position'],
        data['trunk_angle_plot'],
        color=COLOR_TRUNK,
        linewidth=3,
        label='Trunk Angle',
        zorder=5,
    )

    # Mark catch and finish scatter dots (no legend entry — labelled directly on the plot)
    ax.scatter(data['catch_seat'], data['catch_angle'], color=COLOR_CATCH, s=100, zorder=6)
    ax.scatter(data['finish_seat'], data['finish_angle'], color=COLOR_FINISH, s=100, zorder=6)

    # Inline labels next to catch / finish dots
    _y_span = ax.get_ylim()[1] - ax.get_ylim()[0]
    _y_nudge = _y_span * 0.04
    ax.text(
        data['catch_seat'],
        data['catch_angle'] + _y_nudge,
        'Catch',
        color=COLOR_CATCH,
        fontsize=9,
        fontweight='bold',
        ha='center',
        va='bottom',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.85, pad=1.2),
        zorder=7,
    )
    ax.text(
        data['finish_seat'],
        data['finish_angle'] + _y_nudge,
        'Finish',
        color=COLOR_FINISH,
        fontsize=9,
        fontweight='bold',
        ha='center',
        va='bottom',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.85, pad=1.2),
        zorder=7,
    )

    # Scenario comparison if available
    if data['scenario_seat'] is not None:
        ax.plot(
            data['scenario_seat'],
            data['scenario_angle'],
            color=COLOR_COMPARE,
            linestyle='--',
            alpha=0.7,
            label=f'Comparison: {metadata["scenario_name"]}',
            zorder=4,
        )

    ax.set_xlabel(metadata['x_label'], color='#444444', fontweight='bold', labelpad=10)
    ax.set_ylabel(metadata['y_label'], color='#444444', fontweight='bold', labelpad=10)
    ax.set_title(metadata['title'], fontsize=14, fontweight='bold', color='#444444', pad=16)
    ax.tick_params(colors='#666666')
    ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor=SPINE_COLOR, fontsize=9)

    # Apply annotations and build legend
    # Zone color overrides: catch point uses green, finish uses red
    _zone_overrides = {
        '[P1]': COLOR_CATCH,
        '[P2]': COLOR_FINISH,
    }
    legend_items = apply_annotations(
        ax,
        annotations,
        active_labels=active_annotations,
        axis_id='main',
        color_overrides=_zone_overrides,
    )

    if legend_items:
        import dataclasses as _dc

        _auto_colored = assign_annotation_colors(list(annotations))
        _with_overrides = [
            _dc.replace(a, color=_zone_overrides[a.label]) if a.label in _zone_overrides else a for a in _auto_colored
        ]
        _vis = [a for a in _with_overrides if active_annotations is None or a.label in active_annotations]
        legend_colors = [a.color or '#555555' for a in _vis]
        render_annotation_legend_on_figure(fig, ax_legend, legend_items, colors=legend_colors)
    else:
        ax_legend.axis('off')

    if return_fig:
        return fig

    st.pyplot(fig)
    st.info(f'**Developing Advice:** {coach_tip}')
    return None
