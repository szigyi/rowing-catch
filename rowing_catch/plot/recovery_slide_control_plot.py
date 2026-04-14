"""Recovery Slide Control renderer.

Renders seat velocity during recovery phase.
"""

from typing import Any

import matplotlib.figure
import streamlit as st

from rowing_catch.plot.theme import COLOR_SEAT
from rowing_catch.plot.utils import setup_premium_plot


def render_recovery_slide_control(
    computed_data: dict[str, Any],
    return_fig: bool = False,
) -> matplotlib.figure.Figure | None:
    """Render recovery slide control plot.

    Args:
        computed_data: Output from RecoverySlideControlComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data.get('has_data', True):
        st.warning('Insufficient data for recovery control analysis.')
        return None

    fig, ax = setup_premium_plot(title=metadata['title'], figsize=(10, 6.4))

    recovery_progress = data['recovery_progress']
    seat_speed = data['seat_speed']

    # Main plot: seat velocity during recovery
    ax.plot(recovery_progress, seat_speed, color=COLOR_SEAT, linewidth=2.5, label='Seat Velocity')
    ax.fill_between(recovery_progress, seat_speed, alpha=0.3, color=COLOR_SEAT)

    # Labels and formatting
    ax.set_xlabel(metadata['x_label'], fontsize=11)
    ax.set_ylabel(metadata['y_label'], fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='best', framealpha=0.95)

    st.pyplot(fig)
    st.info(f'**Performance Insight:** {coach_tip}')

    if return_fig:
        return fig
    return None
