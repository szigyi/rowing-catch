"""Rowing Catch — app entry point and navigation router."""

import streamlit as st

st.set_page_config(
    page_title='The Rowing Catch',
    layout='wide',
    page_icon='🚣',
)

pg = st.navigation(
    {
        'Analysis': [
            st.Page('rowing_catch/pages/report.py', title='Analysis Report', icon='📊', default=True),
            st.Page('rowing_catch/pages/trunk_angle.py', title='Trunk Angle', icon='📐'),
            st.Page('rowing_catch/pages/development.py', title='Development', icon='🏋️'),
            st.Page('rowing_catch/pages/performance.py', title='Performance', icon='⚡'),
        ],
        'Debug': [
            st.Page('rowing_catch/pages/debug_pipeline.py', title='Debug Pipeline', icon='🔬'),
            st.Page('rowing_catch/pages/debug_trace.py', title='Debug Trace', icon='🔍'),
        ],
    }
)

pg.run()
