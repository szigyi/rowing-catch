"""Production Finish Trajectory renderer.

Renders full trajectory with catch and production-heuristic finish markers.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plots.theme import BG_COLOR_AXES, COLOR_CATCH, COLOR_FINISH, COLOR_SEAT
from rowing_catch.plots.utils import setup_premium_plot


def render_production_finish_trajectory(computed_data: dict[str, Any]) -> None:
    """Render full trajectory with production finish detection.

    Args:
        computed_data: Output from ProductionFinishTrajectoryComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data['index']:
        st.warning('Insufficient data to display full trajectory.')
        st.info(coach_tip)
        return

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(10, 3.5),
    )

    ax.plot(data['index'], data['seat_smooth'], color=COLOR_SEAT, linewidth=1.5, label='Smoothed Seat_X')

    for ci in data['catch_indices']:
        ax.axvline(ci, color=COLOR_CATCH, linewidth=1, linestyle='--', alpha=0.7)

    ax.scatter(data['catch_indices'], data['catch_values'], color=COLOR_CATCH, s=50, zorder=5, label='Catch')
    ax.scatter(data['finish_indices'], data['finish_values'], color=COLOR_FINISH, marker='X', s=60, zorder=5, label='Finish')

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.info(coach_tip)
