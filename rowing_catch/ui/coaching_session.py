"""Session-state helpers for the coaching profile.

This module imports Streamlit and must only be used in Layer 4 (pages/UI).
It reads from and writes to ``st.session_state`` so that the active
``CoachingProfile`` is shared across all pages within a single browser session.
"""

from typing import cast

import streamlit as st

from rowing_catch.coaching.profile import DEFAULT_COACHING_PROFILE, CoachingProfile


def get_coaching_profile() -> CoachingProfile:
    """Return the current coaching profile from session state.

    If no profile has been saved yet, the ``DEFAULT_COACHING_PROFILE`` is
    stored and returned.

    Returns:
        The active ``CoachingProfile`` for this session.
    """
    if 'coaching_profile' not in st.session_state:
        st.session_state['coaching_profile'] = DEFAULT_COACHING_PROFILE
    return cast(CoachingProfile, st.session_state['coaching_profile'])


def save_coaching_profile(profile: CoachingProfile) -> None:
    """Persist a coaching profile to session state.

    Args:
        profile: The ``CoachingProfile`` to store for the current session.
    """
    st.session_state['coaching_profile'] = profile


__all__ = [
    'get_coaching_profile',
    'save_coaching_profile',
]
