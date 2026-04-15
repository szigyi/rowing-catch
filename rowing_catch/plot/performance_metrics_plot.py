"""Performance Metrics renderer.

Renders jerk analysis and handle height stability metrics.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import COLOR_CATCH, COLOR_HANDLE
from rowing_catch.plot.utils import setup_premium_plot


def render_performance_metrics(computed_data: dict[str, Any], return_fig: bool = False) -> list[plt.Figure] | None:
    """Render performance metrics plots (jerk + handle height stability).

    Args:
        computed_data: Output from PerformanceMetricsComponent.compute()
        return_fig: If True, skip st.pyplot() and return a list of Figures.
    """
    data = computed_data['data']
    coach_tip = computed_data['coach_tip']

    col1, col2 = st.columns(2)

    # Left column: Handle Jerk
    fig_jerk, ax_jerk = setup_premium_plot(y_label='Jerk (mm/s³)', figsize=(5, 4))
    ax_jerk.plot(data['stroke_index'], data['jerk'], color='#FF4B4B', linewidth=1.5)
    ax_jerk.axvline(data['catch_idx'], color=COLOR_CATCH, alpha=0.3)

    # Right column: Handle Height Stability
    fig_height, ax_height = setup_premium_plot(y_label='Handle Y (mm)', figsize=(5, 4))
    # Boxplot of drive phase handle height
    ax_height.boxplot(data['drive_y'], patch_artist=True, boxprops=dict(facecolor=COLOR_HANDLE, alpha=0.5))
    ax_height.set_xticks([])

    if not return_fig:
        with col1:
            st.write('#### Handle Jerk (Smoothness)')
            st.pyplot(fig_jerk)
            plt.close(fig_jerk)
        with col2:
            st.write('#### Handle Height Stability')
            st.pyplot(fig_height)
            plt.close(fig_height)
        st.info(f'**High Performance:** {coach_tip}')
        return None

    return [fig_jerk, fig_height]
