"""Avg Cycle Multi-Axis Events renderer.

Renders Seat, Handle, and Shoulder position on the averaged stroke with catch/finish markers.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.theme import (
    BG_COLOR_AXES,
    BG_COLOR_FIGURE,
    COLOR_ARMS,
    COLOR_CATCH,
    COLOR_FINISH,
    COLOR_HANDLE,
    COLOR_SEAT,
)
from rowing_catch.plot.utils import setup_premium_plot


def render_avg_cycle_multi_axis(computed_data: dict[str, Any]) -> None:
    """Render multi-axis averaged cycle plot.

    Args:
        computed_data: Output from AvgCycleMultiAxisComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    index = data['index']
    seat = data['seat']
    handle = data['handle']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']
    catch_seat_y = data['catch_seat_y']
    finish_seat_y = data['finish_seat_y']
    seat_min = data['seat_min']
    seat_max = data['seat_max']
    x_end = data['x_end']
    n = data['n']

    fig, ax1 = setup_premium_plot(
        title=metadata['title'],
        x_label=metadata['x_label'],
        y_label=metadata['y_label'],
        figsize=(9, 5),
    )
    fig.patch.set_facecolor(BG_COLOR_FIGURE)

    ax1.plot(index, seat, color=COLOR_SEAT, linewidth=2, label='Seat_X_Smooth')
    ax1.set_ylabel('Seat X (mm)', color=COLOR_SEAT)
    ax1.tick_params(axis='y', labelcolor=COLOR_SEAT)
    if data['seat_bounds']:
        ax1.set_ylim(*data['seat_bounds'])
    ax1.invert_yaxis()

    ax2 = ax1.twinx()
    ax2.plot(index, handle, color=COLOR_HANDLE, linewidth=1.5, linestyle='--', label='Handle_X_Smooth')
    ax2.set_ylabel('Handle X (mm)', color=COLOR_HANDLE)
    ax2.tick_params(axis='y', labelcolor=COLOR_HANDLE)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color('#DDDDDD')
    if data['handle_bounds']:
        ax2.set_ylim(*data['handle_bounds'])
    ax2.invert_yaxis()

    if data['has_shoulder']:
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('outward', 60))
        ax3.spines['right'].set_color('#DDDDDD')
        ax3.spines['top'].set_visible(False)
        ax3.plot(index, data['shoulder'], color=COLOR_ARMS, linewidth=1.5, linestyle='-.', label='Shoulder_X_Smooth')
        ax3.set_ylabel('Shoulder X (mm)', color=COLOR_ARMS)
        ax3.tick_params(axis='y', labelcolor=COLOR_ARMS)
        if data['shoulder_bounds']:
            ax3.set_ylim(*data['shoulder_bounds'])
        ax3.invert_yaxis()

    # Catch marker
    ax1.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.4, alpha=0.8)
    ax1.scatter([catch_idx], [catch_seat_y], color=COLOR_CATCH, s=80, marker='o', zorder=5)
    ax1.annotate(
        'Catch',
        xy=(catch_idx, catch_seat_y),
        xytext=(catch_idx + max(1, n * 0.01), catch_seat_y),
        color=COLOR_CATCH,
        fontsize=8,
        fontweight='bold',
        va='center',
    )

    # Finish marker
    ax1.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.4, alpha=0.8)
    ax1.scatter([finish_idx], [finish_seat_y], color=COLOR_FINISH, s=80, marker='X', zorder=5)
    ax1.annotate(
        'Finish',
        xy=(finish_idx, finish_seat_y),
        xytext=(finish_idx + max(1, n * 0.01), finish_seat_y),
        color=COLOR_FINISH,
        fontsize=8,
        fontweight='bold',
        va='center',
    )

    # Front stop / Back stop lines
    ax1.axhline(seat_min, color=COLOR_CATCH, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(x_end, seat_min, 'Front stop', color=COLOR_CATCH, fontsize=8, fontweight='bold', va='top', ha='right')
    ax1.axhline(seat_max, color=COLOR_FINISH, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(x_end, seat_max, 'Back stop', color=COLOR_FINISH, fontsize=8, fontweight='bold', va='bottom', ha='right')

    ax1.grid(axis='x', alpha=0.2)

    legend_lines, legend_labels = ax1.get_legend_handles_labels()
    legend_lines2, legend_labels2 = ax2.get_legend_handles_labels()
    all_lines = legend_lines + legend_lines2
    all_labels = legend_labels + legend_labels2
    if data['has_shoulder']:
        legend_lines3, legend_labels3 = ax3.get_legend_handles_labels()  # type: ignore[possibly-undefined]
        all_lines += legend_lines3
        all_labels += legend_labels3

    ax1.legend(
        all_lines,
        all_labels,
        loc='upper center',
        bbox_to_anchor=(0.5, 0.98),
        ncol=min(3, len(all_lines)),
        fontsize=8,
        framealpha=0.8,
        facecolor=BG_COLOR_AXES,
        edgecolor='#DDDDDD',
    )

    st.pyplot(fig, width='stretch')
    plt.close(fig)

    st.info(coach_tip)
