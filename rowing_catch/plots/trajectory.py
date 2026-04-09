"""Handle Trajectory plot renderer.

Renders 2D handle path during stroke cycle.
"""

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import (
    BG_COLOR_AXES,
    COLOR_CATCH,
    COLOR_COMPARE,
    COLOR_FINISH,
    COLOR_MAIN,
)
from rowing_catch.plots.utils import setup_premium_plot


def render_handle_trajectory(computed_data: dict[str, Any]):
    """Render handle trajectory plot.

    Args:
        computed_data: Output from HandleTrajectoryComponent.compute()
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

    # Plot ideal path
    ax.plot(
        data['ideal_x'],
        data['ideal_y'],
        color=COLOR_COMPARE,
        linestyle='--',
        alpha=0.5,
        label='Ideal Path',
        linewidth=1.5,
        zorder=2,
    )
    ax.scatter(
        data['ideal_catch_x'],
        data['ideal_catch_y'],
        color=COLOR_COMPARE,
        s=50,
        alpha=0.5,
        label='Ideal Catch/Finish',
        zorder=2,
    )

    # Plot actual path
    ax.plot(
        data['handle_x'],
        data['handle_y'],
        color=COLOR_MAIN,
        label='Handle Path',
        linewidth=2.5,
        zorder=4,
    )

    # Mark catch and finish
    ax.scatter(
        data['catch_x'],
        data['catch_y'],
        color=COLOR_CATCH,
        s=100,
        label='Catch',
        zorder=5,
    )
    ax.scatter(
        data['finish_x'],
        data['finish_y'],
        color=COLOR_FINISH,
        s=100,
        label='Finish',
        zorder=5,
    )

    ax.invert_yaxis()
    ax.legend(frameon=True, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    st.pyplot(fig)
    st.info(f"**Coach's Tip:** {coach_tip}")


__all__ = ['render_handle_trajectory']
