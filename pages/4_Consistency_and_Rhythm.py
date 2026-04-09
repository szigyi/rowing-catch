import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.plot_transforms import get_plot_component
from rowing_catch.plots.rhythm import render_consistency_rhythm
from rowing_catch.scenario.scenarios import create_scenario_data, get_consistency_scenarios

st.set_page_config(page_title='Consistency & Rhythm Analysis', layout='wide')

st.title('Consistency & Rhythm Analysis')

st.markdown("""
### Deep Dive: Rhythm and Consistency
These metrics focus on the stability and timing of the rower's movement.

#### Stroke Consistency Score (CV):
- **Coefficient of Variation (CV):** Measures how much the stroke length and duration vary
  across all recorded strokes.
- **Professional Goal:** < 2% variability. Lower numbers mean a more "robotic" and repeatable rhythm.

#### Drive/Recovery Ratio:
- **Drive Phase:** The "Work" phase where the rower is pushing against the water.
- **Recovery Phase:** The "Rest" phase where the rower moves back to the catch.
- **Ideal Ratio:** At lower stroke rates (like 20 SPM), the ideal is roughly 1:2
  (33% Drive / 66% Recovery). This allows for maximum muscle recovery between powerful drives.
""")

# Scenario Loader
st.sidebar.header('Scenario Selector')
scenarios = get_consistency_scenarios()
selected_scenario = st.sidebar.selectbox('Choose a technical scenario', list(scenarios.keys()))

if selected_scenario:
    st.sidebar.markdown(f'**Description:** {scenarios[selected_scenario]}')

    df = create_scenario_data('Consistency', selected_scenario)
    results = process_rowing_data(df)

    if results:
        # Get plot component and compute plot-ready data
        component = get_plot_component('rhythm')
        computed = component.compute(
            avg_cycle=results['avg_cycle'],
            catch_idx=results['catch_idx'],
            finish_idx=results['finish_idx'],
            results=results,
        )

        # Render plot
        render_consistency_rhythm(computed)
    else:
        st.error('Could not process the selected scenario.')

st.sidebar.markdown('---')
st.sidebar.info("Coach: Use this to explain the 'Work vs. Rest' ratio and stability.")
