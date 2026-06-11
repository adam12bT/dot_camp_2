"""
ui/results_table.py – Results table, decision overrides, remove, and Excel export.

Usage:
    from ui.results_table import render_results_table
    render_results_table(active_config, results_all)
"""

import streamlit as st

from engine import evaluate
from excel_export import build_excel
from utils import DECISION_COLORS, OVERRIDE_OPTIONS
from ui.styles import decision_badge, color_decision


def render_results_table(active_config: dict, results_all: list) -> None:
    startups = st.session_state.get("startups", [])
    if not startups:
        st.info("No startups yet. Use the tabs above to add startups manually, or upload a CSV / Typeform JSON.")
        return

    # ── Persist overrides in session state ────────────────────────────────────
    if "overrides" not in st.session_state:
        st.session_state["overrides"] = {}

    st.markdown("### 📊 All Startups")

    # ── Filter bar ────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([2, 2, 3])
    with fc1:
        filter_decision = st.multiselect(
            "Filter by decision", OVERRIDE_OPTIONS,
            default=[], key="ov_filter_dec", placeholder="All decisions",
        )
    with fc2:
        filter_sector = st.multiselect(
            "Filter by sector",
            options=sorted({a["sector"] for a in startups if a.get("sector")}),
            default=[], key="ov_filter_sec", placeholder="All sectors",
        )
    with fc3:
        search_text = st.text_input("🔍 Search startup name", key="ov_search", placeholder="Type to filter...")

    # Apply effective decision (override takes precedence)
    def _effective_decision(a, r):
        return st.session_state["overrides"].get(a["startup_name"], r.final_decision)

    evaluated_all = list(zip(startups, results_all))
    filtered = evaluated_all
    if filter_decision:
        filtered = [(a, r) for a, r in filtered if _effective_decision(a, r) in filter_decision]
    if filter_sector:
        filtered = [(a, r) for a, r in filtered if a.get("sector") in filter_sector]
    if search_text:
        filtered = [(a, r) for a, r in filtered if search_text.lower() in a["startup_name"].lower()]

    st.caption(f"Showing **{len(filtered)}** of **{len(startups)}** startups")

    # ── Header row ────────────────────────────────────────────────────────────
    hcols = st.columns([3, 2, 2, 2, 3, 3, 3])
    for col, lbl in zip(hcols, ["**Startup**", "**Sector**", "**Age**", "**Bonus**",
                                  "**Decision**", "**Reason**", "**Override**"]):
        col.markdown(lbl)
    st.divider()

    for idx, (a, r) in enumerate(filtered):
        row_cols = st.columns([3, 2, 2, 2, 3, 3, 3])

        row_cols[0].markdown(
            f"**{a['startup_name']}**  \n"
            f"<span style='font-size:11px;color:#888'>{a.get('governorate','')}</span>",
            unsafe_allow_html=True,
        )
        row_cols[1].markdown(
            f"<span style='font-size:12px'>{a.get('sector') or '—'}</span>",
            unsafe_allow_html=True,
        )
        row_cols[2].markdown(
            f"<span style='font-size:12px'>{a.get('age') or '—'}</span>  \n"
            f"<span style='font-size:11px;color:#aaa'>{a.get('maturity','')}</span>",
            unsafe_allow_html=True,
        )
        row_cols[3].markdown(f"**{r.bonus_score}**")

        # Show effective decision (may be overridden)
        eff_decision = _effective_decision(a, r)
        row_cols[4].markdown(decision_badge(eff_decision), unsafe_allow_html=True)

        if r.rejection_reason:
            reason_html = f"<span style='color:#ff4d6d;font-size:11px'>✗ {r.rejection_reason}</span>"
        elif r.bonus_details:
            reason_html = f"<span style='color:#00e5a0;font-size:11px'>✓ {' · '.join(r.bonus_details)}</span>"
        else:
            reason_html = "<span style='color:#666;font-size:11px'>—</span>"
        row_cols[5].markdown(reason_html, unsafe_allow_html=True)

        default_idx = OVERRIDE_OPTIONS.index(eff_decision) if eff_decision in OVERRIDE_OPTIONS else 0
        new_dec = row_cols[6].selectbox(
            "override", OVERRIDE_OPTIONS, index=default_idx,
            key=f"ov_{idx}_{a['startup_name']}", label_visibility="collapsed",
        )
        # Persist override immediately (survives rerun)
        if new_dec != r.final_decision:
            st.session_state["overrides"][a["startup_name"]] = new_dec
        elif a["startup_name"] in st.session_state["overrides"] and new_dec == r.final_decision:
            # User reset back to engine decision — clear the override
            del st.session_state["overrides"][a["startup_name"]]

    # ── Active overrides summary ───────────────────────────────────────────────
    active_overrides = st.session_state["overrides"]
    if active_overrides:
        st.divider()
        st.markdown(f"#### ✏️ {len(active_overrides)} active override(s):")
        for name_ov, dec_ov in active_overrides.items():
            c = DECISION_COLORS.get(dec_ov, "#888")
            st.markdown(
                f"- **{name_ov}** → <span style='color:{c};font-weight:700'>{dec_ov}</span>",
                unsafe_allow_html=True,
            )
        if st.button("🗑 Clear all overrides", key="btn_clear_overrides"):
            st.session_state["overrides"] = {}
            st.rerun()

    # ── Remove startup ────────────────────────────────────────────────────────
    st.divider()
    with st.expander("🗑 Remove a startup", expanded=False):
        names_list = [a["startup_name"] for a in startups]
        to_remove  = st.selectbox("Select startup to remove", ["— select —"] + names_list, key="remove_select")
        if to_remove != "— select —" and st.button("Remove", key="btn_remove"):
            st.session_state["startups"] = [a for a in startups if a["startup_name"] != to_remove]
            st.session_state["overrides"].pop(to_remove, None)
            # Invalidate results cache
            st.session_state.pop("results_all", None)
            st.session_state.pop("_results_key", None)
            st.success(f"Removed **{to_remove}**")
            st.rerun()

    # ── Excel export ──────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📥 Export to Excel")
    n_total = len(startups)
    n_filters = len(active_config.get("filters", []))
    n_overrides = len(active_overrides)
    st.caption(
        f"Generates a fresh workbook from all {n_total} startup(s) using the **current filter pipeline** "
        f"({n_filters} filter(s))"
        + (f", with **{n_overrides} decision override(s)** applied" if n_overrides else "")
        + "."
    )
    if st.button("🔄 Generate Excel", type="primary"):
        xl_bytes = build_excel(startups, active_config, overrides=active_overrides)
        st.download_button(
            "⬇️ Download Excel",
            data=xl_bytes,
            file_name=f"DotCamp_Selection_{active_config['name'].replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True,
        )