"""Jerk Comparison renderer.

Renders per-segment jerk subplots vs system jerk baseline.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plots.theme import BG_COLOR_AXES, BG_COLOR_FIGURE, COLOR_CATCH, COLOR_FINISH, COLOR_TEXT_SUB
from rowing_catch.plots.utils import setup_premium_plot  # noqa: F401 — imported for style consistency


def render_jerk_comparison(computed_data: dict[str, Any]) -> None:
    """Render jerk comparison subplots.

    Args:
        computed_data: Output from JerkComparisonComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    panels = data['panels']
    if not panels:
        st.warning('No jerk data available.')
        st.info(coach_tip)
        return

    index = data['index']
    rower_jerk = data['rower_jerk']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']

    n_plots = len(panels)
    fig, axes = plt.subplots(n_plots, 1, figsize=(10, 2.5 * n_plots), sharex=True, sharey=True)
    if n_plots == 1:
        axes = [axes]

    fig.patch.set_facecolor(BG_COLOR_FIGURE)

    for ax, panel in zip(axes, panels, strict=False):
        if data['has_rower_jerk']:
            ax.plot(
                index,
                rower_jerk,
                color='#777777',
                linewidth=1.2,
                linestyle='--',
                label='System Jerk',
                alpha=0.7,
                zorder=1,
            )
        ax.plot(
            index,
            panel['jerk'],
            color=panel['color'],
            linewidth=1.5,
            linestyle='-',
            label=f'{panel["label"]} Jerk',
            zorder=2,
        )

        ax.set_facecolor(BG_COLOR_AXES)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#DDDDDD')
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.grid(axis='y', linestyle='-', linewidth=0.5, color='#F0F0F0', zorder=0)
        ax.set_ylabel(metadata['y_label'], fontweight='bold', color=COLOR_TEXT_SUB, fontsize=8)
        ax.axhline(0, color='#888888', linestyle='-', linewidth=0.5, alpha=0.3)
        ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2, alpha=0.5)
        ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2, alpha=0.5)
        ax.legend(fontsize=7, loc='upper right', framealpha=0.9, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')

    axes[-1].set_xlabel(metadata['x_label'], fontweight='bold', color=COLOR_TEXT_SUB)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.info(coach_tip)
