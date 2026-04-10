"""Trunk Angle Separation renderer.

Renders trunk angle vs seat position plot with scenario comparison.
"""

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import COLOR_CATCH, COLOR_COMPARE, COLOR_FINISH, COLOR_TRUNK
from rowing_catch.plots.utils import setup_premium_plot


def render_trunk_angle_separation(computed_data: dict[str, Any]):
    """Render trunk angle separation plot.

    Args:
        computed_data: Output from TrunkAngleSeparationComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
    )

    # Main plot
    ax.plot(data['seat_position'], data['trunk_angle_plot'], color=COLOR_TRUNK, linewidth=3, label='Your Data', zorder=5)

    # Mark catch and finish
    ax.scatter(data['catch_seat'], data['catch_angle'], color=COLOR_CATCH, s=100, label='Catch', zorder=6)
    ax.scatter(data['finish_seat'], data['finish_angle'], color=COLOR_FINISH, s=100, label='Finish', zorder=6)

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

    ax.legend()
    st.pyplot(fig)
    st.info(f'**Developing Advice:** {coach_tip}')
