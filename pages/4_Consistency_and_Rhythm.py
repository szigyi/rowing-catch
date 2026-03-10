import streamlit as st
import pandas as pd
import os
from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.algo.scenarios import create_scenario_data, get_consistency_scenarios
from rowing_catch.ui.components import plot_consistency_rhythm

st.set_page_config(page_title="Consistency & Rhythm Analysis", layout="wide")

st.title("✅ Consistency & Rhythm Analysis")

st.markdown("""
### Deep Dive: Rhythm and Consistency
These metrics focus on the stability and timing of the rower's movement.

#### Stroke Consistency Score (CV):
- **Coefficient of Variation (CV):** Measures how much the stroke length and duration vary across all recorded strokes.
- **Professional Goal:** < 2% variability. Lower numbers mean a more "robotic" and repeatable rhythm.

#### Drive/Recovery Ratio:
- **Drive Phase:** The "Work" phase where the rower is pushing against the water.
- **Recovery Phase:** The "Rest" phase where the rower moves back to the catch.
- **Ideal Ratio:** At lower stroke rates (like 20 SPM), the ideal is roughly 1:2 (33% Drive / 66% Recovery). This allows for maximum muscle recovery between powerful drives.
""")

# Scenario Loader
st.sidebar.header("Scenario Selector")
scenarios = get_consistency_scenarios()
selected_scenario = st.sidebar.selectbox("Choose a technical scenario", list(scenarios.keys()))

if selected_scenario:
    st.sidebar.markdown(f"**Description:** {scenarios[selected_scenario]}")
    
    df = create_scenario_data("Consistency", selected_scenario)
    results = process_rowing_data(df)
    
    if results:
        cv = results['cv_length']
        drive_p = (results['drive_len'] / results['min_length']) * 100
        rec_p = (results['recovery_len'] / results['min_length']) * 100
        
        plot_consistency_rhythm(cv, drive_p, rec_p)
    else:
        st.error("Could not process the selected scenario.")

st.sidebar.markdown("---")
st.sidebar.info("Coach: Use this to explain the 'Work vs. Rest' ratio and stability.")
