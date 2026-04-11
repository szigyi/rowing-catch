import streamlit as st

import dataclasses

from rowing_catch.plot.handle_seat_distance_plot import render_handle_seat_distance
from rowing_catch.plot.handle_trajectory_dev_plot import render_handle_trajectory_dev
from rowing_catch.plot.recovery_slide_control_plot import render_recovery_slide_control
from rowing_catch.plot.rhythm.rhythm_consistency_plot import render_rhythm_consistency
from rowing_catch.plot.theme import COLOR_CATCH, COLOR_FINISH
from rowing_catch.plot.trunk.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.plot.trunk.trunk_angle_separation_plot import render_trunk_angle_separation
from rowing_catch.plot_transformer import TrunkAngleComponent
from rowing_catch.plot_transformer.annotations import assign_annotation_colors
from rowing_catch.plot_transformer.handle_seat_distance_transformer import HandleSeatDistanceComponent
from rowing_catch.plot_transformer.handle_trajectory_dev_transformer import HandleTrajectoryDevComponent
from rowing_catch.plot_transformer.recovery_slide_control_transformer import RecoverySlideControlComponent
from rowing_catch.plot_transformer.rhythm.rhythm_consistency_transformer import RhythmConsistencyComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import TrunkAngleSeparationComponent
from rowing_catch.ui.pre_process import render_sidebar_and_process

st.title('Development Analysis')

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# --- Main Content ---
st.subheader('1a. Trunk Angle Separation')
st.markdown(
    'Shows how the body rocks over relative to seat position. '
    "Ideal technique requires the body to be 'set' before the knees rise."
)
trunk_angle_sep_component = TrunkAngleSeparationComponent()
computed_data = trunk_angle_sep_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
render_trunk_angle_separation(computed_data)

# --- Trunk Angle & Range ---
trunk_component = TrunkAngleComponent()
trunk_computed = trunk_component.compute(
    avg_cycle=results['avg_cycle'],
    catch_idx=results['catch_idx'],
    finish_idx=results['finish_idx'],
    ghost_cycle=scenario_avg,
    results=results,
)


st.subheader('1b. Trunk Angle with Stick figures')
# Annotation toggles — one checkbox per annotation, collapsible
# Toggles must be rendered BEFORE the plot so the selected state is passed in.
trunk_annotations = trunk_computed.get('annotations', [])
active_trunk_annotations: set[str] | None = None

if trunk_annotations:
    # Resolve the same colors the renderer uses: auto-palette + zone overrides.
    _zone_overrides = {'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH}
    _colored_anns = assign_annotation_colors(trunk_annotations)
    _colored_anns = [
        dataclasses.replace(a, color=_zone_overrides[a.label])
        if a.label in _zone_overrides else a
        for a in _colored_anns
    ]

    with st.expander('Trunk Angle Annotations - Toggle individual annotations on or off', expanded=False):
        show_all = st.checkbox(
            'Show all annotations',
            value=True,
            key='ann_trunk_show_all',
        )
        st.markdown('<hr style="margin:4px 0 8px 0; border-color:#E8E8E8">', unsafe_allow_html=True)

        active_trunk_annotations = set()
        for ann in _colored_anns:
            color = ann.color or '#888888'
            col_dot, col_cb = st.columns([0.04, 0.96])
            with col_dot:
                st.markdown(
                    f'<div style="width:12px;height:12px;border-radius:50%;'
                    f'background:{color};margin-top:6px"></div>',
                    unsafe_allow_html=True,
                )
            with col_cb:
                checked = st.checkbox(
                    f'{ann.label} — {ann.description}',
                    value=show_all,
                    key=f'ann_trunk_{ann.label}',
                    disabled=not show_all,
                )
            if checked and show_all:
                active_trunk_annotations.add(ann.label)

        if not show_all:
            active_trunk_annotations = set()  # hide all

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
