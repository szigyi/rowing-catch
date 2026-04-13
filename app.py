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
            st.Page('rowing_catch/page/report.py', title='Analysis Report', icon='📊', default=True),
            st.Page('rowing_catch/page/development.py', title='Development', icon='🏋️'),
            st.Page('rowing_catch/page/performance.py', title='Performance', icon='⚡'),
        ],
        'Coach': [
            st.Page('rowing_catch/page/coaching_profile.py', title='Coaching Profile', icon='🎯'),
        ],
        'Debug': [
            st.Page('rowing_catch/page/debug_pipeline.py', title='Debug Pipeline', icon='🔬'),
            st.Page('rowing_catch/page/debug_trace.py', title='Debug Trace', icon='🔍'),
        ],
    }
)

pg.run()
