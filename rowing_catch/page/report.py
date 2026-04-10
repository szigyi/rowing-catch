"""Main Rowing Analysis Report page."""

import os

import pandas as pd
import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.plot_transformer.trunk.trunk_angle_transformer import TrunkAngleComponent
from rowing_catch.plot.trunk_angle_plot import render_trunk_angle_with_stage_stickfigures
from rowing_catch.plot.utils import get_traffic_light

st.title('The Rowing Catch — Rowing Analysis Report')
st.markdown(
    'Upload your raw trajectory data (CSV) to generate a comprehensive technical report. '
    'You can also explore detailed explanations of each metric using the sidebar navigation.'
)

# --- File Selection Section ---
col_u1, col_u2 = st.columns([2, 1])

with col_u1:
    uploaded_file = st.file_uploader('Upload your trajectory CSV', type='csv')

with col_u2:
    resource_dir = 'resources'
    example_files: list[str] = []
    if os.path.exists(resource_dir):
        example_files = [f for f in os.listdir(resource_dir) if f.endswith('.csv') and 'trajectory' in f.lower()]

    selected_example = st.selectbox(
        'Or choose an example file',
        options=['None'] + sorted(example_files),
        help='Quickly test the analysis with provided example data.',
    )

# --- Data Loading ---
df: pd.DataFrame | None = None
data_source_name: str | None = None

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    data_source_name = uploaded_file.name
elif selected_example != 'None':
    df = pd.read_csv(os.path.join(resource_dir, selected_example))
    data_source_name = selected_example

if df is not None:
    st.info(f'Analyzing: **{data_source_name}**')
    results = process_rowing_data(df)

    if results is None:
        st.error('Could not detect enough stroke cycles in the data. Please check the file format.')
    else:
        st.sidebar.header('Key Performance Indicators')

        cv = results['cv_length']
        status = get_traffic_light(cv, 2, green_threshold=2, yellow_threshold=5)
        st.sidebar.metric('Consistency (CV)', f'{cv:.2f}%', help='Professional Goal < 2%')
        if status == 'Green':
            st.sidebar.success(f'Status: {status}')
        elif status == 'Yellow':
            st.sidebar.warning(f'Status: {status}')
        else:
            st.sidebar.error(f'Status: {status}')

        drive_p = (results['drive_len'] / results['min_length']) * 100
        rec_p = (results['recovery_len'] / results['min_length']) * 100
        ratio_status = get_traffic_light(drive_p, 33, green_threshold=5, yellow_threshold=15)
        st.sidebar.metric('Drive/Recovery Ratio', f'{drive_p:.1f}% / {rec_p:.1f}%')
        if ratio_status == 'Green':
            st.sidebar.success(f'Status: {ratio_status}')
        elif ratio_status == 'Yellow':
            st.sidebar.warning(f'Status: {ratio_status}')
        else:
            st.sidebar.error(f'Status: {ratio_status}')

        col1, col2 = st.columns(2)

        with col1:
            st.subheader('1. Biomechanical & Technical Efficiency')
            st.write('#### Trunk Angle & Range Analysis')
            component = TrunkAngleComponent()
            computed = component.compute(
                avg_cycle=results['avg_cycle'],
                catch_idx=results['catch_idx'],
                finish_idx=results['finish_idx'],
                results=results,
            )
            render_trunk_angle_with_stage_stickfigures(computed)

        with col2:
            st.subheader('2. Performance Metrics')

else:
    st.info('Please upload a CSV file from the `resources` folder to see the analysis.')
    st.write('Example files available in `resources/`:')
    st.code('2023.12.27.Szabi_20strokesPerMinute_trajectory.csv\n2023.12.27.Szabi_36strokesPerMinute_trajectory.csv')
