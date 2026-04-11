"""Kinetic Chain Coordination renderer.

Renders velocity and acceleration coordination with dual-axis plot.
"""

from typing import Any

import streamlit as st

from rowing_catch.plot.theme import COLOR_CATCH, COLOR_FINISH, MAIN_COLORS
from rowing_catch.plot.utils import setup_premium_plot


def render_kinetic_chain(computed_data: dict[str, Any]):
    """Render kinetic chain coordination plot.

    Args:
        computed_data: Output from KineticChainComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    fig, ax = setup_premium_plot(metadata['title'], metadata['x_label'], metadata['y_label'])

    stroke_index = data['stroke_index']
    handle_x_vel = data['handle_x_vel']
    seat_x_vel = data['seat_x_vel']
    handle_x_accel = data['handle_x_accel']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']

    # Main axis: velocities — use MAIN_COLORS palette in order
    ax.plot(stroke_index, handle_x_vel, color=MAIN_COLORS[0], label='Handle Vel', linewidth=2.5)
    ax.plot(stroke_index, seat_x_vel, color=MAIN_COLORS[1], label='Seat Vel', linewidth=2)

    # Secondary axis for Acceleration
    ax2 = ax.twinx()
    ax2.plot(stroke_index, handle_x_accel, color='#EB55DE', linestyle=':', alpha=0.4, label='Handle Accel')
    ax2.set_ylabel('Acceleration', color='#EB55DE', alpha=0.7)
    ax2.spines['right'].set_visible(True)
    ax2.spines['right'].set_color('#EB55DE')

    # Mark catch and finish
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', alpha=0.3)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', alpha=0.3)

    ax.legend(loc='upper left')

    st.pyplot(fig)
    st.info(f'**Performance Insight:** {coach_tip}')
