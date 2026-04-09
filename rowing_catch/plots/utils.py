"""Shared utilities for plot rendering."""

from typing import Any, cast

import matplotlib.pyplot as plt

from rowing_catch.plots.theme import (
    BG_COLOR_AXES,
    BG_COLOR_FIGURE,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_SUB,
    GRID_COLOR,
    SPINE_COLOR,
)


def setup_premium_plot(title='', xlabel='', ylabel='', figsize=(10, 5)):
    """Set up a standard matplotlib figure with the premium UI aesthetic.

    Args:
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size (width, height)

    Returns:
        Tuple of (fig, ax) ready for plotting
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Modern Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(SPINE_COLOR)
    ax.spines['bottom'].set_color(SPINE_COLOR)

    # Subtle horizontal gridlines
    ax.grid(axis='y', linestyle='-', linewidth=0.5, color=GRID_COLOR, zorder=0)

    # Fonts and labeling
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLOR_TEXT_MAIN)
    if xlabel:
        ax.set_xlabel(xlabel, fontweight='bold', color=COLOR_TEXT_SUB, labelpad=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontweight='bold', color=COLOR_TEXT_SUB, labelpad=10)

    ax.tick_params(axis='x', colors=COLOR_TEXT_SUB)
    ax.tick_params(axis='y', colors=COLOR_TEXT_SUB)

    # Ensure constrained layout padding to prevent edge cropping in Streamlit
    try:
        cast(Any, fig).set_constrained_layout_pads(w_pad=0.04, h_pad=0.04, wspace=0.02, hspace=0.02)
    except Exception:
        pass

    return fig, ax


def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    """Return a status based on deviation from ideal value.

    Args:
        value: Observed value
        ideal: Target / ideal value
        yellow_threshold: Max % deviation still considered Yellow
        green_threshold: Max % deviation considered Green

    Returns:
        One of: 'Green', 'Yellow', 'Red'
    """
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return 'Green'
    elif deviation <= yellow_threshold:
        return 'Yellow'
    else:
        return 'Red'


__all__ = ['setup_premium_plot', 'get_traffic_light']
