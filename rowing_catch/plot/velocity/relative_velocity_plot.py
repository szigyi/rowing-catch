"""Relative Velocity renderer.

Renders Handle and Shoulder velocity relative to Seat across the averaged stroke.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_ARMS, COLOR_CATCH, COLOR_FINISH, COLOR_HANDLE
from rowing_catch.plot.utils import setup_premium_plot


def render_relative_velocity(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render relative velocity plot.

    Args:
        computed_data: Output from RelativeVelocityComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    index = data['index']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(10, 3.5),
    )

    ax.plot(index, data['handle_rel'], color=COLOR_HANDLE, linewidth=1.5, label='Handle - Seat')
    ax.fill_between(index, data['handle_rel'], 0, color=COLOR_HANDLE, alpha=0.08)

    if data['has_shoulder']:
        ax.plot(index, data['shoulder_rel'], color=COLOR_ARMS, linewidth=1.5, label='Shoulder - Seat')

    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
