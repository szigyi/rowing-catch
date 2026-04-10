"""Rhythm Consistency renderer.

Renders SPM vs drive/recovery ratio scatter plot using altair.
"""

from typing import Any

import altair as alt
import streamlit as st

from rowing_catch.plots.theme import BG_COLOR_AXES, BG_COLOR_FIGURE, COLOR_MAIN, COLOR_TEXT_MAIN, COLOR_TEXT_SUB


def render_rhythm_consistency(computed_data: dict[str, Any]):
    """Render rhythm consistency plot.

    Args:
        computed_data: Output from RhythmConsistencyComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    if not data['has_data']:
        st.warning('No individual cycle data available for ratio consistency.')
        return

    df = data['dataframe']

    if df.empty:
        st.warning('Insufficient data points for consistency plot.')
        return

    chart = (
        alt.Chart(df)
        .mark_circle(size=100, opacity=0.7, color=COLOR_MAIN)
        .encode(
            x=alt.X('spm:Q', title=metadata['x_label'], scale=alt.Scale(zero=False)),
            y=alt.Y('drive_recovery_ratio:Q', title=metadata['y_label'], scale=alt.Scale(zero=False)),
            tooltip=['cycle_idx', 'spm', 'drive_recovery_ratio'],
        )
        .properties(title=metadata['title'], width=700, height=400, background=BG_COLOR_FIGURE)
        .configure_view(fill=BG_COLOR_AXES, strokeWidth=0)
        .configure_axis(
            grid=True,
            gridColor='#F0F0F0',
            domainColor='#DDDDDD',
            tickColor='#DDDDDD',
            labelColor=COLOR_TEXT_SUB,
            titleColor=COLOR_TEXT_SUB,
        )
        .configure_title(color=COLOR_TEXT_MAIN, fontSize=14)
    )

    st.altair_chart(chart, use_container_width=True)
    st.info(f'**Performance Insight:** {coach_tip}')
