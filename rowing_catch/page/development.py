import base64

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
from rowing_catch.utils.pdf_export import generate_development_report

st.title('Development Analysis')

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()
profile = get_coaching_profile()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

st.subheader('1. Trunk Angle Separation')
st.markdown('Shows the trunk angle relative to seat position.')
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
fig1 = render_trunk_angle_separation(computed_sep, active_annotations=active_sep_annotations, return_fig=True)

st.subheader('2. Trunk Angle with Stick figures')
st.markdown('Shows the trunk angle compare to the progress of the stroke.')
trunk_component = TrunkAngleComponent(profile=profile)
trunk_computed = trunk_component.compute(
    avg_cycle=results['avg_cycle'],
    catch_idx=results['catch_idx'],
    finish_idx=results['finish_idx'],
    ghost_cycle=scenario_avg,
    results=results,
)
active_trunk_annotations = render_annotation_toggles(
    annotations=trunk_computed.get('annotations', []),
    color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
    expander_label='Annotations — Trunk Angle & Range',
    key_prefix='ann_trunk',
)
fig2 = render_trunk_angle_with_stage_stickfigures(
    trunk_computed,
    active_annotations=active_trunk_annotations,
    return_fig=True,
)

st.subheader('3. Rhythm Consistency')
st.markdown(
    'Comparison of SPM and Drive/Recovery ratio across all strokes. A tight cluster indicates professional-grade consistency.'
)
rhythm_consistency_component = RhythmConsistencyComponent(profile=profile)
computed_data_2 = rhythm_consistency_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results=results,
)
active_rhythm_annotations = render_annotation_toggles(
    annotations=computed_data_2.get('annotations', []),
    expander_label='Annotations — Rhythm Consistency',
    key_prefix='ann_rhythm',
)
fig3 = render_rhythm_consistency(computed_data_2, active_annotations=active_rhythm_annotations, return_fig=True)
fig3_display = render_rhythm_consistency(computed_data_2, active_annotations=active_rhythm_annotations, return_fig=False)

st.subheader('4. Handle-Seat Distance')
st.markdown('Measures compression. Ideally, you want a long reaching distance at the catch without losing core stability.')
handle_distance_component = HandleSeatDistanceComponent()
computed_data_3 = handle_distance_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
fig4 = render_handle_seat_distance(computed_data_3, return_fig=True)


st.subheader('5. Recovery Slide Control')
st.markdown("Seat velocity during the recovery phase. Look for a controlled 'slow-down' before arriving at the catch.")
recovery_control_component = RecoverySlideControlComponent()
computed_data_4 = recovery_control_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={'scenario_name': selected_scenario},
)
fig5 = render_recovery_slide_control(computed_data_4, return_fig=True)

st.markdown('---')
st.subheader('6. Handle Trajectory (Box Plot)')
st.markdown(
    'The vertical vs. horizontal path of the handle. A rectangular shape indicates consistent blade depth and clean extraction.'
)
trajectory_component = HandleTrajectoryDevComponent()
computed_data_5 = trajectory_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
fig6 = render_handle_trajectory_dev(computed_data_5, return_fig=True)


st.markdown('---')
st.subheader('7. Export Report')
st.markdown('Generate a comprehensive PDF documentation of the development phase features above.')

if st.button('Generate PDF Report', type='primary'):
    try:
        import matplotlib.figure

        from rowing_catch.plot_transformer.annotations import AnnotationEntry

        def get_active_anns(all_anns: list[AnnotationEntry], active_set: set[str] | None) -> list[AnnotationEntry]:
            if not all_anns:
                return []
            if active_set is None:
                return all_anns
            return [a for a in all_anns if a.label in active_set]

        figures = [
            ('Trunk Angle Separation', fig1, get_active_anns(computed_sep.get('annotations', []), active_sep_annotations)),
            ('Trunk Angle & Range', fig2, get_active_anns(trunk_computed.get('annotations', []), active_trunk_annotations)),
            ('Rhythm Consistency', fig3, get_active_anns(computed_data_2.get('annotations', []), active_rhythm_annotations)),
            ('Handle-Seat Distance', fig4, []),
            ('Recovery Slide Control', fig5, []),
            ('Handle Trajectory (Box Plot)', fig6, []),
        ]

        # Remove any Nones in case some data was missing
        from collections.abc import Sequence

        valid_figures: list[tuple[str, matplotlib.figure.Figure, Sequence[AnnotationEntry]]] = [
            (t, f, a) for t, f, a in figures if f is not None
        ]

        with st.spinner('Generating report...'):
            pdf_bytes = generate_development_report(valid_figures, data_label)

            # Use base64 encoded data URI via javascript to open in a new window/tab
            b64 = base64.b64encode(pdf_bytes).decode()
            style = (
                'display: inline-block; padding: 0.5rem 1rem; '
                'background-color: #2e66ff; color: white; '
                'text-decoration: none; border-radius: 4px; '
                'font-weight: 500; font-family: sans-serif;'
            )
            pdf_display = f'''
                <a href="data:application/pdf;base64,{b64}" download="{data_label}_Development_Report.pdf" target="_blank"
                   style="{style}">
                    Click to Open/Download Report
                </a>
            '''
            st.markdown(pdf_display, unsafe_allow_html=True)
            st.success('Report successfully generated!')

    except Exception as e:
        st.error(f'Failed to generate report: {e}')

st.markdown('---')
st.caption(f'Analysis complete for **{data_label}**.')
