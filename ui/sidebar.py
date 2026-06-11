"""
ui/sidebar.py – Renders the entire sidebar and returns the active_config dict.

Usage:
    from ui.sidebar import render_sidebar
    active_config = render_sidebar()
"""

import json
import os

import streamlit as st

from camp_config import ALL_CONFIGS
from engine import MATURITY_OPTIONS
from utils import ALL_AGE_GROUPS, AGE_LABEL_MAP


# ── Filter type registry ──────────────────────────────────────────────────────
FILTER_TYPES = [
    "age_reject", "legal_check", "boolean_field", "multi_boolean",
    "maturity_outcome", "field_in", "field_not_in", "min_employees",
    "ai_code",
]


# ── Internal: render params UI for each filter type ──────────────────────────

def _render_age_reject(params: dict, idx: int) -> dict:
    params["reject_groups"] = st.multiselect(
        "Reject these age groups", options=ALL_AGE_GROUPS,
        default=params.get("reject_groups", [">7"]),
        format_func=lambda x: AGE_LABEL_MAP[x], key=f"p_rg_{idx}",
    )
    return params


def _render_legal_check(params: dict, idx: int) -> dict:
    params["required_for"] = st.multiselect(
        "Required for age groups", options=ALL_AGE_GROUPS,
        default=params.get("required_for", ["2-5"]),
        format_func=lambda x: AGE_LABEL_MAP[x], key=f"p_lc_{idx}",
    )
    return params


def _render_boolean_field(params: dict, idx: int) -> dict:
    params["field"]   = st.text_input("App field key",        value=params.get("field", ""),   key=f"p_bf_field_{idx}")
    params["label"]   = st.text_input("Field label",          value=params.get("label", ""),   key=f"p_bf_label_{idx}")
    params["message"] = st.text_input("Rejection message",    value=params.get("message", ""), key=f"p_bf_msg_{idx}")
    return params


def _render_multi_boolean(params: dict, idx: int) -> dict:
    raw_fields = st.text_input(
        "Fields (comma-separated keys)",
        value=", ".join(params.get("fields", [])), key=f"p_mb_fields_{idx}",
    )
    raw_labels = st.text_input(
        "Labels (comma-separated)",
        value=", ".join(params.get("labels", [])), key=f"p_mb_labels_{idx}",
    )
    params["fields"]  = [s.strip() for s in raw_fields.split(",") if s.strip()]
    params["labels"]  = [s.strip() for s in raw_labels.split(",") if s.strip()]
    params["mode"]    = st.radio(
        "Mode", ["all", "any"],
        index=0 if params.get("mode", "all") == "all" else 1,
        horizontal=True, key=f"p_mb_mode_{idx}",
    )
    params["message"] = st.text_input(
        "Rejection message (optional)", value=params.get("message", ""), key=f"p_mb_msg_{idx}",
    )
    return params


def _render_maturity_outcome(params: dict, idx: int) -> dict:
    st.caption("Set the outcome for each (age group, maturity) pair.")
    outcomes = dict(params.get("outcomes", {}))
    new_outcomes: dict = {}
    outcome_opts = ["Rejected", "Shortlisted", "Selected"]
    for ag in ALL_AGE_GROUPS:
        st.markdown(f"**{AGE_LABEL_MAP[ag]}**")
        for mat in MATURITY_OPTIONS:
            cur = outcomes.get((ag, mat), "Rejected")
            val = st.selectbox(
                mat, outcome_opts,
                index=outcome_opts.index(cur) if cur in outcome_opts else 0,
                key=f"p_mo_{idx}_{ag}_{mat}",
            )
            if val != "Rejected":
                new_outcomes[(ag, mat)] = val
        st.divider()
    params["outcomes"] = new_outcomes
    return params


def _render_field_in(params: dict, idx: int) -> dict:
    params["field"]   = st.text_input("Field key", value=params.get("field", ""), key=f"p_fi_field_{idx}")
    raw = st.text_area(
        "Allowed values (one per line)", value="\n".join(params.get("allowed", [])),
        height=80, key=f"p_fi_allowed_{idx}",
    )
    params["allowed"] = [s.strip() for s in raw.splitlines() if s.strip()]
    params["message"] = st.text_input("Rejection message", value=params.get("message", ""), key=f"p_fi_msg_{idx}")
    return params


def _render_field_not_in(params: dict, idx: int) -> dict:
    params["field"]   = st.text_input("Field key", value=params.get("field", ""), key=f"p_fn_field_{idx}")
    raw = st.text_area(
        "Blocked values (one per line)", value="\n".join(params.get("blocked", [])),
        height=80, key=f"p_fn_blocked_{idx}",
    )
    params["blocked"] = [s.strip() for s in raw.splitlines() if s.strip()]
    params["message"] = st.text_input("Rejection message", value=params.get("message", ""), key=f"p_fn_msg_{idx}")
    return params


def _render_min_employees(params: dict, idx: int) -> dict:
    bands = ["None", "1–2", "3–5", "6–10", "+10"]
    params["field"]    = st.text_input("Field key", value=params.get("field", "total_employees"), key=f"p_me_field_{idx}")
    params["min_band"] = st.selectbox(
        "Minimum band", bands,
        index=bands.index(params["min_band"]) if params.get("min_band") in bands else 0,
        key=f"p_me_band_{idx}",
    )
    params["message"] = st.text_input("Rejection message", value=params.get("message", ""), key=f"p_me_msg_{idx}")
    return params



def _render_ai_code(params: dict, idx: int) -> dict:
    st.caption("AI-generated code filter. Edit code below if needed, then re-validate.")
    prompt_text = params.get("prompt", "")
    if prompt_text:
        st.markdown(f"**Original prompt:** {prompt_text}")
    raw = params.get("code", "")
    # Unescape \n sequences so the code displays with real newlines
    display = raw.replace("\\n", "\n")
    new_code = st.text_area(
        "Python function",
        value=display,
        height=180,
        key=f"p_ai_code_{idx}",
    )
    params["code"] = new_code
    if st.button("\U0001f50d Validate", key=f"p_ai_val_{idx}"):
        from ai_code_filter import validate_code
        ok, err = validate_code(new_code)
        if ok:
            st.success("\u2705 Valid")
        else:
            st.error(f"\u274c {err}")
    return params


_PARAM_RENDERERS = {
    "age_reject":       _render_age_reject,
    "legal_check":      _render_legal_check,
    "boolean_field":    _render_boolean_field,
    "multi_boolean":    _render_multi_boolean,
    "maturity_outcome": _render_maturity_outcome,
    "field_in":         _render_field_in,
    "field_not_in":     _render_field_not_in,
    "min_employees":    _render_min_employees,
    "ai_code":          _render_ai_code,
}



# ── Public entry-point ────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    """
    Render the full sidebar.
    Returns the active_config dict consumed by the engine and the rest of the UI.
    """
    with st.sidebar:
        st.markdown("## Dot Camp – Selection Engine")
        st.divider()

        # ── Preset selector ───────────────────────────────────────────────────
        st.markdown("### Camp Config")
        chosen_name = st.selectbox("Load preset", options=list(ALL_CONFIGS.keys()), key="camp_preset")
        base_cfg = ALL_CONFIGS[chosen_name]

        st.divider()
        st.markdown("### Filter Pipeline")
        st.caption("Add, remove, or reorder filters. Changes apply immediately.")

        # Initialise (or reset) filter list when preset changes
        if (
            "filter_list" not in st.session_state
            or st.session_state.get("_last_preset") != chosen_name
        ):
            st.session_state["filter_list"] = [dict(f) for f in base_cfg.get("filters", [])]
            st.session_state["_last_preset"] = chosen_name
            # Clear bonus checkbox state so new preset starts fresh
            for field_key, _, _ in base_cfg.get("bonus_fields", []):
                st.session_state.pop(f"cfg_bonus_{field_key}", None)

        active_filters: list[dict] = []

        for idx, fdef in enumerate(st.session_state["filter_list"]):
            with st.expander(fdef.get("label", f"Filter {idx + 1}"), expanded=False):
                col_label, col_del = st.columns([4, 1])
                with col_label:
                    new_label = st.text_input("Label", value=fdef.get("label", ""), key=f"flabel_{idx}")
                with col_del:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑", key=f"fdel_{idx}", help="Remove this filter"):
                        st.session_state["filter_list"].pop(idx)
                        st.rerun()

                ftype = st.selectbox(
                    "Filter type",
                    options=FILTER_TYPES,
                    index=FILTER_TYPES.index(fdef.get("type", "age_reject"))
                          if fdef.get("type") in FILTER_TYPES else 0,
                    key=f"ftype_{idx}",
                )

                params = dict(fdef.get("params", {}))
                renderer = _PARAM_RENDERERS.get(ftype)
                if renderer:
                    params = renderer(params, idx)

                active_filters.append({
                    "type":   ftype,
                    "label":  new_label or fdef.get("label", f"Filter {idx + 1}"),
                    "params": params,
                })

                mc1, mc2 = st.columns(2)
                with mc1:
                    if idx > 0 and st.button("↑ Move up", key=f"fup_{idx}"):
                        fl = st.session_state["filter_list"]
                        fl[idx - 1], fl[idx] = fl[idx], fl[idx - 1]
                        st.rerun()
                with mc2:
                    if idx < len(st.session_state["filter_list"]) - 1 and st.button("↓ Move down", key=f"fdown_{idx}"):
                        fl = st.session_state["filter_list"]
                        fl[idx], fl[idx + 1] = fl[idx + 1], fl[idx]
                        st.rerun()

        if st.button("➕ Add filter", use_container_width=True):
            st.session_state["filter_list"].append({
                "type":   "boolean_field",
                "label":  f"New filter {len(st.session_state['filter_list']) + 1}",
                "params": {},
            })
            st.rerun()

        st.divider()

        # ── Bonus scoring ─────────────────────────────────────────────────────
        st.markdown("### Bonus scoring")
        bc1, bc2 = st.columns(2)
        with bc1:
            star_thresh  = st.number_input("★ threshold",  min_value=1, max_value=8,
                                            value=base_cfg.get("star_threshold", 3),      key="cfg_star")
        with bc2:
            check_thresh = st.number_input("✓ threshold", min_value=1, max_value=8,
                                            value=base_cfg.get("checkmark_threshold", 2), key="cfg_check")

        st.markdown("**Active bonus fields**")
        active_bonus = [
            (field_key, blabel, fn_name)
            for field_key, blabel, fn_name in base_cfg.get("bonus_fields", [])
            if st.checkbox(blabel, value=True, key=f"cfg_bonus_{field_key}")
        ]

        st.divider()
        st.caption(f"Active config: **{chosen_name}**  |  {len(active_filters)} filter(s)")

    return {
        "name":                chosen_name,
        "filters":             active_filters,
        "bonus_fields":        active_bonus,
        "star_threshold":      int(star_thresh),
        "checkmark_threshold": int(check_thresh),
    }