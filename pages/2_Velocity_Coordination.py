import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.plot_transforms import get_plot_component
from rowing_catch.plots.velocity import render_velocity_coordination
from rowing_catch.scenario.scenarios import create_scenario_data, get_coordination_scenarios

st.set_page_config(page_title='Velocity Coordination Analysis', layout='wide')

st.title('Seat vs. Handle Velocity Coordination')

st.markdown("""
### Deep Dive: Velocity Coordination
This metric analyzes the coordination between the legs (seat velocity) and the upper body/arms
(handle velocity) during the drive phase.

#### What to look for:
- **Peak Overlap:** Ideally, the peaks of the seat and handle velocities should overlap or be very close
  together. This indicates that the power from the legs is being effectively transferred through the
  back and arms to the handle.
- **Shooting the Slide:** If the **Orange Peak** (Seat) occurs significantly before the **Purple Peak**
  (Handle), it identifies "shooting the slide." This means the legs are moving, but the handle is
  not accelerating proportionally, leading to power loss.

#### How to read this diagram:
- The **Orange Line** is the seat's horizontal velocity.
- The **Blue-Purple Line** is the handle's horizontal velocity.
- The vertical lines mark the **Catch** (Green) and **Finish** (Red).
""")

# Scenario Loader
st.sidebar.header('Scenario Selector')
scenarios = get_coordination_scenarios()
selected_scenario = st.sidebar.selectbox('Choose a technical scenario', list(scenarios.keys()))

if selected_scenario:
    st.sidebar.markdown(f'**Description:** {scenarios[selected_scenario]}')

    df = create_scenario_data('Coordination', selected_scenario)
    results = process_rowing_data(df)

    if results:
        # Get plot component and compute plot-ready data
        component = get_plot_component('velocity')
        computed = component.compute(
            avg_cycle=results['avg_cycle'],
            catch_idx=results['catch_idx'],
            finish_idx=results['finish_idx'],
            results=results,
        )

        # Render plot
        render_velocity_coordination(computed)
    else:
        st.error('Could not process the selected scenario.')

st.sidebar.markdown('---')
st.sidebar.info('Coach: Use this to explain the connection between the legs and the handle.')
