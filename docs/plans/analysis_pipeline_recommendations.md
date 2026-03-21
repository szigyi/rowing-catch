# Rowing Catch Analysis Pipeline Audit & Recommendations

## Current Pipeline Summary

The analysis pipeline in `analysis.py` follows a **6-step pipelined architecture**:

1. **step1_rename_columns** - Map input CSV columns to internal format
2. **step2_smooth** - Apply rolling mean smoothing
3. **step3_detect_catches** - Identify stroke catch events using seat reversal logic
4. **step4_segment_and_average** - Partition into cycles and compute averages
5. **step5_compute_metrics** - Calculate trunk angles, velocities, stroke markers
6. **step6_statistics** - Compute CV, drive/recovery ratios, cycle duration

The public wrapper **`process_rowing_data(...)`** chains all steps and returns:
- `avg_cycle` - Average cycle trajectory
- `cycles` - Individual cycle segments
- `catch_idx`, `finish_idx` - Event indices
- `min_length`, `cv_length`, `drive_len`, `recovery_len`, `mean_duration` - Metrics

**Key techniques used:**
- Rolling mean smoothing for noise reduction
- Local maxima/minima logic (seat reversal detection)
- Chest/seat orientation-based trunk angle computation
- `np.gradient` for velocity estimation
- Multi-signal cache/finish selection heuristics

---

## What is Already Working Well

✅ **Modular steps** - easy to test and replace individually  
✅ **Transparent debug page** - per-step visuals with expandable debug sections  
✅ **Meaningful metrics** - trunk angle, velocities, drive/recovery durations resonate with coaches  
✅ **Reusable KPI helper** - `get_traffic_light()` function simplifies status UI  
✅ **Example scenario pipeline** - reproducible analysis without real data dependencies  
✅ **Database agnostic** - works with any CSV matching column schema  

---

## Risks & Robustness Gaps in Data Processing

### 1. No Strict Input Validation
- ✅ Done

**Problem:**
- `step1_rename_columns` silently keeps unmapped columns
- Missing required columns (e.g., `Handle/0/X`) cause hard failures downstream
- No early detection of malformed input

**Recommendation:**
- Add `validate_input_df(df)` validation block at pipeline entry
- Enforce explicit required column list and clear error messages

### 2. Timestamp/Sampling Assumptions
- ✅ Done

**Problem:**
- `np.gradient(pos)` on sample indices assumes uniform sampling
- Real-world data can have jitter or dropped frames
- Velocity calculations lack time awareness

**Recommendation:**
- Use `Time` column when available: `velocity = diff(pos) / diff(Time)`
- Fall back to sample-based metrics for datasets without timestamps
- Validate `Time` column is monotonic and non-NaN

### 3. Smoothing & Cycle Boundary Effects
- ✅ Done

**Problem:**
- `step2_smooth` center window + drop NaN edges removes data
- Deletes beginning/ending rows; problematic for small datasets
- Can shift cycle alignment

**Recommendation:**
- Use `min_periods=1` or border padding (symmetric, pad)
- Preserve row count to avoid losing endpoints

### 4. Catch/Finish Detection Edge Cases
- ✅ Done

**Problem:**
- `_detect_catches_by_seat_reversal` and `_is_valid_finish` use deterministic thresholding
- No signal quality checks
- May fail on poor/noisy data

**Recommendation:**
- Add signal quality threshold (reject if noise too high)
- Implement alternate detection on `Handle_X` or fused feature scores
- Use `Seat_Y` or dynamic angle as secondary guard for poor data

### 5. Proportional Metrics Missing Drift Normalization
- ✅ Done

**Problem:**
- Stroke lengths from seat X range vary with tracker drift
- No real timestamp integration
- No explicit denoising or artifact detection

**Recommendation:**
- Add:
  - `stroke_rate = 60 / avg_cycle_duration_seconds` (SPM)
  - Drive/recovery volume in `mm * sec`
  - Rowwise z-score or IQR trimming for outlier detection
  - Interpolation for small missing gaps

### 6. No Metadata Tracking
- ✅ Done

**Problem:**
- No diagnostics for sampling stability, row drops, NaN patterns
- Difficult to assess data trustworthiness
- No warnings surfaced to user

**Recommendation:**
- Output warnings: `"sampling frequency unstable"`, `"capture length < 3 strokes"`
- Add `results['data_quality']` dict with flags:
  - `rows_dropped`, `nan_rate`, `expected_rate_variation`, `outlier_count`

---

## Data Analyst Product-Grade Improvements

### 1. Stronger Data Validation & Schema Contract

**Enforce:**
- Required columns: `Time`, `Handle/0/X`, `Shoulder/0/X`, `Seat/0/X`, and Y variants
- Numeric conversion with clear error handling
- No stroke < 1 second or entire NaN rows
- Monotonic timestamps

**Output:**
- DataFrame progression: raw → cleaned → filtered → analyzed
- Clear error messages at each stage

### 2. Add Temporal Metrics & Unit Standardization

**Add to output:**
- `sample_rate_hz` - sampling frequency
- `cycle_duration_s` - real time per stroke (seconds)
- `drive_duration_s`, `recovery_duration_s` - phase times
- `stroke_rate_spm` - strokes per minute
- Distances per phase (mm or meters)

**Standardize units:**
- Document all outputs with SI units or clear choice (e.g., mm for position, degrees for angles, mm/s for velocity)

### 3. Dedicated Data Quality Report

**Add to `process_rowing_data` output:**
- Rows dropped in smoothing
- NaN rate by column
- Sample rate stability (coefficient of variation)
- Outlier count per metric
- Estimated data quality flags: OK / warning / fail

### 4. Configurable Parameterization

**Currently hard-coded:**
- `window = 10`, `min_separation = 20`, `prominence`, `cv_threshold`

**Expose via:**
- Streamlit sliders in UI
- Function parameters with defaults
- Enable A/B testing and batch runs

### 5. Batch & Parallel Mode

**For "data analyst product":**
- Support processing multiple files
- Aggregate dashboard with:
  - Heatmap of CV across sessions
  - Baseline + trend features
  - Export to Parquet/HDF for BI tools

---

## Debug Page UX Improvements (for Analysts)

Current debug page is useful but needs enhancements for "serious product" status.

### Data Summary Panel (Top)

**Display:**
- Raw dataset metadata: source, row count, estimated sample rate, missing value rate
- Pipeline status and warnings
- Data quality flags

### Time-Level Interactive Charts

**Use plotly or altair:**
- Zoom + hover over raw vs. smoothed traces
- Individual cycle overlays with confidence bands
- Actionable event markers (catch, finish)

### Quality Controls in UI

**Add sliders:**
- Smoothing window, min_separation, prominence, pre-catch window
- Auto-compare with scenario baseline (reproducible ghost line)

### Multi-Cycle Consistency Diagnostics

**Display:**
- Aligned median + 90% quantile band
- Superimposed catch/finish windows across cycles
- Diagonal / time lag heatmaps of cycle alignment

### Text Insights & Coaching Hints

**Generate signals:**
- "Cycle 2 was 25% slower (160ms) than average → possible technical drift"
- "Handle velocity leads Seat by X samples: possible early hand opening"

### Export Report

**Enable:**
- CSV export of metrics table
- PDF export for coaching insights

---

## Code Suggestions in Place

### Add Logging

```python
import logging
logger = logging.getLogger(__name__)
logger.warning(f"Failed to detect finish: {error_msg}")
```

### Add Tests Around

- Badly shaped input (wrong column count, types)
- Missing required columns
- Non-uniform timestamps, spike data
- Consistent results for known scenarios

### Add Docstrings

- Document every output metric with units
- Include calculation method and assumptions

---

## Recommendation: Final "Seriousness" Checklist

- ✅ Deterministic pipeline
- ✅ Reproducible fixtures (scenario folder)
- ✅ Code modular + testable
- ⏳ Input validation / config defined **(needed)**
- ⏳ Data quality summary **(missing)**
- ⏳ Metric definitions in docs **(partial)**
- ⏳ Streamlit debug UX makes assumptions visible **(can improve)**
- ⏳ Pathology handling + logged warnings **(not yet)**
- ⏳ Batch/long-term trend report **(missing)**

---

## Next Concrete Actions (Proposed)

### In `analysis.py`

1. Add `validate_input_df(df)` at pipeline start
2. Implement timing-aware velocity using `Time` column
3. Add outlier filter for "noisy points"
4. Return `data_quality` dict with all diagnostic fields

### In `app.py` / `0_Debug_Pipeline.py`

1. Add interactive sliders for pipeline parameters
2. Auto-calculate sample rate display
3. Add data quality panel with flags/warnings
4. Enable parameter export/save workflows

### Add Comprehensive Tests

- Synthetic edge cases: missing data, low stroke count, non-monotonic time
- Malformed CSV: wrong types, missing columns
- Known scenario regression tests

### Add Documentation

- README section: "Data Product Guidance for Analysts"
  - Required CSV format specification
  - Performance metrics and bias sources
  - Drift handling and limitations
  - Example workflow and interpretation

---

## Quick Data Product Value-Add

With these improvements, the solution evolves from a rowing coach demo into a **serious analytics application**:

- ✅ Robust quality control with early failure detection
- ✅ Full audit trail with data quality tracking
- ✅ Reproducible model with configurable parameters
- ✅ Analyst-focused dashboards with interactive exploration
- ✅ Export capabilities for downstream BI and reporting
- ✅ Clear documentation of assumptions and limitations

**Result:** Polished, production-ready tool suitable for real coaching decisions and analysis teams.
