"""
ui/ai_filter_builder.py – Sidebar section for the AI code filter builder.

Replaces the old simple AI filter builder with a full code-generation +
preview + edit + validate + save workflow.
"""

import streamlit as st
from ai_code_filter import generate_filter_code, validate_code

from dotenv import load_dotenv
load_dotenv()

def render_ai_code_builder() -> None:
    """
    Renders the full AI Code Filter Builder UI inside the sidebar.
    On success, appends an 'ai_code' filter to st.session_state['filter_list'].
    """
    st.markdown("### 🤖 AI Code Filter Builder")
    st.caption("Describe any filter in plain English — AI writes the Python for you.")

    prompt = st.text_area(
        "Describe your filter",
        placeholder=(
            "e.g. Reject startups that have less than 3 employees "
            "and are not generating revenue"
        ),
        height=90,
        key="ai_code_prompt",
    )

    gen_col, _ = st.columns([2, 1])
    with gen_col:
        generate_clicked = st.button(
            "✨ Generate filter code",
            use_container_width=True,
            key="btn_ai_code_gen",
            type="primary",
        )

    # ── Generate ──────────────────────────────────────────────────────────────
    if generate_clicked:
        if not prompt.strip():
            st.warning("Please describe the filter first.")
        else:
            with st.spinner("Asking AI to write the filter…"):
                try:
                    result = generate_filter_code(prompt.strip())
                    raw_code = result["code"]
                    # Convert escaped \n sequences into real newlines for display
                    display_code = raw_code.replace("\\n", "\n")
                    st.session_state["ai_gen_label"] = result["label"]
                    st.session_state["ai_gen_code"]  = display_code
                    st.session_state["ai_gen_valid"] = None   # reset validation
                    st.success(f"✅ Generated **{result['label']}** — review and validate below.")
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    # ── Preview + edit + validate ─────────────────────────────────────────────
    if st.session_state.get("ai_gen_code"):
        st.divider()
        st.markdown("#### 📝 Review generated code")

        label = st.text_input(
            "Filter label",
            value=st.session_state.get("ai_gen_label", "AI Filter"),
            key="ai_code_label_input",
        )

        code = st.text_area(
            "Python function (editable)",
            value=st.session_state["ai_gen_code"],
            height=220,
            key="ai_code_editor",
        )
        # Keep code in sync with editor
        st.session_state["ai_gen_code"] = code

        # ── Validate ──────────────────────────────────────────────────────────
        val_col, save_col = st.columns(2)

        with val_col:
            if st.button("🔍 Validate", use_container_width=True, key="btn_ai_validate"):
                ok, err = validate_code(code)
                st.session_state["ai_gen_valid"] = (ok, err)

        # Show validation result
        valid_state = st.session_state.get("ai_gen_valid")
        if valid_state is not None:
            ok, err = valid_state
            if ok:
                st.success("✅ Code is valid — ready to add.")
            else:
                st.error(f"❌ Validation failed:\n```\n{err}\n```")

        # ── Save ──────────────────────────────────────────────────────────────
        with save_col:
            save_disabled = not (valid_state and valid_state[0])
            if st.button(
                "💾 Add to pipeline",
                use_container_width=True,
                key="btn_ai_save",
                disabled=save_disabled,
                type="primary",
            ):
                st.session_state["filter_list"].append({
                    "type":  "ai_code",
                    "label": label or "AI Filter",
                    "params": {
                        "prompt": prompt.strip(),
                        "code":   code,
                    },
                })
                # Clear state
                for k in ("ai_gen_label", "ai_gen_code", "ai_gen_valid"):
                    st.session_state.pop(k, None)

                st.success(f"✅ **{label}** added to the filter pipeline!")
                st.rerun()

        # ── Field reference expander ──────────────────────────────────────────
        with st.expander("📋 App field reference", expanded=False):
            st.code("""
# Boolean fields (True/False):
legally_created, full_time_founder, founder_in_tunisia,
gender_mixed, generating_revenue, raised_funding,
startup_label, participated_programs

# Range fields ("None"|"1–2"|"3–5"|"6–10"|"+10"):
total_employees, salaried_employees, num_clients

# Use BAND_ORDER to compare ranges:
BAND_ORDER = {"None":0, "1–2":1, "3–5":2, "6–10":3, "+10":4}
BAND_ORDER.get(app["total_employees"], 0) >= BAND_ORDER["3–5"]

# String fields:
age       → "Less than 2 years" | "2–5 years" | "5–7 years" | "More than 7 years"
maturity  → "Idea" | "POC finalized" | "Functional MVP" |
            "MVP currently being tested" | "Go To Market (Early sales)" |
            "Product/Service on the market" | "International Expansion"
sector    → "AI/Data" | "FinTech" | "HealthTech" | "GreenTech" | ...
governorate → "Tunis" | "Sfax" | "Sousse" | ...
""", language="python")