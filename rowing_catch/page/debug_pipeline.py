import os
from typing import cast

import numpy as np
import pandas as pd
import streamlit as st

from rowing_catch.algo.constants import PROCESSED_COLUMN_NAMES, REQUIRED_COLUMN_NAMES
from rowing_catch.algo.step.step0_validation import validate_input_df
from rowing_catch.algo.step.step1_rename import step1_rename_columns
from rowing_catch.algo.step.step2_smoothing import step2_smooth
from rowing_catch.algo.step.step3_detection import step3_detect_catches
from rowing_catch.algo.step.step4_segmentation import step4_segment_and_average
from rowing_catch.algo.step.step5_metrics import step5_compute_metrics
from rowing_catch.algo.step.step6_statistics import step6_statistics
from rowing_catch.algo.step.step7_diagnostics import step7_diagnostics
from rowing_catch.plot.avg_cycle_multi_axis_plot import render_avg_cycle_multi_axis
from rowing_catch.plot.avg_cycle_trunk_angle_plot import render_avg_cycle_trunk_angle
from rowing_catch.plot.catch.catch_detection_plot import render_catch_detection
from rowing_catch.plot.cycle_overlay_mean_std_plot import render_cycle_overlay_mean_std
from rowing_catch.plot.jerk_comparison_plot import render_jerk_comparison
from rowing_catch.plot.power_curve.debug_power_curve_plot import render_debug_power_curve
from rowing_catch.plot.production_finish_trajectory_plot import render_production_finish_trajectory
from rowing_catch.plot.rhythm.drive_recovery_balance_plot import render_drive_recovery_balance
from rowing_catch.plot.rhythm.rhythm_consistency_plot import render_rhythm_consistency
from rowing_catch.plot.signal_smoothing_comparison_plot import render_signal_smoothing_comparison
from rowing_catch.plot.velocity.relative_velocity_plot import render_relative_velocity
from rowing_catch.plot.velocity.velocity_profile_plot import render_velocity_profile
from rowing_catch.plot_transformer.avg_cycle_multi_axis_transformer import AvgCycleMultiAxisComponent
from rowing_catch.plot_transformer.avg_cycle_trunk_angle_transformer import AvgCycleTrunkAngleComponent
from rowing_catch.plot_transformer.catch.catch_detection_transformer import CatchDetectionComponent
from rowing_catch.plot_transformer.cycle_overlay_mean_std_transformer import CycleOverlayMeanStdComponent
from rowing_catch.plot_transformer.jerk_comparison_transformer import JerkComparisonComponent
from rowing_catch.plot_transformer.power_curve.debug_power_curve_transformer import DebugPowerCurveComponent
from rowing_catch.plot_transformer.production_finish_trajectory_transformer import ProductionFinishTrajectoryComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import DriveRecoveryBalanceComponent
from rowing_catch.plot_transformer.rhythm.rhythm_consistency_transformer import RhythmConsistencyComponent
from rowing_catch.plot_transformer.signal_smoothing_comparison_transformer import SignalSmoothingComparisonComponent
from rowing_catch.plot_transformer.velocity.relative_velocity_transformer import RelativeVelocityComponent
from rowing_catch.plot_transformer.velocity.velocity_profile_transformer import VelocityProfileComponent
from rowing_catch.scenario.scenarios import create_scenario_data, get_trunk_scenarios

st.title('Data Processing Pipeline — Debug View')
st.markdown(
    'This page runs the analysis pipeline step-by-step and exposes the **intermediate '
    'state of the data** after each step. Use it to spot where numbers go wrong.'
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
            default_index = example_files.index(default_file) + 1  # +1 for "None"

        selected_example = st.sidebar.selectbox('Or pick an example file', ['None'] + example_files, index=default_index)
        if selected_example != 'None' and df_raw is None:
            df_raw = pd.read_csv(os.path.join(resource_dir, selected_example))
            data_label = selected_example
else:
    scenarios = get_trunk_scenarios()
    selected_scenario = st.sidebar.selectbox('Scenario', list(scenarios.keys()), index=0)
    df_raw = create_scenario_data('Trunk', selected_scenario)
    data_label = f'Scenario: {selected_scenario}'

# New parameter for unit conversion
st.sidebar.divider()
fps = st.sidebar.number_input(
    'Recording FPS',
    min_value=1.0,
    max_value=240.0,
    value=120.0,
    step=1.0,
    help='Frames Per Second of the video. Used to calculate real-world velocity (mm/s).',
)

if df_raw is None:
    st.info('Select a data source in the sidebar to begin.')
    st.stop()

# Ensure Time column exists for mm/s conversion
if 'Time' not in df_raw.columns:
    df_raw['Time'] = np.arange(len(df_raw)) / fps

st.caption(f'**Input:** {data_label} — {len(df_raw):,} rows × {len(df_raw.columns)} columns')

WINDOW = 10


# ---------------------------------------------------------------------------
# Helper: a small reusable banner for each step
# ---------------------------------------------------------------------------
def _phase_header(title: str, subtitle: str):
    """Render a wide, amber-accented phase-level divider banner."""
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f'background:#1c1a12;padding:10px 14px;border-radius:10px;'
        f'border-left:5px solid #f59e0b;margin:20px 0 10px 0;'
        f"font-family:inherit;'>"
        f"<div style='display:flex;align-items:center;gap:12px;'>"
        f"<span style='color:#fbbf24;font-size:10px;font-weight:800;letter-spacing:1.5px;"
        f"text-transform:uppercase'>PHASE</span>"
        f"<strong style='color:#fef3c7;font-size:16px;margin:0;letter-spacing:0.3px'>{title}</strong>"
        f'</div>'
        f"<span style='color:#92400e;font-size:12px;margin:0;font-style:italic;'>{subtitle}</span>"
        f'</div>',
        unsafe_allow_html=True,
    )


def _step_header(number: int, title: str, subtitle: str):
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f'background:#1e293b;padding:6px 10px;border-radius:8px;border-left:4px solid #6366f1;'
        f"margin-bottom:6px;font-family:inherit;font-size:14px;'>"
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"<span style='color:#a5b4fc;font-size:11px;font-weight:700;letter-spacing:1px;"
        f"text-transform:uppercase'>STEP {number}</span>"
        f"<strong style='color:#f1f5f9;font-size:14px;margin:0'>{title}</strong>"
        f'</div>'
        f"<span style='color:#94a3b8;font-size:12px;margin:0;white-space:nowrap;'>{subtitle}</span>"
        f'</div>',
        unsafe_allow_html=True,
    )


def _ok(msg: str):
    st.success(f'{msg}')


def _fail(msg: str):
    st.error(f'{msg}')
    st.stop()


# ===========================================================================
# PHASE 1 — Raw Data Intake & Validation
# ===========================================================================
_phase_header(
    'Raw Data Intake & Validation',
    'Steps 0–1 · Ingest raw CSV, verify required columns exist, and normalise column names',
)

# ===========================================================================
# STEP 0 — Validation
# ===========================================================================
_step_header(0, 'Validation', 'Ensure input DataFrame has required columns and enough data.')

with st.expander('Step 0 details', expanded=False):
    try:
        validate_input_df(df_raw)
        _ok('Input validation passed.')
    except Exception as e:
        _fail(f'Input validation failed: {e}')


# ===========================================================================
# STEP 1 — Rename columns
# ===========================================================================
_step_header(1, 'Rename Columns', 'Map raw tracker names → clean internal names.')

with st.expander('Step 1 details', expanded=False):
    df_step1 = step1_rename_columns(df_raw)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('**Column mapping:**')
        rename_rows = []
        for raw, clean in REQUIRED_COLUMN_NAMES.items():
            found = raw in df_raw.columns
            rename_rows.append({'Raw column': raw, 'Clean column': clean, 'Found': 'Found' if found else 'Missing'})
        st.dataframe(pd.DataFrame(rename_rows), width='stretch', hide_index=True)

    with col_b:
        st.markdown('**Output columns:**')
        col_df = pd.DataFrame(
            {
                'Column': df_step1.columns.tolist(),
                'dtype': [str(dt) for dt in df_step1.dtypes],
                'non-null': df_step1.count().values,
            }
        )
        st.dataframe(col_df, width='stretch', hide_index=True)

    missing = [c for c in REQUIRED_COLUMN_NAMES.values() if c not in df_step1.columns]
    if missing:
        _fail(f'Missing required columns after rename: {missing}')
    else:
        _ok(f'{len(df_step1):,} rows, all required columns present.')

# ===========================================================================
# PHASE 2 — Signal Conditioning
# ===========================================================================
_phase_header(
    'Signal Conditioning',
    'Step 2 · Apply centred rolling-mean smoothing to suppress high-frequency sensor noise before analysis',
)

# ===========================================================================
# STEP 2 — Smooth
# ===========================================================================
_step_header(2, 'Smooth', f'Apply centred rolling mean (window={WINDOW}) to position columns.')

with st.expander('Step 2 details', expanded=False):
    df_step2 = step2_smooth(df_step1, window=WINDOW)

    _ok(f'Rows after smoothing: {len(df_step2):,} (all rows preserved, including edges with min_periods=1).')

    computed_smoothing = SignalSmoothingComparisonComponent().compute(
        avg_cycle=df_step2,
        catch_idx=0,
        finish_idx=0,
        results={'df_raw_step1': df_step1, 'df_smoothed': df_step2},
    )
    render_signal_smoothing_comparison(computed_smoothing)

    st.markdown('**Smoothed column stats:**')
    smooth_cols = [f'{c}_Smooth' for c in PROCESSED_COLUMN_NAMES if f'{c}_Smooth' in df_step2.columns]
    st.dataframe(df_step2[smooth_cols].describe().T.round(2), width='stretch')

# ===========================================================================
# PHASE 3 — Stroke Segmentation
# ===========================================================================
_phase_header(
    'Stroke Segmentation',
    'Steps 3–4 · Detect each catch event, slice the recording into individual stroke cycles, time-align and average them',
)

# ===========================================================================
# STEP 3 — Detect catches
# ===========================================================================
_step_header(3, 'Detect Catches', 'Interpolate small gaps and find local minima of Seat_X_Smooth.')

with st.expander('Step 3 details', expanded=False):
    df_step3, catch_indices = step3_detect_catches(df_step2, window=WINDOW)

    n_catches = len(catch_indices)
    if n_catches < 2:
        _fail(f'Only {n_catches} catch(es) detected — need at least 2 to form a cycle.')

    _ok(f'{n_catches} catches detected at indices: {catch_indices.tolist()}')

    computed_catches = CatchDetectionComponent().compute(
        avg_cycle=df_step3,
        catch_idx=0,
        finish_idx=0,
        results={'df_smoothed': df_step3, 'catch_indices': catch_indices},
    )
    render_catch_detection(computed_catches)

# ===========================================================================
# STEP 4 — Segment & Average
# ===========================================================================
_step_header(4, 'Segment & Average', 'Cut data into per-stroke cycles and average them.')

with st.expander('Step 4 details', expanded=False):
    result4 = step4_segment_and_average(df_step3, catch_indices, window=WINDOW)

    if result4 is None:
        _fail('Could not extract any valid cycles.')
    assert result4 is not None

    cycles, avg_cycle, min_length = result4
    _ok(f'{len(cycles)} valid cycle(s) extracted. Shortest: {min_length} samples — used as average length.')

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown('**Cycle lengths:**')
        cycle_df = pd.DataFrame(
            {
                'Cycle #': list(range(1, len(cycles) + 1)),
                'Length (samples)': [len(c) for c in cycles],
                'Seat_X range': [f'{c["Seat_X_Smooth"].min():.1f} – {c["Seat_X_Smooth"].max():.1f}' for c in cycles],
            }
        )
        st.dataframe(cycle_df, width='stretch', hide_index=True)

    with col_r:
        st.markdown('**Averaged Seat_X (all cycles overlaid):**')
        computed_overlay = CycleOverlayMeanStdComponent().compute(
            avg_cycle=avg_cycle,
            catch_idx=0,
            finish_idx=0,
            results={'cycles': cycles},
        )
        render_cycle_overlay_mean_std(computed_overlay)

# ===========================================================================
# PHASE 4 — Biomechanical Metrics on the Average Cycle
# ===========================================================================
_phase_header(
    'Biomechanical Metrics on the Average Cycle',
    'Step 5 · Derive trunk angle, velocities, acceleration, jerk, and drive-phase power proxy from the averaged stroke',
)

# ===========================================================================
# STEP 5 — Compute metrics
# ===========================================================================
_step_header(
    5, 'Compute Metrics', 'Calculate Trunk_Angle, velocities, and locate catch/finish (reversal-based) on the averaged cycle.'
)

with st.expander('Step 5 details', expanded=True):
    avg_cycle_m, catch_idx, finish_idx, _ = step5_compute_metrics(avg_cycle, window=WINDOW)

    # --- Derived Relative Metrics (UI/Analysis helper) ---
    if 'Seat_X_Vel' in avg_cycle_m.columns:
        if 'Shoulder_X_Vel' in avg_cycle_m.columns:
            avg_cycle_m['Shoulder_rel_Seat_Vel'] = avg_cycle_m['Shoulder_X_Vel'] - avg_cycle_m['Seat_X_Vel']
        avg_cycle_m['Handle_rel_Seat_Vel'] = avg_cycle_m['Handle_X_Vel'] - avg_cycle_m['Seat_X_Vel']

    catch_angle = cast(float, avg_cycle_m.loc[catch_idx, 'Trunk_Angle'])
    finish_angle = cast(float, avg_cycle_m.loc[finish_idx, 'Trunk_Angle'])

    col1, col2, col3 = st.columns(3)
    col1.metric('Catch index', catch_idx)
    col2.metric('Finish index', finish_idx)
    col3.metric('Drive length (samples)', finish_idx - catch_idx)

    col4, col5 = st.columns(2)
    col4.metric('Trunk angle @ Catch', f'{catch_angle:.1f}°')
    col5.metric('Trunk angle @ Finish', f'{finish_angle:.1f}°')

    st.markdown('**Catch + Finish on averaged cycle**')
    computed_multi = AvgCycleMultiAxisComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_avg_cycle_multi_axis(computed_multi)

    st.markdown('**All detected Catches & Finishes (Full Trajectory)**')
    st.caption('This plot shows where the *production* heuristic would place the finish for every individual cycle.')
    computed_traj = ProductionFinishTrajectoryComponent().compute(
        avg_cycle=avg_cycle_m,
        catch_idx=catch_idx,
        finish_idx=finish_idx,
        results={'df_smoothed': df_step3, 'catch_indices': catch_indices},
    )
    render_production_finish_trajectory(computed_traj)

    st.markdown('**Trunk Angle across the averaged stroke:**')
    computed_trunk = AvgCycleTrunkAngleComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_avg_cycle_trunk_angle(computed_trunk)

    st.markdown('**Detailed Velocity [rate of change] (Seat, Handle, Shoulder, Rower):**')
    computed_vel = VelocityProfileComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_velocity_profile(computed_vel)

    st.markdown('**Relative Velocity (vs. Seat):**')
    computed_rel = RelativeVelocityComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_relative_velocity(computed_rel)

    st.markdown('**Jerk in the system (Smoothness):**')
    st.caption("Each panel compares an individual segment's smoothness vs. the overall System (Torso) baseline.")
    computed_jerk = JerkComparisonComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_jerk_comparison(computed_jerk)

    st.markdown('**Power Curve (V³ Drag Model):**')
    computed_power = DebugPowerCurveComponent().compute(avg_cycle_m, catch_idx, finish_idx)
    render_debug_power_curve(computed_power)

    with st.expander('Raw averaged cycle DataFrame (all computed columns)'):
        st.dataframe(avg_cycle_m.round(3), width='stretch')

# ===========================================================================
# PHASE 5 — Stroke-Level Statistics
# ===========================================================================
_phase_header(
    'Stroke-Level Statistics',
    (
        'Step 6 · Aggregate scalar metrics across all individual cycles: '
        'consistency CV, SPM, drive/recovery ratio and temporal durations'
    ),
)

# ===========================================================================
# STEP 6 — Statistics
# ===========================================================================
_step_header(6, 'Statistics', 'Summarise stroke consistency, drive/recovery ratio.')

with st.expander('Step 6 details', expanded=True):
    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx, avg_cycle_m)

    cv = stats['cv_length']
    avg_ratio = stats['avg_drive_recovery_ratio']

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric('Consistency CV', f'{cv:.2f}%', help='Lower is better. Target < 2%.')
    col_s2.metric(
        'Avg Drive:Recovery Ratio',
        f'{avg_ratio:.3f}' if not np.isnan(avg_ratio) else 'N/A',
        help='Averaged across all individual cycles using per-cycle finish detection.',
    )
    col_s3.metric('Avg cycle duration', f'{stats["mean_duration"]:.0f} samples')

    st.markdown('**Drive vs. Recovery Balance:**')
    computed_balance = DriveRecoveryBalanceComponent().compute(
        avg_cycle=avg_cycle_m,
        catch_idx=catch_idx,
        finish_idx=finish_idx,
        results={'cycles': cycles, 'min_length': min_length},
    )
    render_drive_recovery_balance(computed_balance)

    st.markdown('**Ratio & Rhythm Spread (Consistency):**')
    from rowing_catch.ui.coaching_session import get_coaching_profile

    profile = get_coaching_profile()
    computed_rhythm = RhythmConsistencyComponent(profile=profile).compute(
        avg_cycle=avg_cycle_m,
        catch_idx=catch_idx,
        finish_idx=finish_idx,
        results={'cycles': cycles},
    )
    render_rhythm_consistency(computed_rhythm)


# ===========================================================================
# PHASE 6 — Data Quality & Diagnostics
# ===========================================================================
_phase_header(
    'Data Quality & Diagnostics',
    'Step 7 · Assess sampling stability, count rows dropped, and surface any pipeline warnings',
)

st.markdown('### Data Quality & Metadata Diagnostics')

with st.expander('Metadata details', expanded=True):
    # Note: In the debug page context, we're stepping through manually,
    # so we simulate the full pipeline context for metadata calculation
    if 'cycles' in locals() and cycles is not None:
        metadata = step7_diagnostics(df_raw, df_step2, cycles, avg_cycle_m, stats)

        # Display metadata metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric('Cycles Detected', metadata['capture_length'], help='Number of complete strokes')

        # Sampling status with background color
        with col_m2:
            if metadata['sampling_is_stable']:
                st.success('Sampling Status: Stable')
            else:
                st.warning('Sampling Status: Unstable')

        if metadata['sampling_cv'] is not None:
            col_m3.metric('Sampling CV', f'{metadata["sampling_cv"]:.2f}%', help='Coefficient of variation')

        # Row drops
        if metadata['rows_dropped'] > 0:
            st.info(f'{metadata["rows_dropped"]} rows dropped during processing')

        # Warnings
        if metadata['warnings']:
            for warning in metadata['warnings']:
                st.warning(f'Quality Alert: {warning}')
        else:
            st.success('Quality Status: Clear')

    _ok('Pipeline completed successfully — all six steps produced valid output.')

st.divider()
st.caption(
    'This page is intended for debugging only. To view the full coaching report, use the main **Rowing Analysis Report** page.'
)
