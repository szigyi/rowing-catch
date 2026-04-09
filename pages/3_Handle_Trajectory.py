import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.plot_transforms import get_plot_component
from rowing_catch.plots.trajectory import render_handle_trajectory
from rowing_catch.scenario.scenarios import create_scenario_data, get_trajectory_scenarios

st.set_page_config(page_title='Handle Trajectory Analysis', layout='wide')

st.title("Handle Trajectory 'Box' Plot")

st.markdown("""
### Deep Dive: Handle Trajectory
The 'Box' plot shows the 2D path of the handle (Vertical vs. Horizontal) during a full stroke cycle.

#### Technical Goals:
- **Consistent Depth:** A professional stroke has a flat top line during the drive phase,
  indicating a consistent blade depth.
- **Clean Transitions:** The **Catch** (Green dot) and **Finish** (Red dot) should be sharp and efficient.
- **Minimal "Dipping":** Skewed or dipping paths often indicate "digging" (too deep) or "skying"
  (handle too high before the catch).

#### How to read this diagram:
- The **Blue-Purple Line** is your actual handle path.
- The **Gray Dashed Box** is the ideal reference path based on your current stroke length.
- The **Green Dot** is the catch point.
- The **Red Dot** is the finish point.
- *Note: The vertical axis is inverted to match common coaching perspectives (up is higher, down is deeper).*
""")

# Scenario Loader
st.sidebar.header('Scenario Selector')
scenarios = get_trajectory_scenarios()
selected_scenario = st.sidebar.selectbox('Choose a technical scenario', list(scenarios.keys()))

if selected_scenario:
    st.sidebar.markdown(f'**Description:** {scenarios[selected_scenario]}')

    df = create_scenario_data('Trajectory', selected_scenario)
    results = process_rowing_data(df)

    if results:
        # Get plot component and compute plot-ready data
        component = get_plot_component('trajectory')
        computed = component.compute(
            avg_cycle=results['avg_cycle'],
            catch_idx=results['catch_idx'],
            finish_idx=results['finish_idx'],
            results=results,
        )

        # Render plot
        render_handle_trajectory(computed)
    else:
        st.error('Could not process the selected scenario.')

st.sidebar.markdown('---')
st.sidebar.info('Coach: Use this to identify technical errors like digging or skying.')
