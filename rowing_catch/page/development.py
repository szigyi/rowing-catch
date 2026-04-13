import streamlit as st

from rowing_catch.plot.handle_seat_distance_plot import render_handle_seat_distance
from rowing_catch.plot.handle_trajectory_dev_plot import render_handle_trajectory_dev
from rowing_catch.plot.recovery_slide_control_plot import render_recovery_slide_control
from rowing_catch.plot.rhythm.rhythm_consistency_plot import render_rhythm_consistency
from rowing_catch.plot.theme import COLOR_CATCH, COLOR_FINISH
from rowing_catch.plot.trunk.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.plot.trunk.trunk_angle_separation_plot import render_trunk_angle_separation
from rowing_catch.plot_transformer import TrunkAngleComponent
from rowing_catch.plot_transformer.handle_seat_distance_transformer import HandleSeatDistanceComponent
from rowing_catch.plot_transformer.handle_trajectory_dev_transformer import HandleTrajectoryDevComponent
from rowing_catch.plot_transformer.recovery_slide_control_transformer import RecoverySlideControlComponent
from rowing_catch.plot_transformer.rhythm.rhythm_consistency_transformer import RhythmConsistencyComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import TrunkAngleSeparationComponent
from rowing_catch.ui.annotation_toggles import render_annotation_toggles
from rowing_catch.ui.coaching_session import get_coaching_profile
from rowing_catch.ui.pre_process import render_sidebar_and_process

st.title('Development Analysis')

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()
profile = get_coaching_profile()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# --- 1a. Trunk Angle Separation ---
st.subheader('1a. Trunk Angle Separation')
st.markdown(
    'Shows how the body rocks over relative to seat position. '
    "Ideal technique requires the body to be 'set' before the knees rise."
)
trunk_angle_sep_component = TrunkAngleSeparationComponent(profile=profile)
computed_sep = trunk_angle_sep_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
active_sep_annotations = render_annotation_toggles(
    annotations=computed_sep.get('annotations', []),
    color_overrides={'[P1]': COLOR_CATCH, '[P2]': COLOR_FINISH, '[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
    expander_label='Annotations — Trunk Angle Separation',
    key_prefix='ann_sep',
)
render_trunk_angle_separation(computed_sep, active_annotations=active_sep_annotations)

# --- 1b. Trunk Angle & Range ---
trunk_component = TrunkAngleComponent(profile=profile)
trunk_computed = trunk_component.compute(
    avg_cycle=results['avg_cycle'],
    catch_idx=results['catch_idx'],
    finish_idx=results['finish_idx'],
    ghost_cycle=scenario_avg,
    results=results,
)

st.subheader('1b. Trunk Angle with Stick figures')
active_trunk_annotations = render_annotation_toggles(
    annotations=trunk_computed.get('annotations', []),
    color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
    expander_label='Annotations — Trunk Angle & Range',
    key_prefix='ann_trunk',
)
render_trunk_angle_with_stage_stickfigures(
    trunk_computed,
    active_annotations=active_trunk_annotations,
)

st.subheader('2. Rhythm Consistency')
st.markdown(
    'Comparison of SPM and Drive/Recovery ratio across all strokes. A tight cluster indicates professional-grade consistency.'
)
rhythm_consistency_component = RhythmConsistencyComponent()
computed_data = rhythm_consistency_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results=results,
)
render_rhythm_consistency(computed_data)

st.subheader('3. Handle-Seat Distance')
st.markdown('Measures compression. Ideally, you want a long reaching distance at the catch without losing core stability.')
handle_distance_component = HandleSeatDistanceComponent()
computed_data = handle_distance_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
render_handle_seat_distance(computed_data)


st.subheader('4. Recovery Slide Control')
st.markdown("Seat velocity during the recovery phase. Look for a controlled 'slow-down' before arriving at the catch.")
recovery_control_component = RecoverySlideControlComponent()
computed_data = recovery_control_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={'scenario_name': selected_scenario},
)
render_recovery_slide_control(computed_data)

st.markdown('---')
st.subheader('5. Handle Trajectory (Box Plot)')
st.markdown(
    'The vertical vs. horizontal path of the handle. A rectangular shape indicates consistent blade depth and clean extraction.'
)
trajectory_component = HandleTrajectoryDevComponent()
computed_data = trajectory_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
render_handle_trajectory_dev(computed_data)


st.markdown('---')
st.caption(f'Analysis complete for **{data_label}**.')
