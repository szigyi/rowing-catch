"""Reusable Streamlit annotation toggle + reference table widget.

Renders an always-visible annotation table (no expander) containing:
  - A master "Show all" checkbox
  - One row per annotation: toggle checkbox | pill badge | description | coach tip

Always visible (not collapsible) so the table prints correctly with the page.

Usage (page layer)::

    active = render_annotation_toggles(
        annotations=computed.get('annotations', []),
        color_overrides={'[Z1]': COLOR_CATCH, '[Z2]': COLOR_FINISH},
        expander_label='Annotations',
        key_prefix='my_plot',
    )
    render_my_plot(computed, active_annotations=active)
"""

import dataclasses

import streamlit as st

from rowing_catch.plot_transformer.annotations import AnnotationEntry, assign_annotation_colors

# Pill badge: coloured background, white text, rounded corners.
_BADGE_HTML = (
    '<span style="display:inline-block;background:{color};color:#fff;'
    'font-size:0.75em;font-weight:bold;padding:2px 8px;border-radius:10px;'
    'white-space:nowrap">{label}</span>'
)

# Coach-tip pill: background signals ideal (green) or needs improvement (red).
_TIP_HTML = (
    '<span style="display:inline-block;background:{bg};color:{fg};'
    'font-size:0.78em;font-style:italic;padding:2px 8px;border-radius:6px">'
    '{tip}</span>'
)
_COLOR_IDEAL = ('#D1FAE5', '#065F46')
_COLOR_IMPROVE = ('#FEE2E2', '#991B1B')


def render_annotation_toggles(
    annotations: list[AnnotationEntry],
    color_overrides: dict[str, str] | None = None,
    expander_label: str = 'Annotations',
    key_prefix: str = 'ann',
) -> set[str] | None:
    """Render an always-visible annotation table with toggles.

    Each annotation row has four columns:
      1. Toggle — bare checkbox (no label), controls visibility on the plot
      2. Badge — coloured [Px] pill, reference ID and colour in one element
      3. Description — annotation text (inherits page text colour)
      4. Coach tip — green pill when ideal, red pill when improvement needed

    A master "Show all" checkbox at the top toggles every row at once.
    When the master is off, individual checkboxes are disabled (still visible)
    and an empty set is returned (all hidden).

    Args:
        annotations: List of AnnotationEntry objects from compute().
                     Empty list → returns None (meaning "show all" to renderers).
        color_overrides: Optional dict mapping annotation label → hex color string.
                         Applied on top of the auto-palette.
        expander_label: Heading text rendered above the toggle rows.
        key_prefix: Unique prefix for all st.checkbox widget keys.

    Returns:
        ``set[str]`` of active annotation labels, or ``None`` when annotations is empty.
    """
    if not annotations:
        return None

    colored = assign_annotation_colors(list(annotations))
    if color_overrides:
        colored = [dataclasses.replace(a, color=color_overrides[a.label]) if a.label in color_overrides else a for a in colored]

    st.markdown(
        f'<p style="font-size:0.85em;font-weight:600;margin:8px 0 4px 0">{expander_label}</p>',
        unsafe_allow_html=True,
    )
    show_all = st.checkbox('Show all annotations', value=True, key=f'{key_prefix}_show_all')
    st.markdown('<hr style="margin:4px 0 8px 0;border-color:#E8E8E8">', unsafe_allow_html=True)

    active: set[str] = set()

    for ann in colored:
        color = ann.color or '#888888'

        col_cb, col_badge, col_desc, col_tip = st.columns([0.05, 0.11, 0.43, 0.41], gap='small')

        with col_cb:
            checked = st.checkbox(
                f'Toggle {ann.label}',
                value=show_all,
                key=f'{key_prefix}_{ann.label}',
                disabled=not show_all,
                label_visibility='collapsed',
            )

        with col_badge:
            st.markdown(_BADGE_HTML.format(color=color, label=ann.label), unsafe_allow_html=True)

        with col_desc:
            st.markdown(
                f'<span style="font-size:0.88em">{ann.description}</span>',
                unsafe_allow_html=True,
            )

        with col_tip:
            if ann.coach_tip:
                bg, fg = _COLOR_IDEAL if ann.coach_tip_is_ideal else _COLOR_IMPROVE
                st.markdown(_TIP_HTML.format(bg=bg, fg=fg, tip=ann.coach_tip), unsafe_allow_html=True)

        if checked and show_all:
            active.add(ann.label)

    if not show_all:
        return set()

    return active


__all__ = ['render_annotation_toggles']
