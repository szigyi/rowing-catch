"""Drive Recovery Balance renderer.

Renders a stacked horizontal bar showing drive vs recovery split with ideal drive% reference.
"""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, BG_COLOR_FIGURE, COLOR_CATCH, COLOR_IDEAL_RATIO, COLOR_MAIN, COLOR_TEXT_SUB


def render_drive_recovery_balance(computed_data: dict[str, Any], return_fig: bool = False) -> plt.Figure | None:
    """Render drive vs recovery stacked bar.

    Args:
        computed_data: Output from DriveRecoveryBalanceComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure.
    """
    data = computed_data['data']
    coach_tip = computed_data['coach_tip']

    drive_pct = data['drive_pct']
    rec_pct = data['rec_pct']
    mean_spm = data['mean_spm']
    ideal_drive_pct = data['ideal_drive_pct']

    fig, ax = plt.subplots(figsize=(6, 1.5))
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)

    h = 0.5
    ax.barh(['Drive %'], [drive_pct], color=COLOR_MAIN, height=h, label='Drive')
    ax.barh(['Drive %'], [rec_pct], left=[drive_pct], color=COLOR_CATCH, height=h, label='Recovery')

    ax.text(drive_pct / 2, 0, f'Drive\n{drive_pct:.1f}%', ha='center', va='center', color='white', fontweight='bold', fontsize=9)
    ax.text(
        drive_pct + rec_pct / 2,
        0,
        f'Recovery\n{rec_pct:.1f}%',
        ha='center',
        va='center',
        color='white',
        fontweight='bold',
        fontsize=9,
    )

    ax.axvline(ideal_drive_pct, color=COLOR_IDEAL_RATIO, linestyle=':', linewidth=2.5, alpha=0.8, zorder=3)
    if not np.isnan(mean_spm):
        label = f' Ideal ({ideal_drive_pct:.1f}%) @ {mean_spm:.0f} SPM'
    else:
        label = f' Ideal ({ideal_drive_pct:.1f}%)'
    ax.text(ideal_drive_pct, 0.4, label, color=COLOR_IDEAL_RATIO, fontsize=8, fontweight='bold', va='bottom')

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 33.3, 50, 75, 100])
    ax.set_xticklabels(['0%', '25%', '33%', '50%', '75%', '100%'], fontsize=8)
    ax.tick_params(axis='y', which='both', left=False, labelleft=False)
    ax.tick_params(axis='x', colors=COLOR_TEXT_SUB)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDDD')

    if not return_fig:
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)
        st.info(coach_tip)
        return None

    return fig
