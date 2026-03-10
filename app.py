import streamlit as st
import pandas as pd

from rowing_catch.algo.analysis import process_rowing_data, get_traffic_light
from rowing_catch.ui.components import (
    plot_trunk_angle, 
    plot_velocity_coordination, 
    plot_handle_trajectory, 
    plot_consistency_rhythm
)

st.set_page_config(page_title="The Rowing Catch - Rowing Analysis Report", layout="wide")

st.title("🚣 The Rowing Catch - Rowing Analysis Report")
st.markdown("""
Upload your raw trajectory data (CSV) to generate a comprehensive technical report.
You can also explore detailed explanations of each metric using the sidebar navigation.
""")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    results = process_rowing_data(df)
    
    if results is None:
        st.error("Could not detect enough stroke cycles in the data. Please check the file format.")
    else:
        avg_cycle = results['avg_cycle']
        catch_idx = results['catch_idx']
        finish_idx = results['finish_idx']
        
        # --- Sidebar Metrics ---
        st.sidebar.header("Key Performance Indicators")
        
        # Consistency
        cv = results['cv_length']
        status, icon = get_traffic_light(cv, 2, green_threshold=2, yellow_threshold=5) # Ideal CV < 2%
        st.sidebar.metric("Consistency (CV)", f"{cv:.2f}%", help="Professional Goal < 2%")
        st.sidebar.write(f"Status: {icon} {status}")
        
        # Drive/Recovery Ratio
        drive_p = (results['drive_len'] / results['min_length']) * 100
        rec_p = (results['recovery_len'] / results['min_length']) * 100
        # Ideal at low rates is roughly 1:2 (33% drive)
        ratio_status, ratio_icon = get_traffic_light(drive_p, 33, green_threshold=5, yellow_threshold=15)
        st.sidebar.metric("Drive/Recovery Ratio", f"{drive_p:.1f}% / {rec_p:.1f}%")
        st.sidebar.write(f"Status: {ratio_icon} {ratio_status}")

        # --- Main Report ---
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("1. Biomechanical & Technical Efficiency")
            
            # Trunk Angle Plot
            st.write("#### ✅ Trunk Angle & Range Analysis")
            plot_trunk_angle(avg_cycle, catch_idx, finish_idx)

            # Coordination Plot
            st.write("#### ✅ Seat vs. Handle Velocity Coordination")
            plot_velocity_coordination(avg_cycle, catch_idx, finish_idx)

        with col2:
            st.subheader("2. Consistency & Rhythm")
            
            # Handle Trajectory
            st.write("#### ✅ Handle Trajectory 'Box' Plot")
            plot_handle_trajectory(avg_cycle, catch_idx, finish_idx)
            
            # Consistency Score & Drive/Recovery Ratio
            st.write("#### ✅ Consistency & Rhythm Analysis")
            plot_consistency_rhythm(cv, drive_p, rec_p)

else:
    st.info("Please upload a CSV file from the `resources` folder to see the analysis.")
    # Example files info
    st.write("Example files available in `resources/`:")
    st.code("2023.12.27.Szabi_20strokesPerMinute_trajectory.csv\n2023.12.27.Szabi_36strokesPerMinute_trajectory.csv")
