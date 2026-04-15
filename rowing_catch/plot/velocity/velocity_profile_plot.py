"""Velocity Profile renderer.

Renders Handle, Seat, Shoulder and Rower velocity across the averaged stroke.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_CATCH, COLOR_FINISH, MAIN_COLORS
from rowing_catch.plot.utils import setup_premium_plot


def render_velocity_profile(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render velocity profile plot.

    Args:
        computed_data: Output from VelocityProfileComponent.compute()
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

    ax.plot(index, data['handle_vel'], color=MAIN_COLORS[0], linewidth=1.5, label='Handle')
    ax.fill_between(index, data['handle_vel'], 0, color=MAIN_COLORS[0], alpha=0.08)
    ax.plot(index, data['seat_vel'], color=MAIN_COLORS[1], linewidth=1.5, label='Seat')
    ax.fill_between(index, data['seat_vel'], 0, color=MAIN_COLORS[1], alpha=0.08)

    if data['has_shoulder']:
        ax.plot(index, data['shoulder_vel'], color=MAIN_COLORS[2], linewidth=1.2, linestyle='--', label='Shoulder')
        if data['rower_vel']:
            ax.plot(index, data['rower_vel'], color=MAIN_COLORS[3], linewidth=2, label='Torso (Seat/Shoulder Avg)')

    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
    ax.legend(fontsize=8, loc='upper right', facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
