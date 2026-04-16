import base64
from collections.abc import Sequence

import matplotlib.pyplot as plt
import streamlit as st

from rowing_catch.plot.handle_seat_distance_plot import render_handle_seat_distance
from rowing_catch.plot.handle_trajectory_dev_plot import render_handle_trajectory_dev
from rowing_catch.plot.recovery_slide_control_plot import render_recovery_slide_control
from rowing_catch.plot.rhythm.rhythm_consistency_plot import render_rhythm_consistency
from rowing_catch.plot.theme import COLOR_CATCH, COLOR_FINISH, COLOR_IDEAL_RATIO, COLOR_RHYTHM_SPREAD
from rowing_catch.plot.trunk.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.plot.trunk.trunk_angle_separation_plot import render_trunk_angle_separation
from rowing_catch.plot.velocity.velocity_profile_plot import render_velocity_profile
from rowing_catch.plot_transformer import TrunkAngleComponent
from rowing_catch.plot_transformer.annotations import AnnotationEntry
from rowing_catch.plot_transformer.handle_seat.handle_seat_distance_transformer import HandleSeatDistanceComponent
from rowing_catch.plot_transformer.handle_trajectory_dev_transformer import HandleTrajectoryDevComponent
from rowing_catch.plot_transformer.recovery_slide_control_transformer import RecoverySlideControlComponent
from rowing_catch.plot_transformer.rhythm.rhythm_consistency_transformer import RhythmConsistencyComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import TrunkAngleSeparationComponent
from rowing_catch.plot_transformer.velocity.velocity_profile_transformer import VelocityProfileComponent
from rowing_catch.ui.annotation_toggles import render_annotation_toggles
from rowing_catch.ui.coaching_session import get_coaching_profile
from rowing_catch.ui.pre_process import render_sidebar_and_process
from rowing_catch.utils.pdf_export import generate_development_report

st.title('Development Analysis')

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()
profile = get_coaching_profile()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

st.subheader('1. Detailed Velocity Profile (Seat, Handle, Shoulder, Rower)')
st.markdown('Rate of change (velocity) of all tracked segments across the averaged stroke.')
velocity_profile_component = VelocityProfileComponent()
computed_vel = velocity_profile_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results=results,
)
fig0 = render_velocity_profile(computed_vel, return_fig=True)
if fig0:
    st.pyplot(fig0)
    st.info(f"**Coach's Tip:** {computed_vel['coach_tip']}")

st.subheader('2. Trunk Angle Separation')
st.markdown('Shows the trunk angle relative to seat position.')
trunk_angle_sep_component = TrunkAngleSeparationComponent(profile=profile)
computed_sep = trunk_angle_sep_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={**results, 'scenario_name': selected_scenario},
)
_sep_color_overrides = {'[P1]': COLOR_CATCH, '[P2]': COLOR_FINISH, '[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH}
active_sep_annotations = render_annotation_toggles(
    annotations=computed_sep.get('annotations', []),
    color_overrides=_sep_color_overrides,
    expander_label='Annotations — Trunk Angle Separation',
    key_prefix='ann_sep',
)
fig1 = render_trunk_angle_separation(
    computed_sep,
    active_annotations=active_sep_annotations,
    color_overrides=_sep_color_overrides,
    return_fig=True,
)
if fig1:
    st.pyplot(fig1)
    st.info(f'**Developing Advice:** {computed_sep["coach_tip"]}')

st.subheader('3. Trunk Angle with Stick figures')
st.markdown('Shows the trunk angle compare to the progress of the stroke.')
trunk_component = TrunkAngleComponent(profile=profile)
trunk_computed = trunk_component.compute(
    avg_cycle=results['avg_cycle'],
    catch_idx=results['catch_idx'],
    finish_idx=results['finish_idx'],
    ghost_cycle=scenario_avg,
    results=results,
)
_trunk_color_overrides = {'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH}
active_trunk_annotations = render_annotation_toggles(
    annotations=trunk_computed.get('annotations', []),
    color_overrides=_trunk_color_overrides,
    expander_label='Annotations — Trunk Angle & Range',
    key_prefix='ann_trunk',
)
fig2 = render_trunk_angle_with_stage_stickfigures(
    trunk_computed,
    active_annotations=active_trunk_annotations,
    color_overrides=_trunk_color_overrides,
    return_fig=True,
)
if fig2:
    st.pyplot(fig2)
    st.info(f"**Coach's Tip:** {trunk_computed['coach_tip']}")

st.subheader('4. Rhythm Consistency')
st.markdown('Measures how consistently the rower reaches the target rhythm. Consistency is key for high-level performance.')
rhythm_component = RhythmConsistencyComponent(profile=profile)
computed_data_2 = rhythm_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={'cycles': results['cycles']},
)
_rhythm_color_overrides = {'[S1]': COLOR_IDEAL_RATIO, '[Z1]': COLOR_RHYTHM_SPREAD, '[Z2]': COLOR_RHYTHM_SPREAD}
active_rhythm_annotations = render_annotation_toggles(
    annotations=computed_data_2.get('annotations', []),
    color_overrides=_rhythm_color_overrides,
    expander_label='Annotations — Rhythm Consistency',
    key_prefix='ann_rhythm',
)
fig3 = render_rhythm_consistency(
    computed_data_2,
    active_annotations=active_rhythm_annotations,
    color_overrides=_rhythm_color_overrides,
    return_fig=True,
)
if fig3:
    st.pyplot(fig3, width='stretch')
    st.info(f'**Performance Insight:** {computed_data_2["coach_tip"]}')

st.subheader('5. Handle-Seat Distance')
st.markdown('Measures compression. Ideally, you want a long reaching distance at the catch without losing core stability.')
handle_seat_distance_component = HandleSeatDistanceComponent(profile=profile)
computed_data_3 = handle_seat_distance_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={**results, 'scenario_name': selected_scenario},
)
active_hsd_annotations = render_annotation_toggles(
    annotations=computed_data_3.get('annotations', []),
    expander_label='Annotations — Handle-Seat Distance',
    key_prefix='ann_hsd',
)
fig4 = render_handle_seat_distance(
    computed_data_3,
    active_annotations=active_hsd_annotations,
    return_fig=True,
)
if fig4:
    st.pyplot(fig4)
    st.info(f'**Developing Advice:** {computed_data_3["coach_tip"]}')


st.subheader('6. Recovery Slide Control')
st.markdown('Analyzes seat velocity during recovery. Gradual deceleration into the catch indicates good slide control.')
recovery_slide_control_component = RecoverySlideControlComponent()
computed_data_4 = recovery_slide_control_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={**results, 'scenario_name': selected_scenario},
)
fig5 = render_recovery_slide_control(computed_data_4, return_fig=True)
if fig5:
    st.pyplot(fig5)
    st.info(f'**Performance Insight:** {computed_data_4["coach_tip"]}')

st.markdown('---')
st.subheader('7. Handle Trajectory (Box Plot)')
st.markdown('Shows the variance of handle height across the stroke.')
handle_trajectory_dev_component = HandleTrajectoryDevComponent()
computed_data_5 = handle_trajectory_dev_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={**results, 'scenario_name': selected_scenario},
)
fig6 = render_handle_trajectory_dev(computed_data_5, return_fig=True)
if fig6:
    st.pyplot(fig6)
    st.info(f"**Coach's Tip:** {computed_data_5['coach_tip']}")


st.markdown('---')
if st.button('Generate PDF Report', type='primary'):
    with st.spinner('Generating report...'):
        # Filter out multi-figure lists or None. renderer_performance_metrics returns a list.
        # But we only use single figures here.
        # Filter active annotations to pass full objects to PDF generator
        def _get_active_anns(all_anns: list[AnnotationEntry], active_labels: set[str] | None) -> list[AnnotationEntry]:
            if active_labels is None:
                return all_anns
            return [a for a in all_anns if a.label in active_labels]

        figures: list[tuple[str, plt.Figure | None, Sequence[AnnotationEntry]]] = [
            ('Detailed Velocity Profile', fig0, []),
            ('Trunk Angle Separation', fig1, _get_active_anns(computed_sep.get('annotations', []), active_sep_annotations)),
            ('Trunk Angle & Range', fig2, _get_active_anns(trunk_computed.get('annotations', []), active_trunk_annotations)),
            ('Rhythm Consistency', fig3, _get_active_anns(computed_data_2.get('annotations', []), active_rhythm_annotations)),
            ('Handle-Seat Distance', fig4, _get_active_anns(computed_data_3.get('annotations', []), active_hsd_annotations)),
            ('Recovery Slide Control', fig5, []),
            ('Handle Trajectory', fig6, []),
        ]

        valid_figures: list[tuple[str, plt.Figure, Sequence[AnnotationEntry]]] = []
        for name, f, anns in figures:
            if f is not None:
                valid_figures.append((name, f, anns))

        pdf_bytes = generate_development_report(
            valid_figures,
            data_label=data_label,
        )

        b64 = base64.b64encode(pdf_bytes).decode()
        href = (
            f'<a href="data:application/pdf;base64,{b64}" '
            f'download="Rowing_Development_Report_{data_label}.pdf" '
            f'style="text-decoration:none;">'
            f'<div style="background-color:#FF4B4B;color:white;padding:10px 20px;'
            f'border-radius:5px;text-align:center;font-weight:bold;margin-top:10px;">'
            f'Download PDF Report'
            f'</div></a>'
        )
        st.markdown(href, unsafe_allow_html=True)

st.markdown('---')
st.caption(f'Analysis complete for **{data_label}**.')

# Cleanup Matplotlib figures to prevent memory leaks and MediaFileStorageError
for f in [fig0, fig1, fig2, fig3, fig4, fig5, fig6]:
    if f is not None:
        plt.close(f)
