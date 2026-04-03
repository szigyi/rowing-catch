import streamlit as st
from pages.components.shared_ui import render_sidebar_and_process
from pages.components.dev_performance import (
    plot_power_accumulation,
    plot_kinetic_chain,
    plot_performance_metrics
)

st.set_page_config(page_title="Performance Analysis", layout="wide", page_icon="⚡")

st.title("Performance Analysis")

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# --- Main Content ---
st.subheader("1. Power Accumulation (V³ Model)")
st.markdown("Shows how Legs, Trunk, and Arms contribute to the total power curve. Legs should drive the first 50% of the curve.")
plot_power_accumulation(avg_cycle, catch_idx, finish_idx, scenario_data=scenario_avg, scenario_name=selected_scenario)

st.subheader("2. Kinetic Chain Coordination")
st.markdown("Coordination between seat velocity and handle acceleration. A lag here indicates 'shooting the slide'.")
plot_kinetic_chain(avg_cycle, catch_idx, finish_idx, scenario_name=selected_scenario)

st.subheader("3. Smoothness & Stability")
st.markdown("Jerk analysis (rate of change of acceleration) and vertical handle stability during the drive.")
plot_performance_metrics(avg_cycle, catch_idx, finish_idx, scenario_name=selected_scenario)

st.markdown("---")
st.caption(f"Analysis complete for **{data_label}**. Metrics calculated using improved V³ Power Proxy.")
