import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.plot_transformer.trunk.trunk_angle_transformer import TrunkAngleComponent
from rowing_catch.plot.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.scenario.scenarios import create_scenario_data, get_trunk_scenarios

st.title('Trunk Angle & Range Analysis')

# Scenario Loader (Programmatic scenarios for coaching)
st.sidebar.header('Scenario Selector')
scenarios = get_trunk_scenarios()
scenario_names = list(scenarios.keys())

# Provide short text for the immediate option caption
scenario_captions = [scenarios[name]['description'] for name in scenario_names]

selected_scenario = st.sidebar.radio('Choose a technical scenario', options=scenario_names, captions=scenario_captions)

st.sidebar.divider()

ghost_options = ['None'] + scenario_names
ghost_captions = ['No comparison line'] + scenario_captions
selected_ghost = st.sidebar.radio(
    'Compare with (Ghost line)',
    options=ghost_options,
    captions=ghost_captions,
)

if selected_scenario:
    df = create_scenario_data('Trunk', selected_scenario)
    results = process_rowing_data(df)

    if results:
        # Get plot component and compute plot-ready data
        component = TrunkAngleComponent()

        ghost_cycle = None
        if selected_ghost != 'None':
            ghost_df = create_scenario_data('Trunk', selected_ghost)
            ghost_results = process_rowing_data(ghost_df)
            if ghost_results:
                ghost_cycle = ghost_results['avg_cycle']

        computed = component.compute(
            avg_cycle=results['avg_cycle'],
            catch_idx=results['catch_idx'],
            finish_idx=results['finish_idx'],
            ghost_cycle=ghost_cycle,
            results=results,
        )

        # Render plot
        render_trunk_angle_with_stage_stickfigures(computed)
    else:
        st.error('Could not process the selected scenario.')

st.markdown("""
### Deep Dive: Trunk Angle
The trunk angle is a critical biomechanical metric that measures the rower's lean relative to the vertical axis.
- **At the Catch:** A forward lean (typically -30° to -25°) allows for a longer stroke and better
  engagement of the powerful leg muscles.
- **At the Finish:** A slight backward lean (typically 10° to 15°) ensures a clean extraction
  of the blade and completes the power phase.
- **Range:** The total degrees of movement between catch and finish.

#### How to read this diagram:
- The **Blue Line** shows your trunk angle throughout one average stroke.
- The **Green Shaded Zone** is the ideal catch angle.
- The **Red-Orange Shaded Zone** is the ideal finish angle.
- Vertical dashed lines mark the **Catch** (Green) and **Finish** (Red) as detected by your seat movement.
""")
