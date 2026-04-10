"""Trunk Angle plot renderer.

Renders trunk angle trace with anatomical stick figures at key stages.
"""

from typing import Any, cast

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from rowing_catch.plots.theme import (
    BG_COLOR_FIGURE,
    COLOR_CATCH,
    COLOR_COMPARE,
    COLOR_FINISH,
    COLOR_MAIN,
    REFERENCE_LINE_COLOR,
    SPINE_COLOR,
)


def render_trunk_angle_with_stage_stickfigures(computed_data: dict[str, Any]):
    """Render trunk angle with stage stick figures.

    Args:
        computed_data: Output from TrunkAngleComponent.compute()
    """
    data = computed_data['data']
    ghost_data = computed_data.get('ghost_data')
    coach_tip = computed_data['coach_tip']

    x = data['x']
    trunk_angle = data['trunk_angle_plot']
    catch_idx = data['catch_idx']
    finish_idx = data['finish_idx']
    x_min = data['x_min']
    x_max = data['x_max']
    stage_angles = data['stage_angles']
    catch_zone = data['catch_zone']
    finish_zone = data['finish_zone']

    # Create figure with 2 subplots
    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        sharex=True,
        gridspec_kw={'height_ratios': [3, 2]},
        constrained_layout=True,
    )

    # Modern Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax_top.set_facecolor('#FFFFFF')
    ax_bot.set_facecolor(BG_COLOR_FIGURE)

    # Clean up spines on top plot
    ax_top.spines['top'].set_visible(False)
    ax_top.spines['right'].set_visible(False)
    ax_top.spines['left'].set_color(SPINE_COLOR)
    ax_top.spines['bottom'].set_color(SPINE_COLOR)
    ax_top.grid(axis='y', linestyle='-', linewidth=0.5, color='#F0F0F0', zorder=0)

    # Add padding to avoid Streamlit cropping
    try:
        cast(Any, fig).set_constrained_layout_pads(w_pad=0.04, h_pad=0.04, wspace=0.02, hspace=0.02)
    except Exception:
        pass

    # --- Top: trunk angle trace ---
    ax_top.plot(x, trunk_angle, color=COLOR_MAIN, label='Trunk Angle', linewidth=2.5, zorder=5)

    # Fill under the curve
    ax_top.fill_between(
        x,
        trunk_angle,
        0,
        where=(trunk_angle > 0),
        color=COLOR_MAIN,
        alpha=0.1,
        zorder=4,
    )
    ax_top.fill_between(
        x,
        trunk_angle,
        0,
        where=(trunk_angle <= 0),
        color=COLOR_MAIN,
        alpha=0.1,
        zorder=4,
    )

    # Plot ghost cycle if provided
    if ghost_data is not None:
        ax_top.plot(
            ghost_data['x'],
            ghost_data['trunk_angle_plot'],
            color=COLOR_COMPARE,
            linestyle=':',
            linewidth=2,
            alpha=0.8,
            label='Compare',
            zorder=4,
        )

    # Upright reference (0° from vertical)
    ax_top.axhline(0, color=REFERENCE_LINE_COLOR, linestyle='dashed', linewidth=1, alpha=0.5, zorder=2)
    ax_top.text(
        x.min() + 2,
        0,
        'Upright (0°)',
        color='#666666',
        fontsize=9,
        fontweight='medium',
        va='bottom',
        ha='left',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.8, pad=0.6),
        zorder=6,
    )

    # Mark catch and finish
    ax_top.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.5, zorder=2)
    ax_top.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.5, zorder=2)
    ax_top.axvline(x_max, color=COLOR_CATCH, linestyle='--', linewidth=1.5, zorder=2)

    # Ideal zones
    ax_top.axhspan(catch_zone[0], catch_zone[1], color=COLOR_CATCH, alpha=0.08, zorder=1)
    ax_top.axhspan(finish_zone[0], finish_zone[1], color=COLOR_FINISH, alpha=0.08, zorder=1)

    ax_top.set_ylabel('Degrees from Vertical', color='#444444', fontweight='bold', labelpad=10)
    ax_top.tick_params(axis='y', colors='#666666')

    # Add labels for catch/finish
    y_min, y_max = ax_top.get_ylim()
    y_label = y_max - (y_max - y_min) * 0.05

    ax_top.text(
        catch_idx,
        y_label,
        'Catch',
        color=COLOR_CATCH,
        ha='center',
        va='top',
        fontsize=10,
        fontweight='bold',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5),
        zorder=6,
    )
    ax_top.text(
        finish_idx,
        y_label,
        'Finish',
        color=COLOR_FINISH,
        ha='center',
        va='top',
        fontsize=10,
        fontweight='bold',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5),
        zorder=6,
    )
    ax_top.text(
        x_max,
        y_label,
        'Catch',
        color=COLOR_CATCH,
        ha='center',
        va='top',
        fontsize=10,
        fontweight='bold',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5),
        zorder=6,
    )

    # Zone labels
    x_right = (x.min() + x.max()) * 0.85
    ax_top.text(
        x_right,
        sum(catch_zone) / 2,
        'Ideal Catch',
        color=COLOR_CATCH,
        ha='center',
        va='center',
        fontsize=9,
        fontweight='medium',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.7, pad=1.5),
        zorder=6,
    )
    ax_top.text(
        x_right,
        sum(finish_zone) / 2,
        'Ideal Finish',
        color=COLOR_FINISH,
        ha='center',
        va='center',
        fontsize=9,
        fontweight='medium',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.7, pad=1.5),
        zorder=6,
    )

    ax_top.legend(loc='center right', frameon=True, facecolor='#FFFFFF', edgecolor=SPINE_COLOR, fontsize=9)

    # --- Bottom: anchor axis with stick figures ---
    ax_bot.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axvline(x_max, color=COLOR_CATCH, linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axhline(0.0, color=REFERENCE_LINE_COLOR, linewidth=1, alpha=0.2)
    ax_bot.set_ylim(-0.5, 1.5)
    ax_bot.set_yticks([])
    ax_bot.set_xlabel('Stroke Timeline (Data Points)', color='#444444', fontweight='bold', labelpad=10)
    ax_bot.tick_params(axis='x', colors='#666666')
    ax_bot.set_xlim(x_min - 5, x_max + 5)

    # Hide spines for clean look
    for spine in ax_bot.spines.values():
        spine.set_visible(False)
    ax_bot.spines['bottom'].set_visible(True)
    ax_bot.spines['bottom'].set_color(SPINE_COLOR)

    # Helper functions for stick figures
    def _data_x_to_axes_frac(ix: int) -> float:
        disp = ax_bot.transData.transform((ix, 0.0))
        axes_xy = ax_bot.transAxes.inverted().transform(disp)
        return float(axes_xy[0])

    def _vector_from_vertical_angle(angle_deg: float, length: float):
        a = np.radians(angle_deg)
        return length * np.sin(a), length * np.cos(a)

    trunk_length = 1.0
    head_radius = 0.22
    inset_w_default = 0.16
    inset_h = 0.80
    inset_y0 = 0.08
    edge_margin = 0.05

    # Draw stick figures at each stage
    for label, ix, angle in stage_angles:
        frac = _data_x_to_axes_frac(ix)
        frac_safe = float(np.clip(frac, edge_margin, 1.0 - edge_margin))

        max_w_left = 2.0 * max(frac_safe - edge_margin, 0.0)
        max_w_right = 2.0 * max((1.0 - edge_margin) - frac_safe, 0.0)
        inset_w = float(min(inset_w_default, max_w_left, max_w_right))
        inset_w = float(max(inset_w, 0.12))

        x0 = float(np.clip(frac_safe - inset_w / 2, edge_margin, (1.0 - edge_margin) - inset_w))
        stage_inside = float(np.clip(frac - x0, 0.0, inset_w))

        inset = ax_bot.inset_axes([x0, inset_y0, inset_w, inset_h], transform=ax_bot.transAxes)
        inset.set_aspect('equal', adjustable='box')
        inset.axis('off')
        inset.set_clip_on(False)

        x_span = 1.2
        frac_in_inset = stage_inside / inset_w if inset_w > 0 else 0.5
        x_left = -x_span * frac_in_inset
        x_right = x_span * (1.0 - frac_in_inset)
        inset.set_xlim(x_left, x_right)
        inset.set_ylim(-0.35, 1.60)

        # Vertical reference line
        inset.plot([0, 0], [0, trunk_length], color=REFERENCE_LINE_COLOR, alpha=0.3, linestyle=':', linewidth=1.5, clip_on=False)

        # Stick figure torso and head
        dx, dy = _vector_from_vertical_angle(angle, trunk_length)
        inset.plot([0, dx], [0, dy], color=COLOR_MAIN, linewidth=3.5, solid_capstyle='round', clip_on=False)
        inset.add_patch(plt.Circle((dx, dy + head_radius), head_radius, color='#B5B9D2', zorder=3, clip_on=False))

        # Stage label
        label_color = COLOR_CATCH if 'Catch' in label else COLOR_FINISH if 'Finish' in label else '#666666'
        label_weight = 'bold' if 'Catch' in label or 'Finish' in label else 'medium'
        inset.text(0, -0.27, label, ha='center', va='top', fontsize=8, color=label_color, fontweight=label_weight, clip_on=False)
        inset.text(
            0,
            1.32,
            f'{angle:.1f}°',
            ha='center',
            va='bottom',
            fontsize=8,
            color='#444444',
            fontweight='bold',
            zorder=5,
            bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.85, pad=1.5),
            clip_on=False,
        )

    st.pyplot(fig)
    st.info(f"**Coach's Tip:** {coach_tip}")


__all__ = ['render_trunk_angle_with_stage_stickfigures']
