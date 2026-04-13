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
from rowing_catch.plot.utils import apply_annotations


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

    Note:
        The annotation reference table (Ref | Description | Coach Tip) is rendered
        by the page layer as a Streamlit widget — not baked into the figure.
        On PDF export the on-plot markers (backdrops, callouts) are still included;
        the page layer is responsible for appending a separate legend page if needed.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']
    annotations = computed_data.get('annotations', [])

    fig, ax = plt.subplots(figsize=(10, 5))

    # Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor('#FFFFFF')

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

    # Apply on-plot annotation markers (backdrops, callout arrows).
    # The legend table is rendered by the page layer, not here.
    _zone_overrides = {
        '[P1]': COLOR_CATCH,
        '[P2]': COLOR_FINISH,
        '[Z1]': COLOR_CATCH,
        '[Z2]': COLOR_FINISH,
    }
    apply_annotations(
        ax,
        annotations,
        active_labels=active_annotations,
        axis_id='main',
        color_overrides=_zone_overrides,
    )

    if return_fig:
        return fig

    st.pyplot(fig)
    st.info(f'**Developing Advice:** {coach_tip}')
    return None
