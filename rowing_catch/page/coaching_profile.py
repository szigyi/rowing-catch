"""Coaching Profile page — coach-configurable thresholds and style settings.

The coach can set high-level philosophy values (e.g. when the upper body
should start opening during the drive) and the app automatically derives all
diagram-level thresholds from those values.  Live re-renders of the affected
diagrams are shown alongside the sliders so the coach can immediately see the
impact of their choices.
"""

import streamlit as st

from rowing_catch.coaching.profile import DEFAULT_COACHING_PROFILE, CoachingProfile
from rowing_catch.plot.theme import COLOR_CATCH, COLOR_FINISH
from rowing_catch.plot.trunk.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.plot.trunk.trunk_angle_separation_plot import render_trunk_angle_separation
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import TrunkAngleSeparationComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_transformer import TrunkAngleComponent
from rowing_catch.ui.annotation_toggles import render_annotation_toggles
from rowing_catch.ui.coaching_session import get_coaching_profile, save_coaching_profile
from rowing_catch.ui.pre_process import render_sidebar_and_process

st.title('Coaching Profile')
st.markdown(
    'Configure your **club style** here. Adjust the high-level coaching philosophy and the app '
    'will automatically derive all diagram thresholds and coaching tips. '
    'Changes take effect immediately across all pages in this session.'
)

# ---------------------------------------------------------------------------
# Sidebar: load data for live previews
# ---------------------------------------------------------------------------
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()
avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# ---------------------------------------------------------------------------
# Load current profile as the starting point for the form
# ---------------------------------------------------------------------------
current = get_coaching_profile()

st.markdown('---')

# ---------------------------------------------------------------------------
# Section 1: Trunk Timing (Philosophy)
# ---------------------------------------------------------------------------
st.subheader('1. Trunk Timing — Opening Philosophy')
st.markdown(
    'Set **when** the upper body should start to open during the drive. '
    'This single number drives the ideal window used in coaching tips for the '
    'trunk angle diagram.'
)

col_ctrl, col_preview = st.columns([1, 2], gap='large')

with col_ctrl:
    trunk_opening_pct = st.slider(
        'Upper body opens at… (% of drive)',
        min_value=15,
        max_value=65,
        value=int(current.trunk_opening_ideal_pct),
        step=1,
        help='The ideal fraction of the drive phase before the trunk begins to swing. Default: 33 % (legs-only first third).',
    )

    with st.expander('Expert: tolerance (±%)'):
        trunk_tolerance_pct = st.slider(
            '±Tolerance (percentage points)',
            min_value=5,
            max_value=25,
            value=int(current.trunk_open_tolerance_pct),
            step=1,
            help='The ±window around the ideal opening time that is still accepted as good.',
        )

    derived_low = max(0, trunk_opening_pct - trunk_tolerance_pct)
    derived_high = min(100, trunk_opening_pct + trunk_tolerance_pct)
    st.info(
        f'**Ideal opening window:** {derived_low}% – {derived_high}% of the drive\n\n'
        f'Below {derived_low}%: "trunk opens too early"\n\n'
        f'Above {derived_high}%: "trunk opens too late"'
    )

with col_preview:
    st.caption('Live preview — Trunk Angle & Range (coaching tips)')
    preview_profile_timing = CoachingProfile(
        trunk_opening_ideal_pct=float(trunk_opening_pct),
        trunk_open_tolerance_pct=float(trunk_tolerance_pct),
        catch_lean_low=current.catch_lean_low,
        catch_lean_high=current.catch_lean_high,
        finish_lean_low=current.finish_lean_low,
        finish_lean_high=current.finish_lean_high,
        recovery_reach_ideal_low=current.recovery_reach_ideal_low,
        recovery_reach_ideal_high=current.recovery_reach_ideal_high,
        separation_reach_ideal_low=current.separation_reach_ideal_low,
        separation_reach_ideal_high=current.separation_reach_ideal_high,
        separation_very_late_threshold=current.separation_very_late_threshold,
    )
    trunk_comp_timing = TrunkAngleComponent(profile=preview_profile_timing)
    trunk_computed_timing = trunk_comp_timing.compute(
        avg_cycle=avg_cycle,
        catch_idx=catch_idx,
        finish_idx=finish_idx,
        ghost_cycle=scenario_avg,
        results=results,
    )
    active_ann_timing = render_annotation_toggles(
        annotations=trunk_computed_timing.get('annotations', []),
        color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
        expander_label='Annotations — Trunk Angle (Timing Preview)',
        key_prefix='profile_timing_ann',
    )
    render_trunk_angle_with_stage_stickfigures(
        trunk_computed_timing,
        active_annotations=active_ann_timing,
    )

st.markdown('---')

# ---------------------------------------------------------------------------
# Section 2: Trunk Angles
# ---------------------------------------------------------------------------
st.subheader('2. Trunk Angle Zones')
st.markdown(
    'Set the **ideal lean ranges** at the catch and finish. '
    'These define the shaded zones on the Trunk Angle diagrams and drive the '
    '"Rock over more" / "Lay back more" coaching tips.'
)

col_ctrl2, col_preview2 = st.columns([1, 2], gap='large')

with col_ctrl2:
    catch_low, catch_high = st.slider(
        'Ideal catch lean zone (°)',
        min_value=-55,
        max_value=-5,
        value=(int(current.catch_lean_low), int(current.catch_lean_high)),
        step=1,
        help='Degrees from vertical (negative = forward lean). Default range: −33° to −27°.',
    )
    finish_low, finish_high = st.slider(
        'Ideal finish lean zone (°)',
        min_value=0,
        max_value=40,
        value=(int(current.finish_lean_low), int(current.finish_lean_high)),
        step=1,
        help='Degrees from vertical (positive = backward lay-back). Default range: 12° to 18°.',
    )
    st.caption(
        f'Catch zone midpoint: **{(catch_low + catch_high) / 2:.1f}°**  |  '
        f'Finish zone midpoint: **{(finish_low + finish_high) / 2:.1f}°**'
    )

with col_preview2:
    preview_profile_angles = CoachingProfile(
        trunk_opening_ideal_pct=float(trunk_opening_pct),
        trunk_open_tolerance_pct=float(trunk_tolerance_pct),
        catch_lean_low=float(catch_low),
        catch_lean_high=float(catch_high),
        finish_lean_low=float(finish_low),
        finish_lean_high=float(finish_high),
        recovery_reach_ideal_low=current.recovery_reach_ideal_low,
        recovery_reach_ideal_high=current.recovery_reach_ideal_high,
        separation_reach_ideal_low=current.separation_reach_ideal_low,
        separation_reach_ideal_high=current.separation_reach_ideal_high,
        separation_very_late_threshold=current.separation_very_late_threshold,
    )

    left_p, right_p = st.columns(2)

    with left_p:
        st.caption('Trunk Angle Separation (1a)')
        sep_comp = TrunkAngleSeparationComponent(profile=preview_profile_angles)
        computed_sep = sep_comp.compute(
            avg_cycle=avg_cycle,
            catch_idx=catch_idx,
            finish_idx=finish_idx,
            ghost_cycle=scenario_avg,
            results={'scenario_name': selected_scenario},
        )
        active_sep_ann = render_annotation_toggles(
            annotations=computed_sep.get('annotations', []),
            color_overrides={'[P1]': COLOR_CATCH, '[P2]': COLOR_FINISH, '[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
            expander_label='Annotations — Separation (Angles Preview)',
            key_prefix='profile_angles_sep_ann',
        )
        render_trunk_angle_separation(computed_sep, active_annotations=active_sep_ann)

    with right_p:
        st.caption('Trunk Angle & Range (1b)')
        trunk_comp_angles = TrunkAngleComponent(profile=preview_profile_angles)
        trunk_computed_angles = trunk_comp_angles.compute(
            avg_cycle=avg_cycle,
            catch_idx=catch_idx,
            finish_idx=finish_idx,
            ghost_cycle=scenario_avg,
            results=results,
        )
        active_ann_angles = render_annotation_toggles(
            annotations=trunk_computed_angles.get('annotations', []),
            color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
            expander_label='Annotations — Trunk Angle (Angles Preview)',
            key_prefix='profile_angles_trunk_ann',
        )
        render_trunk_angle_with_stage_stickfigures(
            trunk_computed_angles,
            active_annotations=active_ann_angles,
        )

st.markdown('---')

# ---------------------------------------------------------------------------
# Section 3: Recovery Timing
# ---------------------------------------------------------------------------
st.subheader('3. Recovery Rock-Over Timing')
st.markdown(
    'Set the **ideal window** during which the trunk should complete its forward '
    'swing and arrive at the catch angle. Expressed as % of the recovery phase.'
)

col_ctrl3, col_preview3 = st.columns([1, 2], gap='large')

with col_ctrl3:
    rec_low, rec_high = st.slider(
        'Ideal trunk arrival window (% of recovery)',
        min_value=10,
        max_value=95,
        value=(int(current.recovery_reach_ideal_low), int(current.recovery_reach_ideal_high)),
        step=5,
        help='Default: 40–80 %. Below 40 % → "rocks over too early"; above 80 % → "late rock-over".',
    )

    sep_low_raw, sep_high_raw = st.slider(
        'Separation ideal window (% of seat travel)',
        min_value=0,
        max_value=95,
        value=(int(current.separation_reach_ideal_low), int(current.separation_reach_ideal_high)),
        step=5,
        help='Default: 10–50 %. Controls the Trunk Angle Separation coaching tip.',
    )
    very_late_raw = st.slider(
        'Separation "very late" threshold (%)',
        min_value=50,
        max_value=100,
        value=int(current.separation_very_late_threshold),
        step=5,
        help='Above this fraction → "no separation / whiplash risk". Default: 90 %.',
    )

with col_preview3:
    st.caption('Live preview — Trunk Angle & Range (recovery S2 coaching tip)')
    preview_profile_rec = CoachingProfile(
        trunk_opening_ideal_pct=float(trunk_opening_pct),
        trunk_open_tolerance_pct=float(trunk_tolerance_pct),
        catch_lean_low=float(catch_low),
        catch_lean_high=float(catch_high),
        finish_lean_low=float(finish_low),
        finish_lean_high=float(finish_high),
        recovery_reach_ideal_low=float(rec_low),
        recovery_reach_ideal_high=float(rec_high),
        separation_reach_ideal_low=float(sep_low_raw),
        separation_reach_ideal_high=float(sep_high_raw),
        separation_very_late_threshold=float(very_late_raw),
    )
    trunk_comp_rec = TrunkAngleComponent(profile=preview_profile_rec)
    trunk_computed_rec = trunk_comp_rec.compute(
        avg_cycle=avg_cycle,
        catch_idx=catch_idx,
        finish_idx=finish_idx,
        ghost_cycle=scenario_avg,
        results=results,
    )
    active_ann_rec = render_annotation_toggles(
        annotations=trunk_computed_rec.get('annotations', []),
        color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
        expander_label='Annotations — Trunk Angle (Recovery Preview)',
        key_prefix='profile_rec_ann',
    )
    render_trunk_angle_with_stage_stickfigures(
        trunk_computed_rec,
        active_annotations=active_ann_rec,
    )

st.markdown('---')

# ---------------------------------------------------------------------------
# Save / Reset buttons
# ---------------------------------------------------------------------------
col_save, col_reset = st.columns([1, 1])

final_profile = CoachingProfile(
    trunk_opening_ideal_pct=float(trunk_opening_pct),
    trunk_open_tolerance_pct=float(trunk_tolerance_pct),
    catch_lean_low=float(catch_low),
    catch_lean_high=float(catch_high),
    finish_lean_low=float(finish_low),
    finish_lean_high=float(finish_high),
    recovery_reach_ideal_low=float(rec_low),
    recovery_reach_ideal_high=float(rec_high),
    separation_reach_ideal_low=float(sep_low_raw),
    separation_reach_ideal_high=float(sep_high_raw),
    separation_very_late_threshold=float(very_late_raw),
)

with col_save:
    if st.button('Apply & Save to Session', type='primary', use_container_width=True):
        save_coaching_profile(final_profile)
        st.success('Coaching profile saved for this session. Navigate to Development or Report to see the updated diagrams.')

with col_reset:
    if st.button('Reset to Defaults', use_container_width=True):
        save_coaching_profile(DEFAULT_COACHING_PROFILE)
        st.rerun()

st.markdown('---')
st.caption(f'Coaching profile active for session. Data: **{data_label}**.')
