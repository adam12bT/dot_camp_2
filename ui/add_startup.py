"""
ui/add_startup.py – "Add new startup(s)" section with tabs:
  1. Manual entry
  2. Typeform CSV  (the real export — English or French)
  3. Google Form CSV (legacy)
  4. Typeform JSON
  5. AI Generate
  6. AI Filter Builder
"""

import pandas as pd
import streamlit as st

from engine import evaluate, MATURITY_OPTIONS, AGE_OPTIONS, EMPLOYEE_RANGES, CLIENT_RANGES
from utils import SECTORS, GOVERNORATES, DECISION_COLORS
from ui.styles import decision_banner, color_decision


def _existing_names() -> set[str]:
    return {a["startup_name"].lower().strip() for a in st.session_state.get("startups", [])}


def _style_decision(df):
    """Apply color_decision to the Decision column — compatible with pandas 2.1+."""
    styler = df.style
    if hasattr(styler, "map"):
        return styler.map(color_decision, subset=["Decision"])
    return styler.applymap(color_decision, subset=["Decision"])


def _add_and_show(unique: list, active_config: dict, key_suffix: str) -> None:
    """Evaluate, add to session state, show dataframe preview."""
    if not unique:
        return
    if not st.button("✅ Evaluate & Add all", key=f"btn_{key_suffix}", type="primary"):
        return
    rows = []
    for a in unique:
        r = evaluate(a, config=active_config)
        st.session_state["startups"].append(a)
        row = {"Startup": r.startup_name, "Decision": r.final_decision, "Bonus": r.bonus_score}
        for lbl, res in r.filter_results:
            row[lbl] = res
        rows.append(row)
    df = pd.DataFrame(rows)
    st.dataframe(_style_decision(df), use_container_width=True, height=300)
    st.success(f"✅ {len(unique)} startup(s) added.")
    st.rerun()


# ── Tab 1 – Manual entry ──────────────────────────────────────────────────────

def _render_manual_tab(active_config: dict) -> None:
    with st.form("add_startup_form"):
        st.markdown("#### 🏢 Startup Info")
        c1, c2, c3 = st.columns(3)
        with c1:
            name         = st.text_input("Startup name *")
            age          = st.selectbox("Age of startup *", AGE_OPTIONS)
            founded_year = st.text_input("Year founded (e.g. 2023)")
        with c2:
            governorate = st.selectbox("Governorate", GOVERNORATES)
            sector      = st.selectbox("Sector", SECTORS)
        with c3:
            website  = st.text_input("Website")
            linkedin = st.text_input("LinkedIn")

        st.markdown("#### ✅ Eligibility")
        e1, e2, e3, e4 = st.columns(4)
        with e1: legally  = st.checkbox("Legally established?")
        with e2: fulltime = st.checkbox("Full-time founder?")
        with e3: resident = st.checkbox("Founder in Tunisia?")
        with e4: mixed    = st.checkbox("Gender-mixed team?")

        st.markdown("#### 👥 Team")
        t1, t2 = st.columns(2)
        with t1: employees = st.selectbox("Total employees", EMPLOYEE_RANGES)
        with t2: salaried  = st.selectbox("Salaried employees", EMPLOYEE_RANGES[:-1])

        st.markdown("#### 💡 Solution")
        maturity = st.selectbox("Solution maturity *", MATURITY_OPTIONS)
        problem  = st.text_area("Problem you solve", height=60)
        solution = st.text_area("Solution you offer", height=60)

        st.markdown("#### 📈 Traction")
        tr1, tr2, tr3, tr4 = st.columns(4)
        with tr1: clients = st.selectbox("Clients / Users", CLIENT_RANGES)
        with tr2: revenue = st.checkbox("Generating revenue?")
        with tr3: funded  = st.checkbox("Raised funding?")
        with tr4: label   = st.checkbox("Startup label?")

        submitted = st.form_submit_button("🚀 Evaluate & Add", type="primary", use_container_width=True)

    if not submitted:
        return
    if not name:
        st.error("Startup name is required.")
        return
    if name.lower().strip() in _existing_names():
        st.warning(f"⚠️ **{name}** already exists.")
        return

    app = {
        "startup_name":          name,
        "age":                   age,
        "sector":                sector,
        "governorate":           governorate,
        "legally_created":       legally,
        "full_time_founder":     fulltime,
        "founder_in_tunisia":    resident,
        "total_employees":       employees,
        "salaried_employees":    salaried,
        "gender_mixed":          mixed,
        "maturity":              maturity,
        "num_clients":           clients,
        "generating_revenue":    revenue,
        "raised_funding":        funded,
        "startup_label":         label,
        "participated_programs": False,
        "founded_year":          founded_year,
        "website":               website,
        "linkedin":              linkedin,
        "problem":               problem,
        "solution":              solution,
    }
    result = evaluate(app, config=active_config)
    st.session_state["startups"].append(app)

    st.markdown(decision_banner(result.final_decision, result.emoji), unsafe_allow_html=True)
    st.markdown("**Filter results:**")
    for flabel, fresult in result.filter_results:
        st.markdown(f"- {flabel}: `{fresult}`")
    if result.rejection_reason:
        st.error(f"Rejection: {result.rejection_reason}")
    if result.bonus_details:
        st.markdown("**Bonus:** " + " · ".join(result.bonus_details))
    st.success(f"✅ **{name}** added. Total startups: {len(st.session_state['startups'])}")


# ── Tab 2 – Typeform CSV (real export) ────────────────────────────────────────

def _render_typeform_csv_tab(active_config: dict) -> None:
    from mock_data import typeform_csv_to_apps

    st.info(
        "Upload the **CSV exported directly from Typeform** — works for both "
        "English and French responses. Go to *Results → Export → Download as CSV*."
    )
    uploaded = st.file_uploader("Upload Typeform CSV", type=["csv"], key="tf_csv")
    if not uploaded:
        return

    try:
        text     = uploaded.read().decode("utf-8-sig")
        new_apps = typeform_csv_to_apps(text)
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return

    existing = _existing_names()
    unique   = [a for a in new_apps if a["startup_name"].lower().strip() not in existing]
    st.info(f"Found **{len(new_apps)}** application(s) · **{len(unique)}** new")

    if unique:
        with st.expander("Preview first 5 parsed apps"):
            for a in unique[:5]:
                st.markdown(
                    f"**{a['startup_name']}** · {a.get('age','')} · "
                    f"{a.get('sector','')} · maturity: {a.get('maturity','')} · "
                    f"revenue: {a.get('generating_revenue','')} · "
                    f"founder FT: {a.get('full_time_founder','')}"
                )

    _add_and_show(unique, active_config, "tf_csv")


# ── Tab 3 – Google Form CSV (legacy) ─────────────────────────────────────────

def _render_gform_csv_tab(active_config: dict) -> None:
    from mock_data import gform_csv_to_apps

    st.info("Upload a CSV exported from **Google Form** (legacy format).")
    uploaded = st.file_uploader("Upload Google Form CSV", type=["csv"], key="gf_csv")
    if not uploaded:
        return

    try:
        text     = uploaded.read().decode("utf-8-sig")
        new_apps = gform_csv_to_apps(text)
    except Exception as e:
        st.error(f"Failed to parse CSV: {e}")
        return

    existing = _existing_names()
    unique   = [a for a in new_apps if a["startup_name"].lower().strip() not in existing]
    st.info(f"Found **{len(new_apps)}** application(s) · **{len(unique)}** new")
    _add_and_show(unique, active_config, "gf_csv")


# ── Tab 4 – Typeform JSON ─────────────────────────────────────────────────────

def _render_json_tab(active_config: dict) -> None:
    from mock_data import typeform_json_to_apps

    st.info("Upload a JSON exported from **Typeform**.")
    uploaded = st.file_uploader("Upload JSON", type=["json"], key="tf_json")
    if not uploaded:
        return

    try:
        new_apps = typeform_json_to_apps(uploaded.read().decode("utf-8"))
    except Exception as e:
        st.error(f"Failed to parse JSON: {e}")
        return

    existing = _existing_names()
    unique   = [a for a in new_apps if a["startup_name"].lower().strip() not in existing]
    st.info(f"Found **{len(new_apps)}** application(s) · **{len(unique)}** new")
    _add_and_show(unique, active_config, "tf_json")


# ── Tab 5 – AI Startup Generator ──────────────────────────────────────────────

def _render_ai_tab(active_config: dict) -> None:
    import os, json, requests as _req

    st.markdown("#### 🤖 AI Startup Generator")
    st.caption(
        "Describe one or more startups in plain English — "
        "the AI will create realistic application records and evaluate them instantly."
    )

    _SYSTEM_PROMPT = """\
You are a startup data generator for a selection pipeline demo.
Given a plain-English description, generate a list of startup application dicts.

Each dict MUST contain exactly these keys:
  startup_name, age, sector, governorate, maturity,
  legally_created, full_time_founder, founder_in_tunisia,
  total_employees, salaried_employees, gender_mixed,
  num_clients, generating_revenue, raised_funding,
  startup_label, participated_programs

Rules:
- age: one of "Less than 2 years" | "2-5 years" | "5-7 years" | "More than 7 years"
- maturity: one of "Idea"|"POC finalized"|"Functional MVP"|"MVP currently being tested"|"Go To Market (Early sales)"|"Product/Service on the market"|"International Expansion"
- total_employees / salaried_employees / num_clients: one of "None"|"1-2"|"3-5"|"6-10"|"+10"
- legally_created, full_time_founder, founder_in_tunisia, gender_mixed,
  generating_revenue, raised_funding, startup_label, participated_programs: boolean
- sector: e.g. "AI/Data","FinTech","HealthTech","GreenTech","EdTech","SaaS","DeepTech"
- governorate: Tunisian governorate e.g. "Tunis","Sfax","Sousse","Nabeul"

OUTPUT: respond with ONLY a valid JSON array, no markdown, no explanation.
[{"startup_name": "...", ...}, ...]
"""

    prompt = st.text_area(
        "Describe the startup(s) you want to generate",
        placeholder=(
            "e.g. 3 early-stage AI startups from Tunis with at least 3 employees\n"
            "or: a funded FinTech startup that is generating revenue"
        ),
        height=100,
        key="ai_gen_startup_prompt",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        n_startups = st.number_input("How many?", min_value=1, max_value=20, value=3, key="ai_gen_n")

    if not st.button("🚀 Generate & Evaluate", type="primary",
                     use_container_width=True, key="btn_ai_gen_startup"):
        return

    if not prompt.strip():
        st.warning("Please describe the startup(s) first.")
        return

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        st.error("❌ GROQ_API_KEY not set in your .env file.")
        return

    full_prompt = f"{prompt.strip()}\n\nGenerate exactly {n_startups} startup(s)."

    with st.spinner("AI is generating startups…"):
        try:
            resp = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {groq_key}"},
                data=json.dumps({
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user",   "content": full_prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7,
                }).encode(),
                timeout=30,
            )
            resp.raise_for_status()
            text = (resp.json().get("choices", [{}])[0]
                               .get("message", {})
                               .get("content", "").strip())

            if text.startswith("```"):
                text = "\n".join(
                    line for line in text.splitlines()
                    if not line.strip().startswith("```")
                ).strip()

            apps = json.loads(text)
            if not isinstance(apps, list):
                apps = [apps]

        except json.JSONDecodeError as e:
            st.error(f"AI returned invalid JSON: {e}\n\nRaw: {text[:400]}")
            return
        except Exception as e:
            st.error(f"Generation failed: {e}")
            return

    existing = {a["startup_name"].lower().strip()
                for a in st.session_state.get("startups", [])}
    unique = [a for a in apps if a.get("startup_name", "").lower().strip() not in existing]
    dupes  = len(apps) - len(unique)

    st.success(f"✅ Generated **{len(apps)}** startup(s)"
               + (f" · {dupes} skipped (duplicate name)" if dupes else ""))

    from engine import evaluate
    from utils import DECISION_COLORS

    rows = []
    for a in unique:
        r = evaluate(a, config=active_config)
        rows.append({
            "Startup":  a.get("startup_name", ""),
            "Age":      a.get("age", ""),
            "Sector":   a.get("sector", ""),
            "Maturity": a.get("maturity", ""),
            "Decision": r.final_decision,
            "Bonus":    r.bonus_score,
            "Reason":   r.rejection_reason or ", ".join(r.bonus_details),
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            _style_decision(df),
            use_container_width=True,
            height=min(80 + len(rows) * 38, 400),
        )

        if st.button("💾 Add all to pipeline", type="primary",
                     key="btn_ai_gen_add", use_container_width=True):
            for a in unique:
                st.session_state["startups"].append(a)
            st.success(f"Added {len(unique)} startup(s) to the pipeline.")
            st.rerun()
    else:
        st.info("All generated startups already exist in the pipeline.")


# ── Tab 6 – AI Filter Builder ─────────────────────────────────────────────────

def _render_ai_filter_builder_tab() -> None:
    from ui.ai_filter_builder import render_ai_code_builder
    render_ai_code_builder()


# ── Public entry-point ────────────────────────────────────────────────────────

def render_add_startup(active_config: dict) -> None:
    st.markdown("### ➕ Add new startup(s)")
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "✏️ Manual Entry",
        "📄 Typeform CSV",
        "📋 Google Form CSV",
        "🗂 Typeform JSON",
        "🤖 AI Generate",
        "⚙️ AI Filter Builder",
    ])
    with tab1: _render_manual_tab(active_config)
    with tab2: _render_typeform_csv_tab(active_config)
    with tab3: _render_gform_csv_tab(active_config)
    with tab4: _render_json_tab(active_config)
    with tab5: _render_ai_tab(active_config)
    with tab6: _render_ai_filter_builder_tab()