import streamlit as st
from pages.components.shared_ui import render_sidebar_and_process
from pages.components.dev_performance import (
    plot_trunk_angle_separation,
    plot_handle_seat_distance,
    plot_ratio_consistency,
    plot_recovery_control,
    plot_handle_trajectory
)

st.set_page_config(page_title="Development Analysis", layout="wide")

st.title("Development Analysis")

# Render shared sidebar and process data
results, scenario_avg, selected_scenario, data_label = render_sidebar_and_process()

avg_cycle = results['avg_cycle']
catch_idx = results['catch_idx']
finish_idx = results['finish_idx']

# --- Main Content ---
st.subheader("1. Trunk Angle Separation")
st.markdown("Shows how the body rocks over relative to seat position. Ideal technique requires the body to be 'set' before the knees rise.")
plot_trunk_angle_separation(avg_cycle, catch_idx, finish_idx, scenario_data=scenario_avg, scenario_name=selected_scenario)

st.subheader("2. Rhythm Consistency")
st.markdown("Comparison of SPM and Drive/Recovery ratio across all strokes. A tight cluster indicates professional-grade consistency.")
plot_ratio_consistency(results)

st.subheader("3. Handle-Seat Distance")
st.markdown("Measures compression. Ideally, you want a long reaching distance at the catch without losing core stability.")
plot_handle_seat_distance(avg_cycle, catch_idx, finish_idx, scenario_data=scenario_avg, scenario_name=selected_scenario)

st.subheader("4. Recovery Slide Control")
st.markdown("Seat velocity during the recovery phase. Look for a controlled 'slow-down' before arriving at the catch.")
plot_recovery_control(avg_cycle, finish_idx, scenario_name=selected_scenario)

st.markdown("---")
st.subheader("5. Handle Trajectory (Box Plot)")
st.markdown("The vertical vs. horizontal path of the handle. A rectangular shape indicates consistent blade depth and clean extraction.")
plot_handle_trajectory(avg_cycle, catch_idx, finish_idx, scenario_data=scenario_avg, scenario_name=selected_scenario)

st.markdown("---")
st.caption(f"Analysis complete for **{data_label}**.")
