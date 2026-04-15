"""Avg Cycle Trunk Angle renderer.

Renders trunk angle across the averaged stroke with catch/finish annotations.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_CATCH, COLOR_FINISH, COLOR_MAIN
from rowing_catch.plot.utils import setup_premium_plot


def render_avg_cycle_trunk_angle(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render trunk angle plot.

    Args:
        computed_data: Output from AvgCycleTrunkAngleComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    index = data['index']
    trunk = data['trunk']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']
    catch_angle = data['catch_angle']
    finish_angle = data['finish_angle']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(10, 3),
    )

    ax.plot(index, trunk, color=COLOR_MAIN, linewidth=2, label='Trunk Angle')
    ax.fill_between(index, trunk, 0, color=COLOR_MAIN, alpha=0.08)
    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)

    # Catch annotation
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.5, alpha=0.8)
    ax.annotate(
        f'Catch ({catch_angle:.1f}°) ',
        xy=(catch_idx, catch_angle),
        xytext=(catch_idx, catch_angle - 2),
        color=COLOR_CATCH,
        fontsize=8,
        fontweight='bold',
        va='center',
        ha='right',
    )

    # Finish annotation
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.5, alpha=0.8)
    ax.annotate(
        f' Finish ({finish_angle:.1f}°)',
        xy=(finish_idx, finish_angle),
        xytext=(finish_idx + 2, finish_angle),
        color=COLOR_FINISH,
        fontsize=8,
        fontweight='bold',
        va='center',
        ha='left',
    )

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
