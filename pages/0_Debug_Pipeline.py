import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import os

from rowing_catch.algo.steps.step0_validation import validate_input_df
from rowing_catch.algo.steps.step1_rename import step1_rename_columns
from rowing_catch.algo.steps.step2_smoothing import step2_smooth
from rowing_catch.algo.steps.step3_detection import step3_detect_catches
from rowing_catch.algo.steps.step4_segmentation import step4_segment_and_average
from rowing_catch.algo.steps.step5_metrics import step5_compute_metrics
from rowing_catch.algo.steps.step6_statistics import step6_statistics
from rowing_catch.algo.steps.step7_diagnostics import step7_diagnostics
from rowing_catch.algo.steps.step5_metrics import _pick_finish_index
from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES, PROCESSED_COLUMN_NAMES
from rowing_catch.scenario.scenarios import create_scenario_data, get_trunk_scenarios
from rowing_catch.ui.utils import (
    setup_premium_plot, COLOR_MAIN, COLOR_SEAT, COLOR_HANDLE, COLOR_ARMS,
    COLOR_CATCH, COLOR_FINISH, COLOR_COMPARE,
    BG_COLOR_FIGURE, BG_COLOR_AXES, COLOR_TEXT_MAIN, COLOR_TEXT_SUB
)

st.set_page_config(page_title="Debug: Data Pipeline", layout="wide")

st.title("Data Processing Pipeline — Debug View")
st.markdown(
    "This page runs the analysis pipeline step-by-step and exposes the **intermediate "
    "state of the data** after each step. Use it to spot where numbers go wrong."
)

# ---------------------------------------------------------------------------
# Data source selection
# ---------------------------------------------------------------------------
st.sidebar.header("Data Source")
source = st.sidebar.radio("Choose input", ["CSV Upload", "Built-in Scenario"], index=0)

df_raw: pd.DataFrame | None = None
data_label = ""

if source == "CSV Upload":
    uploaded = st.sidebar.file_uploader("Upload trajectory CSV", type="csv")
    if uploaded:
        df_raw = pd.read_csv(uploaded)
        data_label = uploaded.name

    resource_dir = "resources"
    if os.path.exists(resource_dir):
        example_files = sorted(
            f for f in os.listdir(resource_dir)
            if f.endswith(".csv") and "trajectory" in f.lower()
        )
        default_file = "2023.12.27.Szabi_36strokesPerMinute_trajectory.csv"
        default_index = 0
        if default_file in example_files:
            default_index = example_files.index(default_file) + 1 # +1 for "None"
            
        selected_example = st.sidebar.selectbox(
            "Or pick an example file", ["None"] + example_files,
            index=default_index
        )
        if selected_example != "None" and df_raw is None:
            df_raw = pd.read_csv(os.path.join(resource_dir, selected_example))
            data_label = selected_example
else:
    scenarios = get_trunk_scenarios()
    selected_scenario = st.sidebar.selectbox(
        "Scenario", list(scenarios.keys()), index=0
    )
    df_raw = create_scenario_data("Trunk", selected_scenario)
    data_label = f"Scenario: {selected_scenario}"

if df_raw is None:
    st.info("Select a data source in the sidebar to begin.")
    st.stop()

st.caption(f"**Input:** {data_label} — {len(df_raw):,} rows × {len(df_raw.columns)} columns")

WINDOW = 10

# ---------------------------------------------------------------------------
# Helper: a small reusable banner for each step
# ---------------------------------------------------------------------------
def _phase_header(title: str, subtitle: str):
    """Render a wide, amber-accented phase-level divider banner."""
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"background:#1c1a12;padding:10px 14px;border-radius:10px;"
        f"border-left:5px solid #f59e0b;margin:20px 0 10px 0;"
        f"font-family:inherit;'>"
        f"<div style='display:flex;align-items:center;gap:12px;'>"
        f"<span style='color:#fbbf24;font-size:10px;font-weight:800;letter-spacing:1.5px;"
        f"text-transform:uppercase'>PHASE</span>"
        f"<strong style='color:#fef3c7;font-size:16px;margin:0;letter-spacing:0.3px'>{title}</strong>"
        f"</div>"
        f"<span style='color:#92400e;font-size:12px;margin:0;font-style:italic;'>{subtitle}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _step_header(number: int, title: str, subtitle: str):
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"background:#1e293b;padding:6px 10px;border-radius:8px;border-left:4px solid #6366f1;"
        f"margin-bottom:6px;font-family:inherit;font-size:14px;'>"
        f"<div style='display:flex;align-items:center;gap:10px;'>"
        f"<span style='color:#a5b4fc;font-size:11px;font-weight:700;letter-spacing:1px;"
        f"text-transform:uppercase'>STEP {number}</span>"
        f"<strong style='color:#f1f5f9;font-size:14px;margin:0'>{title}</strong>"
        f"</div>"
        f"<span style='color:#94a3b8;font-size:12px;margin:0;white-space:nowrap;'>{subtitle}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _ok(msg: str):
    st.success(f"{msg}")


def _fail(msg: str):
    st.error(f"{msg}")
    st.stop()


# ===========================================================================
# PHASE 1 — Raw Data Intake & Validation
# ===========================================================================
_phase_header(
    "Raw Data Intake & Validation",
    "Steps 0–1 · Ingest raw CSV, verify required columns exist, and normalise column names",
)

# ===========================================================================
# STEP 0 — Validation
# ===========================================================================
_step_header(0, "Validation", "Ensure input DataFrame has required columns and enough data.")

with st.expander("Step 0 details", expanded=False):
    try:
        validate_input_df(df_raw)
        _ok("Input validation passed.")
    except Exception as e:
        _fail(f"Input validation failed: {e}")


# ===========================================================================
# STEP 1 — Rename columns
# ===========================================================================
_step_header(1, "Rename Columns", "Map raw tracker names → clean internal names.")

with st.expander("Step 1 details", expanded=False):
    df_step1 = step1_rename_columns(df_raw)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Column mapping:**")
        rename_rows = []
        for raw, clean in REQUIRED_COLUMN_NAMES.items():
            found = raw in df_raw.columns
            rename_rows.append({"Raw column": raw, "Clean column": clean, "Found": "Found" if found else "Missing"})
        st.dataframe(pd.DataFrame(rename_rows), width='stretch', hide_index=True)

    with col_b:
        st.markdown("**Output columns:**")
        col_df = pd.DataFrame({
            "Column": df_step1.columns.tolist(),
            "dtype": [str(dt) for dt in df_step1.dtypes],
            "non-null": df_step1.count().values,
        })
        st.dataframe(col_df, width='stretch', hide_index=True)

    missing = [c for c in REQUIRED_COLUMN_NAMES.values() if c not in df_step1.columns]
    if missing:
        _fail(f"Missing required columns after rename: {missing}")
    else:
        _ok(f"{len(df_step1):,} rows, all required columns present.")

# ===========================================================================
# PHASE 2 — Signal Conditioning
# ===========================================================================
_phase_header(
    "Signal Conditioning",
    "Step 2 · Apply centred rolling-mean smoothing to suppress high-frequency sensor noise before analysis",
)

# ===========================================================================
# STEP 2 — Smooth
# ===========================================================================
_step_header(2, "Smooth", f"Apply centred rolling mean (window={WINDOW}) to position columns.")

with st.expander("Step 2 details", expanded=False):
    df_step2 = step2_smooth(df_step1, window=WINDOW)

    _ok(f"Rows after smoothing: {len(df_step2):,} (all rows preserved, including edges with min_periods=1).")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Before vs. after — `Seat_X`:**")
        fig, ax = setup_premium_plot(xlabel='Sample index', ylabel='Seat_X', figsize=(5, 2.5))
        ax.plot(df_step1.index, df_step1.get('Seat_X', pd.Series(dtype=float)),
                color=COLOR_COMPARE, linewidth=0.8, label='Raw')
        ax.plot(df_step2.index, df_step2['Seat_X_Smooth'],
                color=COLOR_SEAT, linewidth=1.5, label='Smoothed')
        ax.legend(fontsize=8)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    with col_right:
        st.markdown("**Before vs. after — `Handle_X`:**")
        fig, ax = setup_premium_plot(xlabel='Sample index', ylabel='Handle_X', figsize=(5, 2.5))
        ax.plot(df_step1.index, df_step1.get('Handle_X', pd.Series(dtype=float)),
                color=COLOR_COMPARE, linewidth=0.8, label='Raw')
        ax.plot(df_step2.index, df_step2['Handle_X_Smooth'],
                color=COLOR_HANDLE, linewidth=1.5, label='Smoothed')
        ax.legend(fontsize=8)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    st.markdown("**Smoothed column stats:**")
    smooth_cols = [f'{c}_Smooth' for c in PROCESSED_COLUMN_NAMES if f'{c}_Smooth' in df_step2.columns]
    st.dataframe(df_step2[smooth_cols].describe().T.round(2), width='stretch')

# ===========================================================================
# PHASE 3 — Stroke Segmentation
# ===========================================================================
_phase_header(
    "Stroke Segmentation",
    "Steps 3–4 · Detect each catch event, slice the recording into individual stroke cycles, time-align and average them",
)

# ===========================================================================
# STEP 3 — Detect catches
# ===========================================================================
_step_header(3, "Detect Catches", "Interpolate small gaps and find local minima of Seat_X_Smooth.")

with st.expander("Step 3 details", expanded=False):
    df_step3, catch_indices = step3_detect_catches(df_step2, window=WINDOW)

    n_catches = len(catch_indices)
    if n_catches < 2:
        _fail(f"Only {n_catches} catch(es) detected — need at least 2 to form a cycle.")

    _ok(f"{n_catches} catches detected at indices: {catch_indices.tolist()}")

    fig, ax1 = setup_premium_plot(
        title='Seat_X_Smooth — local minima = catches (one per stroke)',
        ylabel='Seat_X_Smooth', figsize=(10, 3)
    )

    ax1.plot(df_step3.index, df_step3['Seat_X_Smooth'],
             color=COLOR_SEAT, linewidth=1.2, label='Seat_X_Smooth (detection signal)')
    ax1.fill_between(df_step3.index, df_step3['Seat_X_Smooth'],
                     df_step3['Seat_X_Smooth'].min(), color=COLOR_SEAT, alpha=0.08)
    for ci in catch_indices:
        ax1.axvline(ci, color=COLOR_CATCH, linewidth=1, linestyle='--', alpha=0.8)
    ax1.scatter(catch_indices, df_step3['Seat_X_Smooth'].iloc[catch_indices],
                color=COLOR_CATCH, s=60, zorder=5, label='Detected Catch (local min)')
    ax1.legend(fontsize=8)

    st.pyplot(fig, width='stretch')
    plt.close(fig)

    st.markdown("**Catch-to-catch intervals (samples):**")
    intervals = np.diff(catch_indices).tolist()
    st.dataframe(
        pd.DataFrame({"Catch #": list(range(1, len(intervals) + 1)),
                      "Start index": catch_indices[:-1].tolist(),
                      "End index": catch_indices[1:].tolist(),
                      "Interval (samples)": intervals}),
        width='stretch',
        hide_index=True,
    )

# ===========================================================================
# STEP 4 — Segment & Average
# ===========================================================================
_step_header(4, "Segment & Average", "Cut data into per-stroke cycles and average them.")

with st.expander("Step 4 details", expanded=False):
    result4 = step4_segment_and_average(df_step3, catch_indices, window=WINDOW)

    if result4 is None:
        _fail("Could not extract any valid cycles.")

    cycles, avg_cycle, min_length = result4
    _ok(f"{len(cycles)} valid cycle(s) extracted. Shortest: {min_length} samples — used as average length.")

    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Cycle lengths:**")
        cycle_df = pd.DataFrame({
            "Cycle #": list(range(1, len(cycles) + 1)),
            "Length (samples)": [len(c) for c in cycles],
            "Seat_X range": [f"{c['Seat_X_Smooth'].min():.1f} – {c['Seat_X_Smooth'].max():.1f}"
                             for c in cycles],
        })
        st.dataframe(cycle_df, width='stretch', hide_index=True)

    with col_r:
        st.markdown("**Averaged Seat_X (all cycles overlaid):**")

        # Build per-cycle arrays and mean/std bands
        cycle_arrays = [c['Seat_X_Smooth'].to_numpy(dtype=float)[:min_length] for c in cycles]
        x_idx = np.arange(min_length)
        stack = np.vstack(cycle_arrays)
        mean_vals = stack.mean(axis=0)
        std_vals = stack.std(axis=0)

        fig, ax = setup_premium_plot(
            xlabel='Cycle Index', ylabel='Seat_X_Smooth (mm)', figsize=(5, 3)
        )
        # Individual cycles (faded)
        for arr in cycle_arrays:
            ax.plot(x_idx, arr, color='#cbd5e1', linewidth=0.8, alpha=0.4)
        # ±1 SD confidence band
        ax.fill_between(x_idx, mean_vals - std_vals, mean_vals + std_vals,
                        color=COLOR_MAIN, alpha=0.15, label='±1 SD')
        # Average cycle (bold)
        ax.plot(x_idx, mean_vals, color=COLOR_MAIN, linewidth=2, label='Mean cycle')
        ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
        st.pyplot(fig, width='stretch')
        plt.close(fig)

# ===========================================================================
# PHASE 4 — Biomechanical Metrics on the Average Cycle
# ===========================================================================
_phase_header(
    "Biomechanical Metrics on the Average Cycle",
    "Step 5 · Derive trunk angle, velocities, acceleration, jerk, and drive-phase power proxy from the averaged stroke",
)

# ===========================================================================
# STEP 5 — Compute metrics
# ===========================================================================
_step_header(5, "Compute Metrics",
             "Calculate Trunk_Angle, velocities, and locate catch/finish (reversal-based) on the averaged cycle.")

with st.expander("Step 5 details", expanded=True):
    avg_cycle_m, catch_idx, finish_idx = step5_compute_metrics(avg_cycle, window=WINDOW)

    # --- Experimental Metrics Calculations ---
    if 'Shoulder_X_Smooth' in avg_cycle_m.columns:
        if 'Time' in avg_cycle_m.columns:
            t = avg_cycle_m['Time'].to_numpy(dtype=float)
            avg_cycle_m['Shoulder_X_Vel'] = np.gradient(avg_cycle_m['Shoulder_X_Smooth'], t)
        else:
            avg_cycle_m['Shoulder_X_Vel'] = np.gradient(avg_cycle_m['Shoulder_X_Smooth'])
        
        avg_cycle_m['Rower_Vel'] = (avg_cycle_m['Seat_X_Vel'] + avg_cycle_m['Shoulder_X_Vel']) / 2
        avg_cycle_m['Shoulder_rel_Seat_Vel'] = avg_cycle_m['Shoulder_X_Vel'] - avg_cycle_m['Seat_X_Vel']
    
    avg_cycle_m['Handle_rel_Seat_Vel'] = avg_cycle_m['Handle_X_Vel'] - avg_cycle_m['Seat_X_Vel']
    
    if 'Time' in avg_cycle_m.columns:
        t = avg_cycle_m['Time'].to_numpy(dtype=float)
        avg_cycle_m['Handle_X_Accel'] = np.gradient(avg_cycle_m['Handle_X_Vel'], t)
        avg_cycle_m['Handle_X_Jerk'] = np.gradient(avg_cycle_m['Handle_X_Accel'], t)
    else:
        avg_cycle_m['Handle_X_Accel'] = np.gradient(avg_cycle_m['Handle_X_Vel'])
        avg_cycle_m['Handle_X_Jerk'] = np.gradient(avg_cycle_m['Handle_X_Accel'])
    
    # Power Curve calculation is restricted to the drive phase
    avg_cycle_m['Power_Proxy'] = 0.0
    drive_mask = (avg_cycle_m.index >= catch_idx) & (avg_cycle_m.index <= finish_idx)
    avg_cycle_m.loc[drive_mask, 'Power_Proxy'] = np.maximum(
        0, 
        avg_cycle_m.loc[drive_mask, 'Handle_X_Vel'] * avg_cycle_m.loc[drive_mask, 'Handle_X_Accel']
    )



    catch_angle = float(avg_cycle_m.loc[catch_idx, 'Trunk_Angle'])
    finish_angle = float(avg_cycle_m.loc[finish_idx, 'Trunk_Angle'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Catch index", catch_idx)
    col2.metric("Finish index", finish_idx)
    col3.metric("Drive length (samples)", finish_idx - catch_idx)

    col4, col5 = st.columns(2)
    col4.metric("Trunk angle @ Catch", f"{catch_angle:.1f}°")
    col5.metric("Trunk angle @ Finish", f"{finish_angle:.1f}°")

    st.markdown("**Catch + Finish on averaged cycle**")
    fig, ax1 = setup_premium_plot(xlabel='Cycle sample index (time)', ylabel='Seat X (mm)', figsize=(9, 5))
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    
    # 1. Seat X (Left axis)
    ax1.plot(avg_cycle_m.index, avg_cycle_m['Seat_X_Smooth'],
             color=COLOR_SEAT, linewidth=2, label='Seat_X_Smooth')
    ax1.set_ylabel('Seat X (mm)', color=COLOR_SEAT)
    ax1.tick_params(axis='y', labelcolor=COLOR_SEAT)
    
    def _rescale_ax(ax, data, pad=0.15):
        ymin, ymax = np.nanmin(data), np.nanmax(data)
        if np.isnan(ymin) or np.isnan(ymax):
            return
        diff = ymax - ymin
        r = diff * pad if diff > 0 else 1.0
        ax.set_ylim(ymin - r, ymax + r)

    _rescale_ax(ax1, avg_cycle_m['Seat_X_Smooth'])
    ax1.invert_yaxis()

    # 2. Handle X (Right axis)
    ax2 = ax1.twinx()
    ax2.plot(avg_cycle_m.index, avg_cycle_m['Handle_X_Smooth'],
             color=COLOR_HANDLE, linewidth=1.5, linestyle='--', label='Handle_X_Smooth')
    ax2.set_ylabel('Handle X (mm)', color=COLOR_HANDLE)
    ax2.tick_params(axis='y', labelcolor=COLOR_HANDLE)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_color('#DDDDDD')
    _rescale_ax(ax2, avg_cycle_m['Handle_X_Smooth'])
    ax2.invert_yaxis()

    # 3. Shoulder X (Offset Right axis)
    if 'Shoulder_X_Smooth' in avg_cycle_m.columns:
        ax3 = ax1.twinx()
        # Offset the third axis to the right
        ax3.spines['right'].set_position(('outward', 60))
        ax3.spines['right'].set_color('#DDDDDD')
        ax3.spines['top'].set_visible(False)
        ax3.plot(avg_cycle_m.index, avg_cycle_m['Shoulder_X_Smooth'],
                 color=COLOR_ARMS, linewidth=1.5, linestyle='-.', label='Shoulder_X_Smooth')
        ax3.set_ylabel('Shoulder X (mm)', color=COLOR_ARMS)
        ax3.tick_params(axis='y', labelcolor=COLOR_ARMS)
        _rescale_ax(ax3, avg_cycle_m['Shoulder_X_Smooth'])
        ax3.invert_yaxis()
    
    # Common markers — no legend labels; annotate directly on the plot instead
    ax1.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.4, alpha=0.8)
    catch_y = float(avg_cycle_m.loc[catch_idx, 'Seat_X_Smooth'])
    ax1.scatter([catch_idx], [catch_y], color=COLOR_CATCH, s=80, marker='o', zorder=5)
    ax1.annotate(
        'Catch', xy=(catch_idx, catch_y),
        xytext=(catch_idx + max(1, len(avg_cycle_m) * 0.01), catch_y),
        color=COLOR_CATCH, fontsize=8, fontweight='bold', va='center',
    )

    ax1.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.4, alpha=0.8)
    finish_y = float(avg_cycle_m.loc[finish_idx, 'Seat_X_Smooth'])
    ax1.scatter([finish_idx], [finish_y], color=COLOR_FINISH, s=80, marker='X', zorder=5)
    ax1.annotate(
        'Finish', xy=(finish_idx, finish_y),
        xytext=(finish_idx + max(1, len(avg_cycle_m) * 0.01), finish_y),
        color=COLOR_FINISH, fontsize=8, fontweight='bold', va='center',
    )

    # Front stop / Back stop — seat travel limits; label on the right edge of the line
    seat_min = float(avg_cycle_m['Seat_X_Smooth'].min())
    seat_max = float(avg_cycle_m['Seat_X_Smooth'].max())
    x_end = float(avg_cycle_m.index.max())
    ax1.axhline(seat_min, color=COLOR_CATCH, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(x_end, seat_min, 'Front stop',
             color=COLOR_CATCH, fontsize=8, fontweight='bold',
             va='top', ha='right')
    ax1.axhline(seat_max, color=COLOR_FINISH, linestyle=':', linewidth=1.5, alpha=0.7)
    ax1.text(x_end, seat_max, 'Back stop',
             color=COLOR_FINISH, fontsize=8, fontweight='bold',
             va='bottom', ha='right')

    ax1.grid(axis='x', alpha=0.2)

    # Legend: only the data lines (Seat, Handle, Shoulder) — event labels are now on the plot
    legend_lines, legend_labels = ax1.get_legend_handles_labels()
    legend_lines2, legend_labels2 = ax2.get_legend_handles_labels()
    all_lines = legend_lines + legend_lines2
    all_labels = legend_labels + legend_labels2
    if 'Shoulder_X_Smooth' in avg_cycle_m.columns:
        legend_lines3, legend_labels3 = ax3.get_legend_handles_labels()
        all_lines += legend_lines3
        all_labels += legend_labels3

    ax1.legend(all_lines, all_labels, loc='upper center', bbox_to_anchor=(0.5, 0.98),
               ncol=min(3, len(all_lines)),
               fontsize=8, framealpha=0.8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # --- Production Heuristic Visualization (Debug Enhancement) ---
    st.markdown("**All detected Catches & Finishes (Full Trajectory)**")
    st.caption("This plot shows where the *production* heuristic would place the finish for every individual cycle.")
    
    # 1. To use the production heuristic (_pick_finish_index), we need Trunk_Angle on the full signal.
    df_debug = df_step3.copy()
    ref_catch = df_debug.iloc[catch_indices[0]] if len(catch_indices) > 0 else df_debug.iloc[0]
    is_facing_left = ref_catch['Handle_X_Smooth'] < ref_catch['Seat_X_Smooth']

    def _calc_trunk_angle_debug(row):
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        dy_abs = abs(dy)
        return np.degrees(np.arctan2(dx if is_facing_left else -dx, dy_abs))

    df_debug['Trunk_Angle'] = df_debug.apply(_calc_trunk_angle_debug, axis=1)

    # 2. Iterate through each cycle and pick the finish using production logic
    production_finish_indices = []
    for i in range(len(catch_indices) - 1):
        idx_start = catch_indices[i]
        idx_end = catch_indices[i+1]
        
        # Slice the cycle (catch to catch)
        cycle_slice = df_debug.iloc[idx_start:idx_end]
        
        # Use production heuristic (pretending this is an avg cycle)
        # Note: catch_idx=0 because cycle_slice starts at the catch
        rel_finish = _pick_finish_index(cycle_slice, catch_idx=0)
        production_finish_indices.append(idx_start + rel_finish)
    
    production_finish_indices = np.array(production_finish_indices, dtype=int)

    # 3. Full-trajectory matplotlib plot
    sample_idx = df_debug.index.to_numpy()
    fig, ax = setup_premium_plot(
        title='Full Trajectory: Seat_X (Raw vs Smoothed) with Detected Events',
        xlabel='Sample Index', ylabel='Seat_X (mm)', figsize=(10, 3.5)
    )
    # Raw signal (faded)
    if 'Seat_X' in df_debug.columns:
        ax.plot(sample_idx, df_debug['Seat_X'], color=COLOR_COMPARE,
                linewidth=0.8, alpha=0.4, label='Raw Seat_X')
    # Smoothed signal
    ax.plot(sample_idx, df_debug['Seat_X_Smooth'], color=COLOR_SEAT,
            linewidth=1.5, label='Smoothed Seat_X')
    # Catch markers
    for ci in catch_indices:
        ax.axvline(ci, color=COLOR_CATCH, linewidth=1, linestyle='--', alpha=0.7)
    ax.scatter(
        catch_indices,
        df_debug['Seat_X_Smooth'].iloc[catch_indices],
        color=COLOR_CATCH, s=50, zorder=5, label='Catch'
    )
    # Production finish markers
    for fi in production_finish_indices:
        ax.axvline(fi, color=COLOR_FINISH, linewidth=1, linestyle='--', alpha=0.7)
    ax.scatter(
        production_finish_indices,
        df_debug['Seat_X_Smooth'].iloc[production_finish_indices],
        color=COLOR_FINISH, marker='X', s=60, zorder=5, label='Finish'
    )
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # Trunk angle plot
    st.markdown("**Trunk Angle across the averaged stroke:**")
    fig, ax = setup_premium_plot(xlabel='Cycle index', ylabel='Degrees from vertical', figsize=(10, 3))
    ax.plot(avg_cycle_m.index, avg_cycle_m['Trunk_Angle'],
            color=COLOR_MAIN, linewidth=2, label='Trunk Angle')
    ax.fill_between(avg_cycle_m.index, avg_cycle_m['Trunk_Angle'], 0, color=COLOR_MAIN, alpha=0.08)
    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.5, label=f'Catch ({catch_angle:.1f}°)')
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.5, label=f'Finish ({finish_angle:.1f}°)')
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # Detailed Velocity plot
    st.markdown("**Detailed Velocity (Seat, Handle, Shoulder, Rower):**")
    fig, ax = setup_premium_plot(xlabel='Cycle index', ylabel='Velocity (px/sample)', figsize=(10, 3.5))
    ax.plot(avg_cycle_m.index, avg_cycle_m['Handle_X_Vel'], color=COLOR_HANDLE, linewidth=1.5, label='Handle')
    ax.fill_between(avg_cycle_m.index, avg_cycle_m['Handle_X_Vel'], 0, color=COLOR_HANDLE, alpha=0.08)
    ax.plot(avg_cycle_m.index, avg_cycle_m['Seat_X_Vel'], color=COLOR_SEAT, linewidth=1.5, label='Seat')
    ax.fill_between(avg_cycle_m.index, avg_cycle_m['Seat_X_Vel'], 0, color=COLOR_SEAT, alpha=0.08)
    if 'Shoulder_X_Vel' in avg_cycle_m.columns:
        ax.plot(avg_cycle_m.index, avg_cycle_m['Shoulder_X_Vel'], color=COLOR_ARMS, linewidth=1.2, linestyle='--', label='Shoulder')
        ax.plot(avg_cycle_m.index, avg_cycle_m['Rower_Vel'], color=COLOR_MAIN, linewidth=2, label='Rower (Torso)')
    ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
    ax.legend(fontsize=8, loc='upper right', facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        # Relative Velocity
        st.markdown("**Relative Velocity (vs. Seat):**")
        fig, ax = setup_premium_plot(ylabel='Relative Velocity', figsize=(5, 3))
        ax.plot(avg_cycle_m.index, avg_cycle_m['Handle_rel_Seat_Vel'], color=COLOR_HANDLE, linewidth=1.5, label='Handle - Seat')
        ax.fill_between(avg_cycle_m.index, avg_cycle_m['Handle_rel_Seat_Vel'], 0, color=COLOR_HANDLE, alpha=0.08)
        if 'Shoulder_rel_Seat_Vel' in avg_cycle_m.columns:
            ax.plot(avg_cycle_m.index, avg_cycle_m['Shoulder_rel_Seat_Vel'], color=COLOR_ARMS, linewidth=1.5, label='Shoulder - Seat')
        ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
        ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
        ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
        ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    with col_v2:
        # Jerk
        st.markdown("**Handle Jerk (Smoothness):**")
        fig, ax = setup_premium_plot(ylabel='Jerk (mm/s³)', figsize=(5, 3))
        ax.plot(avg_cycle_m.index, avg_cycle_m['Handle_X_Jerk'], color='#ec4899', linewidth=1.5, label='Handle Jerk')
        ax.fill_between(avg_cycle_m.index, avg_cycle_m['Handle_X_Jerk'], 0, color='#ec4899', alpha=0.08)
        ax.axhline(0, color='#888888', linestyle=':', linewidth=1, alpha=0.5)
        ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', linewidth=1.2)
        ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', linewidth=1.2)
        ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    # Power Curve
    st.markdown("**Power Curve (Proxy: Velocity × Acceleration):**")
    fig, ax = setup_premium_plot(xlabel='Handle Position (mm)', ylabel='Power Proxy (v * a)', figsize=(10, 3.5))
    drive_slice = avg_cycle_m.iloc[catch_idx:finish_idx]
    if not drive_slice.empty:
        ax.fill_between(drive_slice['Handle_X_Smooth'], drive_slice['Power_Proxy'], color=COLOR_FINISH, alpha=0.25)
        ax.plot(drive_slice['Handle_X_Smooth'], drive_slice['Power_Proxy'], color=COLOR_FINISH, linewidth=2, label='Drive Power')
    
    ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    with st.expander("Raw averaged cycle DataFrame (all computed columns)"):

        st.dataframe(avg_cycle_m.round(3), width='stretch')

# ===========================================================================
# PHASE 5 — Stroke-Level Statistics
# ===========================================================================
_phase_header(
    "Stroke-Level Statistics",
    "Step 6 · Aggregate scalar metrics across all individual cycles: consistency CV, SPM, drive/recovery ratio and temporal durations",
)

# ===========================================================================
# STEP 6 — Statistics
# ===========================================================================
_step_header(6, "Statistics", "Summarise stroke consistency, drive/recovery ratio.")

with st.expander("Step 6 details", expanded=True):
    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx, avg_cycle_m)

    cv = stats['cv_length']
    drive_len = stats['drive_len']
    recovery_len = stats['recovery_len']
    drive_pct = drive_len / min_length * 100
    rec_pct = recovery_len / min_length * 100

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Consistency CV", f"{cv:.2f}%", help="Lower is better. Target < 2%.")
    col_s2.metric("Drive / Recovery", f"{drive_pct:.1f}% / {rec_pct:.1f}%")
    col_s3.metric("Avg cycle duration", f"{stats['mean_duration']:.0f} samples")

    # Bar chart for drive vs recovery
    fig, ax = plt.subplots(figsize=(4, 2))
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)
    bars = ax.barh(['Drive', 'Recovery'], [drive_pct, rec_pct],
                   color=[COLOR_MAIN, COLOR_CATCH], height=0.4)
    ax.bar_label(bars, fmt='%.1f%%', padding=4, fontsize=9, color=COLOR_TEXT_MAIN)
    ax.set_xlim(0, 100)
    ax.set_xlabel('%', color=COLOR_TEXT_SUB)
    ax.tick_params(colors=COLOR_TEXT_SUB)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDDD')
    st.pyplot(fig, width='content')
    plt.close(fig)

    # --- Ratio & Rhythm Spread Diagram ---
    st.markdown("**Ratio & Rhythm Spread (Consistency):**")
    
    cycle_data = []
    for i, c in enumerate(cycles):
        if 'Time' in c.columns and len(c) > 1:
            t = c['Time'].to_numpy(dtype=float)
            duration = t[-1] - t[0]
            if duration > 0:
                spm = 60.0 / duration
                # Find finish for this specific cycle using the same heuristic
                f_idx = _pick_finish_index(c, catch_idx=0)
                drive_dur = t[f_idx] - t[0]
                rec_dur = duration - drive_dur
                ratio = drive_dur / rec_dur if rec_dur > 0 else np.nan
                cycle_data.append({
                    'Cycle': i + 1,
                    'SPM': round(spm, 1),
                    'Ratio_DR': round(ratio, 2),
                    'Drive (s)': round(drive_dur, 2),
                    'Recovery (s)': round(rec_dur, 2)
                })
    
    if cycle_data:
        df_spread = pd.DataFrame(cycle_data)

        fig, ax = setup_premium_plot(
            title='Stroke-by-Stroke Rhythm Consistency',
            xlabel='Strokes Per Minute (SPM)',
            ylabel='Drive:Recovery Ratio',
            figsize=(7, 4)
        )
        spm_vals = df_spread['SPM'].to_numpy(dtype=float)
        ratio_vals = df_spread['Ratio_DR'].to_numpy(dtype=float)
        cycle_nums = df_spread['Cycle'].to_numpy()

        # Mean crosshair lines
        ax.axvline(float(np.nanmean(spm_vals)), color='#94a3b8',
                   linewidth=1, linestyle='--', alpha=0.7, label='Mean SPM')
        ax.axhline(float(np.nanmean(ratio_vals)), color='#94a3b8',
                   linewidth=1, linestyle='--', alpha=0.7, label='Mean D:R')

        # Scatter points
        ax.scatter(spm_vals, ratio_vals, color=COLOR_MAIN, s=80, zorder=5)

        # Cycle number labels next to each point
        for cx, cy, label in zip(spm_vals, ratio_vals, cycle_nums):
            ax.annotate(
                str(label), (cx, cy),
                textcoords='offset points', xytext=(6, 4),
                fontsize=8, color=COLOR_TEXT_SUB
            )

        ax.legend(fontsize=8, facecolor=BG_COLOR_AXES, edgecolor='#DDDDDD')
        st.pyplot(fig, width='stretch')
        plt.close(fig)
    else:
        st.info("Insufficient time data to calculate stroke-by-stroke rhythm spread.")


# ===========================================================================
# PHASE 6 — Data Quality & Diagnostics
# ===========================================================================
_phase_header(
    "Data Quality & Diagnostics",
    "Step 7 · Assess sampling stability, count rows dropped, and surface any pipeline warnings",
)

st.markdown("### Data Quality & Metadata Diagnostics")

with st.expander("Metadata details", expanded=True):
    # Note: In the debug page context, we're stepping through manually,
    # so we simulate the full pipeline context for metadata calculation
    if 'cycles' in locals() and cycles is not None:
        metadata = step7_diagnostics(df_raw, df_step2, cycles, avg_cycle_m, stats)
        
        # Display metadata metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Cycles Detected", metadata['capture_length'], help="Number of complete strokes")
        
        # Sampling status with background color
        with col_m2:
            if metadata['sampling_is_stable']:
                st.success("Sampling Status: Stable")
            else:
                st.warning("Sampling Status: Unstable")
                
        if metadata['sampling_cv'] is not None:
            col_m3.metric("Sampling CV", f"{metadata['sampling_cv']:.2f}%", help="Coefficient of variation")
        
        # Row drops
        if metadata['rows_dropped'] > 0:
            st.info(f"{metadata['rows_dropped']} rows dropped during processing")
        
        # Warnings
        if metadata['warnings']:
            for warning in metadata['warnings']:
                st.warning(f"Quality Alert: {warning}")
        else:
            st.success("Quality Status: Clear")

    _ok("Pipeline completed successfully — all six steps produced valid output.")

st.divider()
st.caption(
    "This page is intended for debugging only. To view the full coaching report, "
    "use the main **Rowing Analysis Report** page."
)
