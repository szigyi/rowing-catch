"""Velocity Coordination plot renderer.

Renders handle vs. seat velocity traces.
"""

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import (
    BG_COLOR_AXES,
    COLOR_CATCH,
    COLOR_FINISH,
    COLOR_MAIN,
    COLOR_SEAT,
)
from rowing_catch.plots.utils import setup_premium_plot


def render_velocity_coordination(computed_data: dict[str, Any]):
    """Render velocity coordination plot.

    Args:
        computed_data: Output from VelocityCoordinationComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    # Create plot
    fig, ax = setup_premium_plot(
        title=metadata['title'],
        xlabel=metadata['xlabel'],
        ylabel=metadata['ylabel'],
    )

    # Plot data
    ax.plot(
        data['x'],
        data['handle_vel'],
        label='Handle Velocity',
        color=COLOR_MAIN,
        linewidth=2.5,
        zorder=5,
    )
    ax.fill_between(
        data['x'],
        data['handle_vel'],
        0,
        color=COLOR_MAIN,
        alpha=0.1,
        zorder=4,
    )

    ax.plot(
        data['x'],
        data['seat_vel'],
        label='Seat Velocity',
        color=COLOR_SEAT,
        linewidth=2.5,
        zorder=5,
    )
    ax.fill_between(
        data['x'],
        data['seat_vel'],
        0,
        color=COLOR_SEAT,
        alpha=0.1,
        zorder=4,
    )

    # Mark catch and finish
    ax.axvline(data['catch_idx'], color=COLOR_CATCH, linestyle='--', linewidth=1.5, zorder=2)
    ax.axvline(data['finish_idx'], color=COLOR_FINISH, linestyle='--', linewidth=1.5, zorder=2)

    ax.legend(frameon=True, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    st.pyplot(fig)
    st.info(f"**Coach's Tip:** {coach_tip}")


__all__ = ['render_velocity_coordination']
