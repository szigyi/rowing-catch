"""Velocity Profile renderer.

Renders Handle, Seat, Shoulder and Rower velocity across the averaged stroke.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plots.theme import BG_COLOR_AXES, COLOR_ARMS, COLOR_CATCH, COLOR_FINISH, COLOR_HANDLE, COLOR_MAIN, COLOR_SEAT
from rowing_catch.plots.utils import setup_premium_plot


def render_velocity_profile(computed_data: dict[str, Any]) -> None:
    """Render velocity profile plot.

    Args:
        computed_data: Output from VelocityProfileComponent.compute()
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

    ax.plot(index, data['handle_vel'], color=COLOR_HANDLE, linewidth=1.5, label='Handle')
    ax.fill_between(index, data['handle_vel'], 0, color=COLOR_HANDLE, alpha=0.08)
    ax.plot(index, data['seat_vel'], color=COLOR_SEAT, linewidth=1.5, label='Seat')
    ax.fill_between(index, data['seat_vel'], 0, color=COLOR_SEAT, alpha=0.08)

    if data['has_shoulder']:
        ax.plot(index, data['shoulder_vel'], color=COLOR_ARMS, linewidth=1.2, linestyle='--', label='Shoulder')
        if data['rower_vel']:
            ax.plot(index, data['rower_vel'], color=COLOR_MAIN, linewidth=2, label='Torso (Seat/Shoulder Avg)')

    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
    ax.legend(fontsize=8, loc='upper right', facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.info(coach_tip)
