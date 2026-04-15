"""Debug Power Curve renderer.

Renders the V³ power curve breakdown across the drive phase.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_ARMS, COLOR_CATCH, COLOR_FINISH, COLOR_HANDLE, COLOR_SEAT
from rowing_catch.plot.utils import setup_premium_plot


def render_debug_power_curve(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render power curve breakdown.

    Args:
        computed_data: Output from DebugPowerCurveComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    x = data['x']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(10, 3.5),
    )

    if x:
        ax.fill_between(x, data['total_clipped'], color=COLOR_FINISH, alpha=0.12, label='_nolegend_')
        ax.plot(x, data['total_raw'], color=COLOR_FINISH, linewidth=2, label='Total')
        if data['has_legs']:
            ax.plot(x, data['legs'], color=COLOR_SEAT, linewidth=1.2, linestyle='--', label='Legs')
        if data['has_trunk']:
            ax.plot(x, data['trunk'], color=COLOR_ARMS, linewidth=1.2, linestyle='-.', label='Trunk')
        if data['has_arms']:
            ax.plot(x, data['arms'], color=COLOR_HANDLE, linewidth=1, linestyle=':', label='Arms')

    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2, alpha=0.6)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2, alpha=0.6)
    ax.legend(fontsize=8, loc='upper left', facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
