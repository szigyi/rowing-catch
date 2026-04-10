import os
import re
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from rowing_catch.algo.step.step1_rename import step1_rename_columns
from rowing_catch.algo.step.step2_smoothing import step2_smooth
from rowing_catch.algo.step.step3_detection import step3_detect_catches
from rowing_catch.algo.step.step4_segmentation import step4_segment_and_average
from rowing_catch.algo.step.step5_metrics import step5_compute_metrics
from rowing_catch.algo.step.step6_statistics import step6_statistics
from rowing_catch.scenario.scenarios import create_scenario_data, get_trunk_scenarios
from rowing_catch.ui.utils import (
    BG_COLOR_AXES,
    COLOR_ARMS,
    COLOR_CATCH,
    COLOR_COMPARE,
    COLOR_HANDLE,
    COLOR_IDEAL_RATIO,
    COLOR_LEGS,
    COLOR_MAIN,
    COLOR_SEAT,
    COLOR_TEXT_SUB,
    COLOR_TRUNK,
    setup_premium_plot,
)

st.title('Debug Trace')
st.markdown(
    'Use this page to follow the exact pipeline functions, data objects and reuse relationships. '
    'The trace is organised by phase and step, and highlights where each intermediate '
    'data point is created, reused, or recomputed.'
)

# ---------------------------------------------------------------------------
# Data source selection
# ---------------------------------------------------------------------------
st.sidebar.header('Data Source')
source = st.sidebar.radio('Choose input', ['CSV Upload', 'Built-in Scenario'], index=0)

df_raw: pd.DataFrame | None = None
data_label = ''

if source == 'CSV Upload':
    uploaded = st.sidebar.file_uploader('Upload trajectory CSV', type='csv')
    if uploaded:
        df_raw = pd.read_csv(uploaded)
        data_label = uploaded.name

    resource_dir = 'resources'
    if os.path.exists(resource_dir):
        example_files = sorted(f for f in os.listdir(resource_dir) if f.endswith('.csv') and 'trajectory' in f.lower())
        default_file = '2023.12.27.Szabi_36strokesPerMinute_trajectory.csv'
        default_index = 0
        if default_file in example_files:
            default_index = example_files.index(default_file) + 1

        selected_example = st.sidebar.selectbox('Or pick an example file', ['None'] + example_files, index=default_index)
        if selected_example != 'None' and df_raw is None:
            df_raw = pd.read_csv(os.path.join(resource_dir, selected_example))
            data_label = selected_example
else:
    scenarios = get_trunk_scenarios()
    selected_scenario = st.sidebar.selectbox('Scenario', list(scenarios.keys()), index=0)
    df_raw = create_scenario_data('Trunk', selected_scenario)
    data_label = f'Scenario: {selected_scenario}'

if df_raw is None:
    st.info('Select a data source in the sidebar to begin.')
    st.stop()

if 'Time' not in df_raw.columns:
    df_raw['Time'] = np.arange(len(df_raw)) / 120.0

st.caption(f'**Input:** {data_label} — {len(df_raw):,} rows × {len(df_raw.columns)} columns')

# ---------------------------------------------------------------------------
# Visual helpers
# ---------------------------------------------------------------------------


def _pill(text: str, color: str) -> str:
    return (
        f"<span style='display:inline-block; padding:2px 8px; border-radius:12px; "
        f"background:{color}; color:#ffffff; font-size:0.85em; margin:0 4px 4px 0;'>"
        f'{text}</span>'
    )


# Column color mapping for consistent theming
COLUMN_COLORS = {
    # Raw position columns
    'Handle_X': COLOR_HANDLE,
    'Handle_Y': COLOR_HANDLE,
    'Seat_X': COLOR_SEAT,
    'Seat_Y': COLOR_SEAT,
    'Shoulder_X': COLOR_TRUNK,
    'Shoulder_Y': COLOR_TRUNK,
    # Smoothed columns
    'Handle_X_Smooth': COLOR_HANDLE,
    'Handle_Y_Smooth': COLOR_HANDLE,
    'Seat_X_Smooth': COLOR_SEAT,
    'Seat_Y_Smooth': COLOR_SEAT,
    'Shoulder_X_Smooth': COLOR_TRUNK,
    'Shoulder_Y_Smooth': COLOR_TRUNK,
    # Velocity columns
    'Handle_X_Vel': COLOR_HANDLE,
    'Seat_X_Vel': COLOR_SEAT,
    'Shoulder_X_Vel': COLOR_TRUNK,
    'Rower_Vel': COLOR_MAIN,
    # Acceleration columns
    'Handle_X_Accel': COLOR_HANDLE,
    'Seat_X_Accel': COLOR_SEAT,
    'Shoulder_X_Accel': COLOR_TRUNK,
    'Rower_Accel': COLOR_MAIN,
    # Jerk columns
    'Handle_X_Jerk': COLOR_HANDLE,
    'Seat_X_Jerk': COLOR_SEAT,
    'Shoulder_X_Jerk': COLOR_TRUNK,
    'Rower_Jerk': COLOR_MAIN,
    # Power columns
    'Power_Total': COLOR_MAIN,
    'Power_Legs': COLOR_LEGS,
    'Power_Trunk': COLOR_TRUNK,
    'Power_Arms': COLOR_ARMS,
    # Other computed columns
    'Trunk_Angle': COLOR_TRUNK,
    'Stroke_Compression': COLOR_COMPARE,
    'Time': COLOR_TEXT_SUB,
}


def _color_column_text(text: str) -> str:
    """Color column names in text using the theme colors."""
    # Replace column names that are in our mapping, but avoid coloring function names
    # by ensuring they appear in contexts like "reads:" or "creates:" or in parentheses
    colored_text = text

    # Sort by length (longest first) to avoid partial matches
    for col_name in sorted(COLUMN_COLORS.keys(), key=len, reverse=True):
        color = COLUMN_COLORS[col_name]
        # Use word boundaries to match whole column names
        pattern = rf'\b{re.escape(col_name)}\b'
        colored_text = re.sub(pattern, _pill(col_name, color), colored_text)

    return colored_text


def _render_call_tree(lines: list[str]):
    # Color the column names in each line and render as HTML
    colored_lines = [_color_column_text(line) for line in lines]
    # Use div with monospace font to preserve tree structure
    html_content = f"<div style='font-family: monospace; font-size: 14px; line-height: 1.4; white-space: pre; margin: 0;'>{chr(10).join(colored_lines)}</div>"  # noqa: E501
    st.markdown(html_content, unsafe_allow_html=True)


def _render_data_matrix(rows: list[dict[str, str]]):
    header = '| Data object | Created by | Used by | Notes |'
    header += '\n|---|---|---|---|'
    body = '\n'.join(f'| {row["data"]} | {row["created_by"]} | {row["used_by"]} | {row["notes"]} |' for row in rows)
    st.markdown(header + '\n' + body, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Execute the pipeline once for trace
# ---------------------------------------------------------------------------
_step_context: dict[str, Any] = {}

try:
    _step_context['df_step1'] = step1_rename_columns(df_raw)
    _step_context['df_step2'] = step2_smooth(_step_context['df_step1'], window=10)
    _step_context['df_step3'], _step_context['catch_indices'] = step3_detect_catches(_step_context['df_step2'], window=10)
    result4 = step4_segment_and_average(_step_context['df_step3'], _step_context['catch_indices'], window=10)
    if result4 is None:
        raise RuntimeError('No valid cycles could be extracted during segmentation.')
    _step_context['cycles'], _step_context['avg_cycle'], _step_context['min_length'] = result4
    _step_context['avg_cycle_m'], _step_context['catch_idx'], _step_context['finish_idx'] = step5_compute_metrics(
        _step_context['avg_cycle'], window=10
    )
    _step_context['stats'] = step6_statistics(
        _step_context['cycles'],
        _step_context['min_length'],
        _step_context['catch_idx'],
        _step_context['finish_idx'],
        _step_context['avg_cycle_m'],
    )
except Exception as exc:
    st.error(f'Pipeline execution failed: {exc}')
    st.stop()

st.markdown('## Trace Summary')

# ---------------------------------------------------------------------------
# Insights from the execution trace
# ---------------------------------------------------------------------------
insights = [
    (
        f'{_pill("Handle_X_Smooth", COLOR_HANDLE)} and {_pill("Seat_X_Smooth", COLOR_SEAT)} '
        'are created once in step 2 and reused in step 3, step 5, and the final metrics.'
    ),
    (
        f'{_pill("Stroke_Compression", COLOR_COMPARE)} is first created in step 3 '
        'for diagnostics, then recomputed on the averaged cycle in step 5. '
        'The averaged-cycle version is not reused from the full-signal version.'
    ),
    (
        f'{_pill("avg_drive_recovery_ratio", COLOR_IDEAL_RATIO)} is calculated from '
        'per-cycle finish heuristics in step 6, not from a single average-cycle measurement.'
    ),
    (f'{_pill("avg_cycle_m", COLOR_IDEAL_RATIO)} is the enriched average cycle used for UI and scalar metric generation.'),
]

for insight in insights:
    st.markdown(f'- {insight}', unsafe_allow_html=True)

with st.expander('Detailed function call tree', expanded=True):
    call_tree = [
        'Phase 1: Raw Data Intake & Validation',
        '  |- Step 0 - Validation',
        '  |  |- validate_input_df(df_raw) [R]',
        '  |  |  |- reads: all columns for validation (names, dtypes, non-empty)',
        '  |  |  |- outputs: None (validation only)',
        '  |- Step 1 - Rename Columns',
        '  |  |- step1_rename_columns(df_raw) [R/W]',
        '  |  |  |- reads: raw columns (assumed Handle_X_raw, etc.)',
        '  |  |  |- creates: Handle_X, Handle_Y, Shoulder_X, Shoulder_Y, Seat_X, Seat_Y',
        '  |  |  |- outputs: df_step1',
        'Phase 2: Signal Conditioning',
        '  |- Step 2 - Smooth',
        '  |  |- step2_smooth(df_step1) [R/W]',
        '  |  |  |- reads: Handle_X, Handle_Y, Shoulder_X, Shoulder_Y, Seat_X, Seat_Y',
        '  |  |  |- creates: Handle_X_Smooth, Handle_Y_Smooth, Seat_X_Smooth, Seat_Y_Smooth, Shoulder_X_Smooth, Shoulder_Y_Smooth',  # noqa: E501
        '  |  |  |- outputs: df_step2',
        '  |- Step 3 - Detect Catches',
        '  |  |- step3_detect_catches(df_step2) [R/W]',
        '  |  |  |- interpolates gaps: _interpolate_small_gaps(Seat_X_Smooth, Seat_Y_Smooth) [R/W]',
        '  |  |  |- detects local minima: _detect_catches_by_seat_reversal(Seat_X_Smooth) [R]',
        '  |  |  |  |- validates candidates: _is_valid_catch(Seat_X_Smooth, candidate_idx) [R]',
        '  |  |  |  |  |- computes clean signal SNR: _compute_signal_noise_ratio(Seat_X_Smooth) [R]',
        '  |  |  |  |  |- validates secondary signal reversal: _validate_secondary_for_reversal(Seat_Y_Smooth) [R]',
        '  |  |  |- reads: Seat_X_Smooth, Seat_Y_Smooth',
        '  |  |  |- creates: Stroke_Compression (diagnostic)',
        '  |  |  |- outputs: df_step3, catch_indices',
        '  |- Step 4 - Segment & Average',
        '  |  |- step4_segment_and_average(df_step3, catch_indices) [R]',
        '  |  |  |- reads: df_step3 (Handle_X_Smooth, Seat_X_Smooth, etc.), catch_indices',
        '  |  |  |- creates: cycles, avg_cycle, min_length',
        '  |  |  |- outputs: avg_cycle',
        'Phase 3: Average Cycle Metrics',
        '  |- Step 5 - Compute Metrics',
        '  |  |- step5_compute_metrics(avg_cycle) [R/W]',
        '  |  |  |- reads: avg_cycle (Handle_X_Smooth, Seat_X_Smooth, Shoulder_X_Smooth, Seat_Y_Smooth, Shoulder_Y_Smooth, Time)',  # noqa: E501
        '  |  |  |- computes trunk angle: _compute_trunk_angles(avg_cycle) [R]',
        '  |  |  |  |- reads: Shoulder_X_Smooth, Seat_X_Smooth, Shoulder_Y_Smooth, Seat_Y_Smooth',
        '  |  |  |  |- creates: Trunk_Angle',
        '  |  |  |- computes velocities/accelerations/jerks from smoothed signals',
        '  |  |  |- computes torso proxy and power proxies via _compute_power_proxies(avg_cycle) [R/W]',
        '  |  |  |  |- reads: Handle_X_Vel, Seat_X_Vel, Shoulder_X_Vel',
        '  |  |  |  |- creates: Power_Total, Power_Legs, Power_Trunk, Power_Arms',
        '  |  |  |- re-detects catch/finish on avg cycle: _pick_finish_index(avg_cycle) [R]',
        '  |  |  |  |- reads: Handle_X_Smooth, Time',
        '  |  |  |- creates: Handle_X_Vel, Seat_X_Vel, Shoulder_X_Vel, Handle_X_Accel, Seat_X_Accel, Shoulder_X_Accel, Handle_X_Jerk, Seat_X_Jerk, Shoulder_X_Jerk, Rower_Vel, Rower_Accel, Rower_Jerk, Stroke_Compression (recomputed)',  # noqa: E501
        '  |  |  |- outputs: avg_cycle_m, catch_idx, finish_idx',
        '  |- Step 6 - Statistics',
        '  |  |- step6_statistics(cycles, min_length, catch_idx, finish_idx, avg_cycle_m) [R/W]',
        '  |  |  |- reads: cycles (Seat_X_Smooth, Time), avg_cycle_m (all columns)',
        '  |  |  |- computes per-cycle metrics and consistency values',
        '  |  |  |- computes phase volume: _compute_phase_volume(Seat_X_Smooth, Time) [R]',
        '  |  |  |- computes temporal metrics: _compute_temporal_metrics(avg_cycle_m, Time) [R]',
        '  |  |  |- reuses _pick_finish_index for cycle-level finish detection',
        '  |  |  |- creates: stats (cv_length, drive_len, recovery_len, mean_duration, drive_volume_mm_sec, recovery_volume_mm_sec, avg_drive_recovery_ratio, sample_rate_hz, cycle_duration_s, drive_duration_s, recovery_duration_s, stroke_rate_spm, cycle_details)',  # noqa: E501
    ]
    _render_call_tree(call_tree)

with st.expander('Data lineage matrix', expanded=False):
    matrix_rows = [
        {
            'data': _pill('df_step1', COLOR_MAIN),
            'created_by': 'step1_rename_columns',
            'used_by': 'step2_smooth',
            'notes': 'Renamed raw columns for the unified pipeline.',
        },
        {
            'data': _pill('df_step2', COLOR_MAIN),
            'created_by': 'step2_smooth',
            'used_by': 'step3_detect_catches, step5_compute_metrics, step6_statistics',
            'notes': 'Contains smooth position channels used throughout the pipeline.',
        },
        {
            'data': _pill('catch_indices', COLOR_CATCH),
            'created_by': 'step3_detect_catches',
            'used_by': 'step4_segment_and_average',
            'notes': 'Stroke boundaries detected from Seat_X_Smooth.',
        },
        {
            'data': _pill('avg_cycle', COLOR_MAIN),
            'created_by': 'step4_segment_and_average',
            'used_by': 'step5_compute_metrics, step6_statistics',
            'notes': 'Aligned averaged stroke before metric enrichment.',
        },
        {
            'data': _pill('avg_cycle_m', COLOR_IDEAL_RATIO),
            'created_by': 'step5_compute_metrics',
            'used_by': 'step6_statistics, UI plots',
            'notes': 'Enriched averaged stroke with biomechanical derivatives and events.',
        },
        {
            'data': _pill('avg_drive_recovery_ratio', COLOR_IDEAL_RATIO),
            'created_by': 'step6_statistics',
            'used_by': 'UI summaries and rhythm diagnostics',
            'notes': 'Computed from individual cycle ratios, not re-used from avg_cycle directly.',
        },
        {
            'data': _pill('Stroke_Compression', COLOR_COMPARE),
            'created_by': 'step3_detect_catches and step5_compute_metrics',
            'used_by': 'Diagnostics and cycle segmentation',
            'notes': 'Diagnostic variable exists in both full-trace and averaged-cycle forms.',
        },
    ]
    _render_data_matrix(matrix_rows)

with st.expander('Pipeline health and reuse check', expanded=False):
    st.markdown(
        '- **Reused once:** `Handle_X_Smooth`, `Seat_X_Smooth`, `Shoulder_X_Smooth` are created in step 2 '
        'and reused downstream.\n'
        '- **Recomputed:** `Stroke_Compression` is recomputed in step 5 on the averaged cycle '
        'rather than reused from step 3.\n'
        '- **Average ratio path:** `avg_drive_recovery_ratio` is assembled from per-cycle ratios in step 6, '
        'so it represents cycle-level consistency rather than a single average-cycle split.\n'
        '- **Event indices:** `catch_idx` and `finish_idx` are derived from the enriched average cycle '
        'and are reused to label metrics and visualizations.\n'
    )

with st.expander('Sample smoothed signal and event trace', expanded=True):
    fig, ax = setup_premium_plot(xlabel='Sample index', ylabel='Seat_X_Smooth', figsize=(10, 3.5))
    ax.plot(
        _step_context['df_step2'].index,
        _step_context['df_step2']['Seat_X_Smooth'],
        color=COLOR_SEAT,
        linewidth=1.6,
        label='Seat_X_Smooth',
    )
    ax.plot(
        _step_context['df_step2'].index,
        _step_context['df_step2']['Handle_X_Smooth'],
        color=COLOR_HANDLE,
        linewidth=1.2,
        linestyle='--',
        label='Handle_X_Smooth',
    )
    ax.scatter(
        _step_context['catch_indices'],
        _step_context['df_step2']['Seat_X_Smooth'].iloc[_step_context['catch_indices']],
        color=COLOR_CATCH,
        s=60,
        zorder=5,
        label='Detected Catch',
    )
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    st.markdown('Use this visualisation to verify the same signal objects shown above are also the ones feeding the trace logic.')

st.divider()
st.caption(
    'This trace page is meant to help you audit the pipeline and understand exactly where '
    'intermediate data is created and reused.'
)
