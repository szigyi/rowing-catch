import streamlit as st

from rowing_catch.plot_transforms.kinetic_chain_transformer import KineticChainComponent
from rowing_catch.plot_transforms.performance_metrics_transformer import PerformanceMetricsComponent
from rowing_catch.plot_transforms.power_accumulation_transformer import PowerAccumulationComponent
from rowing_catch.plots.kinetic_chain_plot import render_kinetic_chain
from rowing_catch.plots.performance_metrics_plot import render_performance_metrics
from rowing_catch.plots.power_accumulation_plot import render_power_accumulation
from rowing_catch.ui.pre_process import render_sidebar_and_process

st.title('Performance Analysis')

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# --- Main Content ---
st.subheader('1. Power Accumulation (V³ Model)')
st.markdown('Shows how Legs, Trunk, and Arms contribute to the total power curve. Legs should drive the first 50% of the curve.')
power_accumulation_component = PowerAccumulationComponent()
computed_data = power_accumulation_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    ghost_cycle=scenario_avg,
    results={'scenario_name': selected_scenario},
)
render_power_accumulation(computed_data)

st.subheader('2. Kinetic Chain Coordination')
st.markdown("Coordination between seat velocity and handle acceleration. A lag here indicates 'shooting the slide'.")
kinetic_chain_component = KineticChainComponent()
computed_data = kinetic_chain_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={'scenario_name': selected_scenario},
)
render_kinetic_chain(computed_data)

st.subheader('3. Smoothness & Stability')
st.markdown('Jerk analysis (rate of change of acceleration) and vertical handle stability during the drive.')
performance_metrics_component = PerformanceMetricsComponent()
computed_data = performance_metrics_component.compute(
    avg_cycle=avg_cycle,
    catch_idx=catch_idx,
    finish_idx=finish_idx,
    results={'scenario_name': selected_scenario},
)
render_performance_metrics(computed_data)

st.markdown('---')
st.caption(f'Analysis complete for **{data_label}**. Metrics calculated using improved V³ Power Proxy.')
