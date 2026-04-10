"""Catch Detection renderer.

Renders the catch detection plot: smoothed seat signal with catch markers and interval table.
"""

from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from rowing_catch.plot.theme import BG_COLOR_AXES, COLOR_CATCH, COLOR_SEAT
from rowing_catch.plot.utils import setup_premium_plot


def render_catch_detection(computed_data: dict[str, Any]) -> None:
    """Render catch detection plot and interval table.

    Args:
        computed_data: Output from CatchDetectionComponent.compute()
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    fig, ax = setup_premium_plot(
        title=metadata['title'],
        y_label=metadata['y_label'],
        figsize=(10, 3),
    )

    index = data['index']
    seat_smooth = data['seat_smooth']
    catch_indices = data['catch_indices']
    catch_values = data['catch_values']

    ax.plot(index, seat_smooth, color=COLOR_SEAT, linewidth=1.2, label='Seat_X_Smooth (detection signal)')
    if seat_smooth:
        seat_min = min(seat_smooth)
        ax.fill_between(index, seat_smooth, seat_min, color=COLOR_SEAT, alpha=0.08)

    for ci in catch_indices:
        ax.axvline(ci, color=COLOR_CATCH, linewidth=1, linestyle='--', alpha=0.8)

    if catch_indices and catch_values:
        ax.scatter(
            catch_indices,
            catch_values,
            color=COLOR_CATCH,
            s=60,
            zorder=5,
            label='Detected Catch (local min)',
        )

    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    if data['intervals']:
        st.markdown('**Catch-to-catch intervals (samples):**')
        df_intervals = pd.DataFrame(
            {
                'Catch #': [r['catch_num'] for r in data['intervals']],
                'Start index': [r['start'] for r in data['intervals']],
                'End index': [r['end'] for r in data['intervals']],
                'Interval (samples)': [r['interval'] for r in data['intervals']],
            }
        )
        st.dataframe(df_intervals, use_container_width=True, hide_index=True)

    st.info(coach_tip)
