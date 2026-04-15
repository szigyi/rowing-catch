"""Signal Smoothing Comparison renderer.

Renders side-by-side before/after smoothing plots for Seat_X and Handle_X.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_COMPARE, COLOR_HANDLE, COLOR_SEAT
from rowing_catch.plot.utils import setup_premium_plot


def render_signal_smoothing_comparison(computed_data: dict[str, Any], return_fig: bool = False) -> list[plt.Figure] | None:
    """Render signal smoothing comparison.

    Args:
        computed_data: Output from SignalSmoothingComparisonComponent.compute()
        return_fig: If True, skip st.pyplot() and return a list of Figures.
    """
    data = computed_data['data']
    coach_tip = computed_data['coach_tip']

    # Seat_X figure
    fig_seat, ax_seat = setup_premium_plot(x_label='Sample index', y_label='Seat_X', figsize=(5, 2.5))
    ax_seat.plot(data['index_raw'], data['seat_raw'], color=COLOR_COMPARE, linewidth=0.8, label='Raw')
    ax_seat.plot(data['index_smooth'], data['seat_smooth'], color=COLOR_SEAT, linewidth=1.5, label='Smoothed')
    ax_seat.legend(fontsize=8, facecolor=BG_COLOR_AXES)

    # Handle_X figure
    fig_handle, ax_handle = setup_premium_plot(x_label='Sample index', y_label='Handle_X', figsize=(5, 2.5))
    ax_handle.plot(data['index_raw'], data['handle_raw'], color=COLOR_COMPARE, linewidth=0.8, label='Raw')
    ax_handle.plot(data['index_smooth'], data['handle_smooth'], color=COLOR_HANDLE, linewidth=1.5, label='Smoothed')
    ax_handle.legend(fontsize=8, facecolor=BG_COLOR_AXES)

    if not return_fig:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown('**Before vs. after — `Seat_X`:**')
            st.pyplot(fig_seat, width='stretch')
            plt.close(fig_seat)
        with col_right:
            st.markdown('**Before vs. after — `Handle_X`:**')
            st.pyplot(fig_handle, width='stretch')
            plt.close(fig_handle)
        st.info(coach_tip)
        return None

    return [fig_seat, fig_handle]
