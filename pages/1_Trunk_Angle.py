import streamlit as st
from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.algo.scenarios import create_scenario_data, get_trunk_scenarios
from rowing_catch.ui.components import plot_trunk_angle_with_stage_stickfigures

st.set_page_config(page_title="Trunk Angle Analysis", layout="wide")

st.title("✅ Trunk Angle & Range Analysis")

st.markdown("""
### Deep Dive: Trunk Angle
The trunk angle is a critical biomechanical metric that measures the rower's lean relative to the vertical axis. 
- **At the Catch:** A forward lean (typically -30° to -25°) allows for a longer stroke and better engagement of the powerful leg muscles.
- **At the Finish:** A slight backward lean (typically 10° to 15°) ensures a clean extraction of the blade and completes the power phase.
- **Range:** The total degrees of movement between catch and finish.

#### How to read this diagram:
- The **Purple Line** shows your trunk angle throughout one average stroke.
- The **Green Shaded Zone** is the ideal catch angle.
- The **Blue Shaded Zone** is the ideal finish angle.
- Vertical dashed lines mark the **Catch** (Green) and **Finish** (Red) as detected by your seat movement.
""")

# Scenario Loader (Programmatic scenarios for coaching)
st.sidebar.header("Scenario Selector")
scenarios = get_trunk_scenarios()
selected_scenario = st.sidebar.selectbox("Choose a technical scenario", list(scenarios.keys()))

if selected_scenario:
    st.sidebar.markdown(f"**Description:** {scenarios[selected_scenario]['description']}")
    
    df = create_scenario_data("Trunk", selected_scenario)
    results = process_rowing_data(df)

    if results:
        avg_cycle = results['avg_cycle']
        catch_idx = results['catch_idx']
        finish_idx = results['finish_idx']
        
        plot_trunk_angle_with_stage_stickfigures(avg_cycle, catch_idx, finish_idx)
    else:
        st.error("Could not process the selected scenario.")

st.sidebar.markdown("---")
st.sidebar.info("Use these scenarios to explain different technical situations to the rower.")
