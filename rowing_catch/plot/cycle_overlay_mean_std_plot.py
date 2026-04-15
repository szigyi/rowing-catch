"""Cycle Overlay Mean Std renderer.

Renders individual stroke cycles overlaid with mean and ±1 SD band.
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_MAIN
from rowing_catch.plot.utils import setup_premium_plot


def render_cycle_overlay_mean_std(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render cycle overlay with mean and SD band.

    Args:
        computed_data: Output from CycleOverlayMeanStdComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data['cycle_arrays']:
        st.warning('No cycle data available.')
        return None

    x_idx = np.array(data['x_idx'])
    mean_vals = np.array(data['mean_vals'])
    std_vals = np.array(data['std_vals'])

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(5, 3),
    )

    for arr in data['cycle_arrays']:
        ax.plot(x_idx, arr, color='#cbd5e1', linewidth=0.8, alpha=0.4)

    ax.fill_between(x_idx, mean_vals - std_vals, mean_vals + std_vals, color=COLOR_MAIN, alpha=0.15, label='±1 SD')
    ax.plot(x_idx, mean_vals, color=COLOR_MAIN, linewidth=2, label='Mean cycle')
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    if not return_fig:
        st.pyplot(fig, width='stretch')
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
