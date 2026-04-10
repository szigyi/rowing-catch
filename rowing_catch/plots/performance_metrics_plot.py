"""Performance Metrics renderer.

Renders jerk analysis and handle height stability metrics.
"""

from typing import Any

import streamlit as st

from rowing_catch.plots.theme import COLOR_CATCH, COLOR_HANDLE
from rowing_catch.plots.utils import setup_premium_plot


def render_performance_metrics(computed_data: dict[str, Any]):
    """Render performance metrics plots (jerk + handle height stability).

    Args:
        computed_data: Output from PerformanceMetricsComponent.compute()
    """
    data = computed_data['data']
    coach_tip = computed_data['coach_tip']

    col1, col2 = st.columns(2)

    # Left column: Handle Jerk
    with col1:
        st.write('#### Handle Jerk (Smoothness)')
        fig, ax = setup_premium_plot(y_label='Jerk (mm/s³)', figsize=(5, 4))
        ax.plot(data['stroke_index'], data['jerk'], color='#FF4B4B', linewidth=1.5)
        ax.axvline(data['catch_idx'], color=COLOR_CATCH, alpha=0.3)
        st.pyplot(fig)

    # Right column: Handle Height Stability
    with col2:
        st.write('#### Handle Height Stability')
        fig, ax = setup_premium_plot(y_label='Handle Y (mm)', figsize=(5, 4))
        # Boxplot of drive phase handle height
        ax.boxplot(data['drive_y'], patch_artist=True, boxprops=dict(facecolor=COLOR_HANDLE, alpha=0.5))
        ax.set_xticks([])
        st.pyplot(fig)

    st.info(f'**High Performance:** {coach_tip}')
