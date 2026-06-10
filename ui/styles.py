"""
ui/styles.py – Inject global CSS and expose shared Streamlit styling helpers.
"""

import streamlit as st
from utils import DECISION_COLORS


def inject_css() -> None:
    """Call once at the top of app.py to apply global styles."""
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Serif+Display&display=swap');
          html, body, [class*="css"] { font-family: 'DM Mono', monospace; }
          h1, h2, h3 { font-family: 'DM Serif Display', serif !important; }
          .stMetric label { font-size: 11px; letter-spacing: 2px; text-transform: uppercase; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def decision_badge(decision: str) -> str:
    """Return an inline HTML badge for the given decision string."""
    c = DECISION_COLORS.get(decision, "#888")
    return (
        f"<span style='background:{c}22;color:{c};font-weight:700;"
        f"padding:3px 8px;border-radius:4px;font-size:12px'>{decision}</span>"
    )


def decision_banner(decision: str, emoji: str = "") -> str:
    """Return a full-width banner div (used after manual evaluation)."""
    c = DECISION_COLORS.get(decision, "#888")
    label = f"{emoji} {decision}".strip()
    return (
        f"<div style='background:{c}22;border-left:5px solid {c};"
        f"padding:16px;border-radius:8px;font-size:20px;font-weight:bold;color:{c}'>"
        f"{label}</div>"
    )


def color_decision(val: str) -> str:
    """Pandas Styler cell formatter."""
    c = DECISION_COLORS.get(val, "")
    return f"background-color: {c}22; color: {c}; font-weight: bold;" if c else ""
