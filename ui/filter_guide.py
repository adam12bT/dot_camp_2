"""
ui/filter_guide.py – "Filter Guide" tab: static, illustrated explanation of
every filter type available in the Filter Pipeline (sidebar).

Usage:
    from ui.filter_guide import render_filter_guide
    render_filter_guide()
"""

import streamlit as st


# ── Static content for each filter type ──────────────────────────────────────
# Each entry: title, emoji/icon, short description, "how it works" steps,
# example config, and a small visual (mermaid diagram or sample table).

_FILTER_DOCS = [
    {
        "type": "age_reject",
        "icon": "📅",
        "title": "Age Reject",
        "summary": "Rejects applications based on the startup's **age group**.",
        "how": [
            "You pick one or more age groups (e.g. *More than 7 years*).",
            "If the startup's age falls in a selected group, it is **rejected immediately**.",
            "Useful for programs targeting only early-stage startups.",
        ],
        "example": {
            "reject_groups": ["<2", ">7"],
        },
        "diagram": """
graph LR
    A[Startup age] --> B{In reject_groups?}
    B -- Yes --> C[❌ Rejected]
    B -- No --> D[✅ Continue to next filter]
""",
    },
    {
        "type": "legal_check",
        "icon": "⚖️",
        "title": "Legal Check",
        "summary": "Requires startups in certain age groups to be **legally established**.",
        "how": [
            "You select which age groups must have `legally_created = True`.",
            "If the startup belongs to one of those groups but isn't legally registered, it's rejected.",
            "Younger startups (e.g. *Less than 2 years*) can often be exempted.",
        ],
        "example": {
            "required_for": ["2-5", ">7"],
        },
        "diagram": """
graph LR
    A[Startup age group] --> B{In required_for?}
    B -- No --> D[✅ Pass]
    B -- Yes --> C{legally_created?}
    C -- True --> D
    C -- False --> E[❌ Rejected]
""",
    },
    {
        "type": "boolean_field",
        "icon": "✅",
        "title": "Boolean Field",
        "summary": "Checks a single **true/false field** on the application.",
        "how": [
            "Pick the application field key (e.g. `full_time_founder`).",
            "If the field is `False`, the startup is rejected with your custom message.",
            "Simple, single-condition gatekeeping.",
        ],
        "example": {
            "field": "full_time_founder",
            "label": "Full-time founder",
            "message": "Founder must be working full-time on the startup.",
        },
        "diagram": """
graph LR
    A["app[field]"] --> B{True?}
    B -- Yes --> C[✅ Pass]
    B -- No --> D["❌ Rejected — message"]
""",
    },
    {
        "type": "multi_boolean",
        "icon": "🧩",
        "title": "Multi Boolean",
        "summary": "Checks **several true/false fields** at once, with ALL or ANY logic.",
        "how": [
            "List multiple field keys and matching display labels.",
            "Choose `all` (every field must be True) or `any` (at least one must be True).",
            "Great for combined eligibility checks (e.g. legal + resident + full-time).",
        ],
        "example": {
            "fields": ["legally_created", "founder_in_tunisia", "full_time_founder"],
            "labels": ["Legally created", "Founder in Tunisia", "Full-time founder"],
            "mode": "all",
            "message": "All eligibility conditions must be met.",
        },
        "diagram": """
graph TD
    A[Field 1] --> M{Mode}
    B[Field 2] --> M
    C[Field 3] --> M
    M -- all: every field True --> P1[✅ Pass]
    M -- any: at least one True --> P2[✅ Pass]
    M -- otherwise --> R[❌ Rejected]
""",
    },
    {
        "type": "maturity_outcome",
        "icon": "📊",
        "title": "Maturity Outcome",
        "summary": "Maps **(age group, maturity level)** combinations to a final outcome.",
        "how": [
            "For each age group, choose the outcome (Rejected / Shortlisted / Selected) per maturity level.",
            "This filter directly determines the final decision — it doesn't just reject.",
            "Use it to encode a full maturity matrix per program stage.",
        ],
        "example": {
            "outcomes": {
                "(<2, Idea)": "Shortlisted",
                "(<2, Functional MVP)": "Selected",
                "(2-5, Idea)": "Rejected",
            }
        },
        "diagram": """
graph TD
    A[Age group] --> M[Maturity outcome matrix]
    B[Maturity level] --> M
    M --> R1[Rejected]
    M --> R2[Shortlisted]
    M --> R3[Selected]
""",
    },
    {
        "type": "field_in",
        "icon": "📋",
        "title": "Field In (Allow-list)",
        "summary": "Only allows applications whose field value is in an **allowed list**.",
        "how": [
            "Pick a field key (e.g. `sector`).",
            "List the allowed values, one per line (e.g. `FinTech`, `HealthTech`).",
            "Anything not in the list is rejected.",
        ],
        "example": {
            "field": "sector",
            "allowed": ["FinTech", "HealthTech", "AI/Data"],
            "message": "Sector not eligible for this program.",
        },
        "diagram": """
graph LR
    A["app[field]"] --> B{Value in allowed list?}
    B -- Yes --> C[✅ Pass]
    B -- No --> D[❌ Rejected]
""",
    },
    {
        "type": "field_not_in",
        "icon": "🚫",
        "title": "Field Not In (Block-list)",
        "summary": "Rejects applications whose field value is in a **blocked list**.",
        "how": [
            "Pick a field key (e.g. `governorate`).",
            "List blocked values, one per line.",
            "Anything matching a blocked value is rejected; everything else passes.",
        ],
        "example": {
            "field": "governorate",
            "blocked": ["Tunis"],
            "message": "This program targets startups outside Tunis.",
        },
        "diagram": """
graph LR
    A["app[field]"] --> B{Value in blocked list?}
    B -- Yes --> C[❌ Rejected]
    B -- No --> D[✅ Pass]
""",
    },
    {
        "type": "min_employees",
        "icon": "👥",
        "title": "Minimum Employees",
        "summary": "Requires the startup to meet a **minimum employee band**.",
        "how": [
            "Pick the field (usually `total_employees` or `salaried_employees`).",
            "Choose the minimum band: None < 1–2 < 3–5 < 6–10 < +10.",
            "Startups below the chosen band are rejected.",
        ],
        "example": {
            "field": "total_employees",
            "min_band": "3-5",
            "message": "At least 3-5 employees required.",
        },
        "diagram": """
graph LR
    A["app[field] band"] --> B{Band >= min_band?}
    B -- Yes --> C[✅ Pass]
    B -- No --> D[❌ Rejected]
""",
    },
    {
        "type": "ai_code",
        "icon": "🤖",
        "title": "AI Code Filter",
        "summary": "A **custom Python function**, generated by AI from a plain-English prompt.",
        "how": [
            "Describe the rule you want in plain English (in the AI Filter Builder tab).",
            "The AI generates a Python function that returns a pass/fail (and optional message).",
            "You can review, edit, and re-validate the generated code before using it.",
        ],
        "example": {
            "prompt": "Reject startups with no revenue and fewer than 3 clients",
            "code": "def filter_fn(app):\\n    if not app['generating_revenue'] and app['num_clients'] in ['None', '1-2']:\\n        return False, 'No revenue and low traction'\\n    return True, ''",
        },
        "diagram": """
graph LR
    A[Plain-English prompt] --> B[AI generates Python function]
    B --> C[Validate code]
    C -- Valid --> D["app → filter_fn(app) → pass/fail"]
    C -- Invalid --> E[Edit & re-validate]
""",
    },
]


def _render_diagram(mermaid_code: str, key: str) -> None:
    """Render a mermaid diagram via mermaid.js inside an HTML component."""
    html = f"""
    <div class="mermaid">
{mermaid_code}
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.0/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: "neutral" }});
    </script>
    """
    st.components.v1.html(html, height=220, scrolling=True)


def _render_filter_card(doc: dict, idx: int) -> None:
    with st.container(border=True):
        st.markdown(f"### {doc['icon']} {doc['title']}")
        st.markdown(f"`{doc['type']}`")
        st.markdown(doc["summary"])

        st.markdown("**How it works:**")
        for step in doc["how"]:
            st.markdown(f"- {step}")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Example config**")
            st.json(doc["example"], expanded=False)

        with col2:
            st.markdown("**Visual flow**")
            _render_diagram(doc["diagram"], key=f"diagram_{idx}")


# ── Public entry-point ────────────────────────────────────────────────────────

def render_filter_guide() -> None:
    """Static, illustrated reference for every filter type in the pipeline."""
    st.markdown("### 📖 Filter Guide")
    st.caption(
        "A reference for every filter type available in the **Filter Pipeline** "
        "(sidebar). Each card shows what it does, how it behaves, an example "
        "config, and a visual flow diagram."
    )
    st.divider()

    # Optional quick-jump
    type_to_title = {d["type"]: f"{d['icon']} {d['title']}" for d in _FILTER_DOCS}
    jump = st.selectbox(
        "Jump to a filter type",
        options=["— Show all —"] + list(type_to_title.values()),
        key="filter_guide_jump",
    )

    if jump == "— Show all —":
        for idx, doc in enumerate(_FILTER_DOCS):
            _render_filter_card(doc, idx)
            st.write("")
    else:
        target_type = next(t for t, title in type_to_title.items() if title == jump)
        idx = next(i for i, d in enumerate(_FILTER_DOCS) if d["type"] == target_type)
        _render_filter_card(_FILTER_DOCS[idx], idx)
