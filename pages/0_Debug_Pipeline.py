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
from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES, PROCESSED_COLUMN_NAMES
from rowing_catch.algo.scenarios import create_scenario_data, get_trunk_scenarios

st.set_page_config(page_title="Debug: Data Pipeline", layout="wide")

st.title("🔬 Data Processing Pipeline — Debug View")
st.markdown(
    "This page runs the analysis pipeline step-by-step and exposes the **intermediate "
    "state of the data** after each step. Use it to spot where numbers go wrong."
)

# ---------------------------------------------------------------------------
# Data source selection
# ---------------------------------------------------------------------------
st.sidebar.header("Data Source")
source = st.sidebar.radio("Choose input", ["CSV Upload", "Built-in Scenario"], index=1)

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
        selected_example = st.sidebar.selectbox(
            "Or pick an example file", ["None"] + example_files
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
    st.info("👈 Select a data source in the sidebar to begin.")
    st.stop()

st.caption(f"**Input:** {data_label} — {len(df_raw):,} rows × {len(df_raw.columns)} columns")

WINDOW = 10

# ---------------------------------------------------------------------------
# Helper: a small reusable banner for each step
# ---------------------------------------------------------------------------
def _step_header(number: int, title: str, subtitle: str):
    st.markdown(
        f"<div style='background:#1e293b;padding:10px 16px;border-radius:8px;"
        f"border-left:4px solid #6366f1;margin-bottom:8px'>"
        f"<span style='color:#a5b4fc;font-size:11px;font-weight:600;letter-spacing:1px'>"
        f"STEP {number}</span>"
        f"<h4 style='color:#f1f5f9;margin:2px 0 0'>{title}</h4>"
        f"<p style='color:#94a3b8;margin:0;font-size:13px'>{subtitle}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _ok(msg: str):
    st.success(f"✅ {msg}")


def _fail(msg: str):
    st.error(f"❌ {msg}")
    st.stop()


# ===========================================================================
# STEP 0 — Validation
# ===========================================================================
_step_header(0, "Validation", "Ensure input DataFrame has required columns and enough data.")

with st.expander("Step 0 details", expanded=True):
    try:
        validate_input_df(df_raw)
        _ok("Input validation passed.")
    except Exception as e:
        _fail(f"Input validation failed: {e}")


# ===========================================================================
# STEP 1 — Rename columns
# ===========================================================================
_step_header(1, "Rename Columns", "Map raw tracker names → clean internal names.")

with st.expander("Step 1 details", expanded=True):
    df_step1 = step1_rename_columns(df_raw)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Column mapping:**")
        rename_rows = []
        for raw, clean in REQUIRED_COLUMN_NAMES.items():
            found = raw in df_raw.columns
            rename_rows.append({"Raw column": raw, "Clean column": clean, "Found": "✅" if found else "⚠️ missing"})
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
# STEP 2 — Smooth
# ===========================================================================
_step_header(2, "Smooth", f"Apply centred rolling mean (window={WINDOW}) to position columns.")

with st.expander("Step 2 details", expanded=True):
    df_step2 = step2_smooth(df_step1, window=WINDOW)

    _ok(f"Rows after smoothing: {len(df_step2):,} (all rows preserved, including edges with min_periods=1).")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Before vs. after — `Seat_X`:**")
        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(df_step1.index, df_step1.get('Seat_X', pd.Series(dtype=float)),
                color='#94a3b8', linewidth=0.8, label='Raw')
        ax.plot(df_step2.index, df_step2['Seat_X_Smooth'],
                color='#6366f1', linewidth=1.5, label='Smoothed')
        ax.set_xlabel('Sample index'); ax.set_ylabel('Seat_X')
        ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    with col_right:
        st.markdown("**Before vs. after — `Handle_X`:**")
        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.plot(df_step1.index, df_step1.get('Handle_X', pd.Series(dtype=float)),
                color='#94a3b8', linewidth=0.8, label='Raw')
        ax.plot(df_step2.index, df_step2['Handle_X_Smooth'],
                color='#f59e0b', linewidth=1.5, label='Smoothed')
        ax.set_xlabel('Sample index'); ax.set_ylabel('Handle_X')
        ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

    st.markdown("**Smoothed column stats:**")
    smooth_cols = [f'{c}_Smooth' for c in PROCESSED_COLUMN_NAMES if f'{c}_Smooth' in df_step2.columns]
    st.dataframe(df_step2[smooth_cols].describe().T.round(2), width='stretch')

# ===========================================================================
# STEP 3 — Detect catches
# ===========================================================================
_step_header(3, "Detect Catches", "Interpolate small gaps and find local minima of Seat_X_Smooth.")

with st.expander("Step 3 details", expanded=True):
    df_step3, catch_indices = step3_detect_catches(df_step2, window=WINDOW)

    n_catches = len(catch_indices)
    if n_catches < 2:
        _fail(f"Only {n_catches} catch(es) detected — need at least 2 to form a cycle.")

    _ok(f"{n_catches} catches detected at indices: {catch_indices.tolist()}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 5), sharex=True)

    # Top: Seat_X_Smooth — what we actually detect minima on
    ax1.plot(df_step3.index, df_step3['Seat_X_Smooth'],
             color='#6366f1', linewidth=1.2, label='Seat_X_Smooth (detection signal)')
    for ci in catch_indices:
        ax1.axvline(ci, color='#22c55e', linewidth=1, linestyle='--', alpha=0.8)
    ax1.scatter(catch_indices, df_step3['Seat_X_Smooth'].iloc[catch_indices],
                color='#22c55e', s=60, zorder=5, label='Detected Catch (local min)')
    ax1.set_ylabel('Seat_X_Smooth')
    ax1.set_title('Seat_X_Smooth — local minima = catches (one per stroke)')
    ax1.legend(fontsize=8); ax1.spines[['top', 'right']].set_visible(False)

    # Bottom: Stroke_Compression — shown for context only
    ax2.plot(df_step3.index, df_step3['Stroke_Compression'],
             color='#f59e0b', linewidth=1.2, label='Stroke_Compression |Seat_X − Handle_X|')
    for ci in catch_indices:
        ax2.axvline(ci, color='#22c55e', linewidth=1, linestyle='--', alpha=0.8)
    ax2.set_xlabel('Sample index')
    ax2.set_ylabel('|Seat_X − Handle_X|')
    ax2.set_title('Stroke_Compression — shown for context (has 2 minima per stroke: catch + finish)')
    ax2.legend(fontsize=8); ax2.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
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

with st.expander("Step 4 details", expanded=True):
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
        fig, ax = plt.subplots(figsize=(5, 2.8))
        for i, c in enumerate(cycles):
            ax.plot(c['Seat_X_Smooth'].to_numpy()[:min_length],
                    color='#cbd5e1', linewidth=0.8, alpha=0.6)
        ax.plot(avg_cycle['Seat_X_Smooth'], color='#6366f1', linewidth=2, label='Average')
        ax.set_xlabel('Cycle index'); ax.set_ylabel('Seat_X_Smooth')
        ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig, width='stretch')
        plt.close(fig)

# ===========================================================================
# STEP 5 — Compute metrics
# ===========================================================================
_step_header(5, "Compute Metrics",
             "Calculate Trunk_Angle, velocities, and locate catch/finish (reversal-based) on the averaged cycle.")

with st.expander("Step 5 details", expanded=True):
    avg_cycle_m, catch_idx, finish_idx = step5_compute_metrics(avg_cycle, window=WINDOW)

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
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(avg_cycle_m.index, avg_cycle_m['Seat_X_Smooth'],
            color='#6366f1', linewidth=1.5, label='Seat_X_Smooth')
    ax.plot(avg_cycle_m.index, avg_cycle_m['Handle_X_Smooth'],
            color='#f59e0b', linewidth=1.2, linestyle='--', label='Handle_X_Smooth')

    ax.axvline(catch_idx, color='#22c55e', linestyle='--', linewidth=1.4, alpha=0.8, label='Catch idx')
    ax.scatter([catch_idx], [avg_cycle_m.loc[catch_idx, 'Seat_X_Smooth']],
               color='#22c55e', s=90, marker='o', zorder=5)

    ax.axvline(finish_idx, color='#d946ef', linestyle='--', linewidth=1.4, alpha=0.8, label='Finish idx')
    ax.scatter([finish_idx], [avg_cycle_m.loc[finish_idx, 'Seat_X_Smooth']],
               color='#d946ef', s=90, marker='X', zorder=5)

    ax.set_xlabel('Cycle sample index')
    ax.set_ylabel('X position (mm)')
    ax.set_title('Averaged stroke: catch & finish markers')
    ax.legend(fontsize=8)
    ax.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # Trunk angle plot
    st.markdown("**Trunk Angle across the averaged stroke:**")
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(avg_cycle_m.index, avg_cycle_m['Trunk_Angle'],
            color='#6366f1', linewidth=2, label='Trunk Angle')
    ax.axhline(0, color='#888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color='#22c55e', linestyle='--', linewidth=1.5, label=f'Catch ({catch_angle:.1f}°)')
    ax.axvline(finish_idx, color='#ef4444', linestyle='--', linewidth=1.5, label=f'Finish ({finish_angle:.1f}°)')
    ax.set_xlabel('Cycle index'); ax.set_ylabel('Degrees from vertical')
    ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    # Velocity plot
    st.markdown("**Seat vs. Handle velocity coordination:**")
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.plot(avg_cycle_m.index, avg_cycle_m['Handle_X_Vel'],
            color='#3b82f6', linewidth=1.5, label='Handle_X velocity')
    ax.plot(avg_cycle_m.index, avg_cycle_m['Seat_X_Vel'],
            color='#f59e0b', linewidth=1.5, label='Seat_X velocity')
    ax.axhline(0, color='#888', linestyle=':', linewidth=1, alpha=0.5)
    ax.axvline(catch_idx, color='#22c55e', linestyle='--', linewidth=1.2)
    ax.axvline(finish_idx, color='#ef4444', linestyle='--', linewidth=1.2)
    ax.set_xlabel('Cycle index'); ax.set_ylabel('Velocity (px/sample)')
    ax.legend(fontsize=8); ax.spines[['top', 'right']].set_visible(False)
    st.pyplot(fig, width='stretch')
    plt.close(fig)

    with st.expander("Raw averaged cycle DataFrame (all computed columns)"):
        st.dataframe(avg_cycle_m.round(3), width='stretch')

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
    bars = ax.barh(['Drive', 'Recovery'], [drive_pct, rec_pct],
                   color=['#6366f1', '#22c55e'], height=0.4)
    ax.bar_label(bars, fmt='%.1f%%', padding=4, fontsize=9)
    ax.set_xlim(0, 100); ax.set_xlabel('%')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    st.pyplot(fig, width='content')
    plt.close(fig)

# ===========================================================================
# METADATA & DIAGNOSTICS
# ===========================================================================
st.markdown("### 📊 Data Quality & Metadata Diagnostics")

with st.expander("Metadata details", expanded=True):
    # Note: In the debug page context, we're stepping through manually,
    # so we simulate the full pipeline context for metadata calculation
    if 'cycles' in locals() and cycles is not None:
        metadata = step7_diagnostics(df_raw, df_step2, cycles, avg_cycle_m, stats)
        
        # Display metadata metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Cycles Detected", metadata['capture_length'], help="Number of complete strokes")
        col_m2.metric("Sampling Stable?", "✅ Yes" if metadata['sampling_is_stable'] else "⚠️ No")
        if metadata['sampling_cv'] is not None:
            col_m3.metric("Sampling CV", f"{metadata['sampling_cv']:.2f}%", help="Coefficient of variation")
        
        # Row drops
        if metadata['rows_dropped'] > 0:
            st.info(f"📉 {metadata['rows_dropped']} rows dropped during processing")
        
        # Warnings
        if metadata['warnings']:
            for warning in metadata['warnings']:
                st.warning(f"⚠️ {warning}")
        else:
            st.success("✅ No data quality warnings detected")

    _ok("Pipeline completed successfully — all six steps produced valid output.")

st.divider()
st.caption(
    "💡 This page is intended for debugging only. To view the full coaching report, "
    "use the main **🚣 Rowing Analysis Report** page."
)
