"""
app.py – Dot Camp Selection Engine entry point.

Run:  streamlit run app.py
"""

import hashlib, json
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

# ── Add startups (must come before results so filter changes are picked up) ───
render_add_startup(active_config)

st.divider()

# ── Evaluate all startups (after add section so new filters/startups are live) ─
startups = st.session_state["startups"]


def _config_hash(config: dict) -> str:
    """Cheap hash of the active config so we only re-evaluate when it changes."""
    try:
        return hashlib.md5(json.dumps(config, default=str, sort_keys=True).encode()).hexdigest()
    except Exception:
        return ""


_cache_key  = f"results_cache_{_config_hash(active_config)}_{len(startups)}"
if st.session_state.get("_results_key") != _cache_key or "results_all" not in st.session_state:
    st.session_state["results_all"]  = [evaluate(a, config=active_config) for a in startups]
    st.session_state["_results_key"] = _cache_key

results_all = st.session_state["results_all"]

# ── Stats bar ─────────────────────────────────────────────────────────────────
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

# ── Results table ─────────────────────────────────────────────────────────────
render_results_table(active_config, results_all)