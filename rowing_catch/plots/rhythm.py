"""Consistency & Rhythm plot renderer.

Renders rhythm metrics and drive/recovery proportion.
"""

from typing import Any

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plots.theme import (
    BG_COLOR_AXES,
    BG_COLOR_FIGURE,
    COLOR_FINISH,
    COLOR_MAIN,
    COLOR_TEXT_MAIN,
)


def render_consistency_rhythm(computed_data: dict[str, Any]):
    """Render consistency and rhythm plot.

    Args:
        computed_data: Output from ConsistencyRhythmComponent.compute()
    """
    data = computed_data['data']
    coach_tip = computed_data['coach_tip']

    cv = data['cv']

    # Display variability text
    st.write(f'Your current variability: **{cv:.2f}%**')
    if cv < 2:
        st.success('Excellent! You have a very stable, robotic rhythm.')
    elif cv < 5:
        st.warning('Good consistency, but room to find a more repeatable rhythm.')
    else:
        st.error('High variability detected. Focus on making every stroke identical.')

    # Create pie chart
    labels = ['Drive', 'Recovery']
    sizes = [data['drive_percent'], data['recovery_percent']]

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)

    ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=[COLOR_FINISH, COLOR_MAIN],
        textprops={'color': COLOR_TEXT_MAIN, 'fontweight': 'bold'},
    )
    ax.axis('equal')

    st.pyplot(fig)
    st.info(f"**Coach's Tip:** {coach_tip}")


__all__ = ['render_consistency_rhythm']
