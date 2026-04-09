from typing import Any, cast

import matplotlib.pyplot as plt

# --- Global Premium Styling Constants ---
COLOR_MAIN = '#636EFA'  # Blue-purple
COLOR_LEGS = '#636EFA'
COLOR_TRUNK = '#EF553B'
COLOR_ARMS = '#00CC96'
COLOR_HANDLE = '#AB63FA'
COLOR_SEAT = '#FFA15A'
COLOR_CATCH = '#00CC96'
COLOR_FINISH = '#EF553B'
COLOR_COMPARE = '#A8B2C1'  # Ideal/Compare (Gray)
COLOR_IDEAL_RATIO = '#FDB833'  # Gold — biomechanically ideal ratio
COLOR_TEXT_MAIN = '#444444'
COLOR_TEXT_SUB = '#666666'
BG_COLOR_FIGURE = '#F8F9FA'
BG_COLOR_AXES = '#FFFFFF'


def setup_premium_plot(title='', xlabel='', ylabel='', figsize=(10, 5)):
    """Set up a standard matplotlib figure with the premium UI aesthetic."""
    fig, ax = plt.subplots(figsize=figsize)

    # Modern Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#DDDDDD')
    ax.spines['bottom'].set_color('#DDDDDD')

    # Subtle horizontal gridlines
    ax.grid(axis='y', linestyle='-', linewidth=0.5, color='#F0F0F0', zorder=0)

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
    """Return a (status, icon) tuple based on deviation from the ideal value.

    Args:
        value: Observed value.
        ideal: Target / ideal value.
        yellow_threshold: Max % deviation still considered Yellow.
        green_threshold: Max % deviation considered Green.

    Returns:
        Tuple of (status_string, emoji_icon).
    """
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return 'Green'
    elif deviation <= yellow_threshold:
        return 'Yellow'
    else:
        return 'Red'
