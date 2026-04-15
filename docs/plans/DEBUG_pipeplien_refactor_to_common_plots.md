Refactor Plan for 0_Debug_Pipeline.py
1. Audit the current page
Identify all debug diagrams and preserve their exact data/computation flow.

Diagrams in 0_Debug_Pipeline.py:

Step 2
Seat_X raw vs Seat_X_Smooth
Handle_X raw vs Handle_X_Smooth
Step 3
Seat_X_Smooth + detected catch lines + catch scatter
Catch-to-catch interval table
Step 4
Cycle length table
Averaged Seat_X overlay with mean + ±1 SD band
Step 5
Averaged cycle multi-axis plot: Seat_X_Smooth, Handle_X_Smooth, optional Shoulder_X_Smooth with catch/finish markers
Full trajectory event plot with production heuristic finish indices
Averaged cycle trunk angle
Detailed velocity plot
Relative velocity vs seat
Jerk comparison subplots
Power curve / V³ drag model breakdown
Raw averaged cycle DataFrame
Step 6
Drive vs recovery stacked bar
Ratio & rhythm spread scatter plot
Step 7
Diagnostics metrics / warnings (not a plot transform)
2. New plot_transforms/ components to create
Create one transform per unique debug plot, preserving the same input data and labels.

Proposed new components:

signal_smoothing_comparison.py
catch_detection.py
cycle_overlay_mean_std.py
avg_cycle_multi_axis_events.py
production_finish_trajectory.py
avg_cycle_trunk_angle.py
velocity_profile.py
relative_velocity.py
jerk_comparison.py
debug_power_curve.py
drive_recovery_ratio_balance.py
rhythm_consistency.py — reuse existing plot if possible
3. New plots/ renderer files to create
Create matching renderer files that draw the exact same figures.

Proposed new renderers:

signal_smoothing_comparison.py
catch_detection.py
cycle_overlay_mean_std.py
avg_cycle_multi_axis_events.py
production_finish_trajectory.py
avg_cycle_trunk_angle.py
velocity_profile.py
relative_velocity.py
jerk_comparison.py
debug_power_curve.py
drive_recovery_ratio_balance.py
rhythm_consistency.py — likely reuse existing renderer
4. Page refactor strategy
Refactor 0_Debug_Pipeline.py into orchestration only:

Keep all sidebar input selection and validation logic unchanged.
Keep helper UI functions _phase_header, _step_header, _ok, _fail unchanged.
Keep all pipeline functions (step1_rename_columns, step2_smooth, step3_detect_catches, step4_segment_and_average, step5_compute_metrics, step6_statistics, step7_diagnostics) unchanged.
Move only plotting code into compute() + render_*() layers.
Keep tables and metric widgets inside the page.
Example pattern per diagram:

computed = component.compute(avg_cycle, catch_idx, finish_idx, ghost_cycle, results)
render_computed(computed)
Use results to pass debug-only context when needed:

catch_indices
cycle_details
production_finish_indices
df_debug
avg_cycle_m
derived cycle_data
5. Similar/existing plot overlap
Mark the plots that already exist or are highly similar:

rhythm_consistency.py
Existing rhythm_consistency.py already covers the SPM vs drive/recovery ratio scatter.
Plan: reuse the existing component/renderer rather than duplicate.
avg_cycle_trunk_angle.py
Similar to existing trunk_angle.py, but debug version is simpler/annotation-focused.
Plan: create a dedicated debug plot renderer, mark overlap in implementation notes.
debug_power_curve.py
Similar domain to existing power_accumulation.py, but the debug page uses a full-drive breakdown and total curve rather than cumulative segmental power only.
Plan: keep as separate debug component.
6. Registry and exports
Update the architecture registry files:

registry.py
__init__.py
__init__.py
Add each new component/renderer so the architecture remains consistent.

7. Validation plan
After refactor, run:

python -m mypy rowing_catch/ pages/ --ignore-missing-imports
python -m pytest tests/
Manual load of 0_Debug_Pipeline.py in Streamlit
Confirm:

no behavior or data computation changes
plots render identically
debug page still shows the same intermediate diagnostics
8. Implementation order
Create new plot transform + renderer files
Update registries and exports
Refactor 0_Debug_Pipeline.py to use the new components
Validate with mypy/tests
Compare overlap plots and keep existing shared plot paths when appropriate
If you want, I can now execute the first implementation step and scaffold the new transform/plot files for Step 2 and Step 3 first.

Do not reuse the 'rhythm_consistency.py'. It should be overwritten by the version from debug pipeline page. The debug page version is much better, it should be used everwhere else. Proceed.