"""Power Accumulation renderer.

Renders stacked power curve for legs, trunk, and arms.
"""

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import COLOR_ARMS, COLOR_LEGS, COLOR_TRUNK
from rowing_catch.plots.utils import setup_premium_plot


def render_power_accumulation(computed_data: dict[str, Any]):
    """Render power accumulation stacked area plot.

    Args:
        computed_data: Output from PowerAccumulationComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data.get('has_data', True):
        st.warning(coach_tip)
        return

    fig, ax = setup_premium_plot(metadata['title'], metadata['x_label'], metadata['y_label'])

    drive_progress = data['drive_progress']
    p_legs = data['power_legs']
    p_trunk = data['power_trunk']
    p_arms = data['power_arms']

    ax.stackplot(
        drive_progress,
        p_legs,
        p_trunk,
        p_arms,
        labels=['Legs', 'Trunk', 'Arms'],
        colors=[COLOR_LEGS, COLOR_TRUNK, COLOR_ARMS],
        alpha=0.8,
    )

    # Optional scenario overlay
    if data['scenario_power_total'] is not None:
        ax.plot(
            data['scenario_progress'],
            data['scenario_power_total'],
            color='#333333',
            linestyle='--',
            linewidth=1.5,
            label=f'Comparison: {metadata["scenario_name"]}',
            alpha=0.6,
        )

    ax.legend(loc='upper right')

    st.pyplot(fig)
    st.info(f'**Performance Insight:** {coach_tip}')
