import os
from typing import Any

import pandas as pd
import streamlit as st

from rowing_catch.algo.analysis import process_rowing_data
from rowing_catch.scenario.scenarios import (
    create_scenario_data,
    get_consistency_scenarios,
    get_coordination_scenarios,
    get_trajectory_scenarios,
    get_trunk_scenarios,
)


def render_sidebar_and_process() -> tuple[dict[str, Any], pd.DataFrame | None, str, str]:
    """
    Renders common sidebar (Data Source + Scenarios) and processes the data.
    Returns:
        results: Dictionary with avg_cycle, catch_idx, finish_idx, etc.
        scenario_avg: Average cycle for the selected comparison scenario.
        selected_scenario: Name of the selected scenario.
        data_label: Name of the loaded data file.
    """
    # --- Sidebar: Data Loading ---
    df_raw, data_label = _load_data_source()

    # --- Sidebar: Global Scenario Overlay ---
    selected_scenario, scenario_type = _get_selected_scenario()

    if df_raw is None:
        st.info('Please upload data or select an example in the sidebar.')
        st.stop()

    # --- Process User Data ---
    with st.spinner('Analyzing rowing strokes...'):
        results = process_rowing_data(df_raw)

    if results is None:
        st.error('Could not detect enough stable strokes in the data. Please check your tracking quality.')
        st.stop()

    avg_cycle = results['avg_cycle']

    # --- Process Scenario Data (Overlay) ---
    scenario_avg = _generate_scenario_overlay(selected_scenario, scenario_type, avg_cycle)

    return results, scenario_avg, selected_scenario, data_label


def _load_data_source() -> tuple[pd.DataFrame | None, str]:
    """Helper to handle data loading logic from sidebar."""
    st.sidebar.header('Data Source')
    source = st.sidebar.radio('Choose input', ['CSV Upload', 'Built-in Example'], index=1)

    df_raw = None
    data_label = ''

    if source == 'CSV Upload':
        uploaded = st.sidebar.file_uploader('Upload trajectory CSV', type='csv')
        if uploaded:
            df_raw = pd.read_csv(uploaded)
            data_label = uploaded.name
    else:
        resource_dir = 'resources'
        example_files = [f for f in os.listdir(resource_dir) if f.endswith('.csv')]
        default_file = '../../resources/2023.12.27.Szabi_36strokesPerMinute_trajectory.csv'
        # Find default file index safely
        try:
            default_idx = example_files.index(default_file)
        except ValueError:
            default_idx = 0

        selected_example = st.sidebar.selectbox('Pick an example', example_files, index=default_idx)
        df_raw = pd.read_csv(os.path.join(resource_dir, selected_example))
        data_label = selected_example

    return df_raw, data_label


def _get_selected_scenario() -> tuple[str, str | None]:
    """Helper to handle scenario selection logic from sidebar."""
    st.sidebar.markdown('---')
    st.sidebar.header('Global Scenario Overlay')

    trunk_scenarios = get_trunk_scenarios()
    traj_scenarios = get_trajectory_scenarios()
    coord_scenarios = get_coordination_scenarios()
    consis_scenarios = get_consistency_scenarios()

    # Simple flat list for the selectbox with type prefixing
    all_scenarios: dict[str, dict[str, Any]] = {'None': {'type': None}}
    for name, info in trunk_scenarios.items():
        all_scenarios[f'Trunk: {name}'] = {'type': 'Trunk', 'subtype': name, 'info': info}
    for name, info in traj_scenarios.items():
        all_scenarios[f'Path: {name}'] = {'type': 'Trajectory', 'subtype': name, 'info': info}
    for name, info in coord_scenarios.items():
        all_scenarios[f'Timing: {name}'] = {'type': 'Coordination', 'subtype': name, 'info': info}
    for name, info in consis_scenarios.items():
        all_scenarios[f'Rhythm: {name}'] = {'type': 'Consistency', 'subtype': name, 'info': info}

    selected_label = st.sidebar.selectbox('Compare against scenario', list(all_scenarios.keys()), index=0)
    config = all_scenarios[selected_label]

    if selected_label != 'None':
        info = config.get('info', '')
        desc = info.get('description', info.get('short', '')) if isinstance(info, dict) else str(info)
        st.sidebar.caption(desc)

    return config.get('subtype', 'None'), config.get('type')


def _generate_scenario_overlay(selected_scenario: str, scenario_type: str | None, avg_cycle: pd.DataFrame) -> pd.DataFrame | None:
    """Helper to generate scenario comparison data."""
    if selected_scenario == 'None' or avg_cycle is None:
        return None

    with st.spinner(f'Generating comparison: {selected_scenario}...'):
        s_min, s_max = float(avg_cycle['Seat_X_Smooth'].min()), float(avg_cycle['Seat_X_Smooth'].max())
        h_min, h_max = float(avg_cycle['Handle_X_Smooth'].min()), float(avg_cycle['Handle_X_Smooth'].max())

        df_scenario = create_scenario_data(
            scenario_type, selected_scenario, handle_x_range=(h_min, h_max), seat_x_range=(s_min, s_max)
        )
        scenario_results = process_rowing_data(df_scenario)
        return scenario_results.get('avg_cycle') if scenario_results else None
