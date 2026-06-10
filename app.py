"""
app.py – Dot Camp Selection Engine entry point.

Run:  streamlit run app.py
"""

import streamlit as st

from engine import evaluate
from ui.styles import inject_css
from ui.sidebar import render_sidebar
from ui.add_startup import render_add_startup
from ui.results_table import render_results_table

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dot Camp – Selection Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Session state ─────────────────────────────────────────────────────────────
if "startups" not in st.session_state:
    st.session_state["startups"] = []

# ── Sidebar → active config ───────────────────────────────────────────────────
active_config = render_sidebar()

# ── Main header ───────────────────────────────────────────────────────────────
st.markdown("# Dot Camp – Startup Selection Engine")
st.divider()

# ── Stats bar ─────────────────────────────────────────────────────────────────
startups = st.session_state["startups"]
results_all = [evaluate(a, config=active_config) for a in startups] if startups else []

n_total = len(startups)
n_sel   = sum(1 for r in results_all if r.final_decision in ("Selected ★", "Selected"))
n_short = sum(1 for r in results_all if r.final_decision in ("Shortlisted ✓", "Shortlisted"))
n_rej   = sum(1 for r in results_all if r.final_decision == "Rejected")

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Total startups", n_total)
col_b.metric("Selected",       n_sel)
col_c.metric("Shortlisted",    n_short)
col_d.metric("Rejected",       n_rej)

st.divider()

# ── Add startups ──────────────────────────────────────────────────────────────
render_add_startup(active_config)

st.divider()

# ── Results table ─────────────────────────────────────────────────────────────
render_results_table(active_config, results_all)
