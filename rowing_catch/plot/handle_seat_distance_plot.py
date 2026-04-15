"""Handle-Seat Distance renderer.

Renders compression distance plot with scenario comparison.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import COLOR_CATCH, COLOR_COMPARE, COLOR_FINISH, COLOR_HANDLE
from rowing_catch.plot.utils import setup_premium_plot


def render_handle_seat_distance(
    computed_data: dict[str, Any],
    return_fig: bool = False,
) -> plt.Figure | None:
    """Render handle-seat distance plot.

    Args:
        computed_data: Output from HandleSeatDistanceComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
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

    # Mark catch and finish
    ax.axvline(data['catch_idx'], color=COLOR_CATCH, linestyle='--', alpha=0.5, zorder=2)
    ax.axvline(data['finish_idx'], color=COLOR_FINISH, linestyle='--', alpha=0.5, zorder=2)

    ax.legend()

    if not return_fig:
        st.pyplot(fig)
        st.info(f'**Developing Advice:** {coach_tip}')
        plt.close(fig)
        return None

    return fig
