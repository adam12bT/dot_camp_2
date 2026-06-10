"""
ai_code_filter.py – Natural language → executable filter function pipeline.
"""

import os, re, json, traceback, requests


APP_FIELDS = """
  age          str  "Less than 2 years"|"2-5 years"|"5-7 years"|"More than 7 years"
  sector       str  "AI/Data"|"FinTech"|"HealthTech"|"GreenTech"|"EdTech"| ...
  governorate  str  "Tunis"|"Sfax"|"Sousse"| ...
  maturity     str  "Idea"|"POC finalized"|"Functional MVP"|"MVP currently being tested"|
                    "Go To Market (Early sales)"|"Product/Service on the market"|"International Expansion"
  legally_created, full_time_founder, founder_in_tunisia, gender_mixed,
  generating_revenue, raised_funding, startup_label, participated_programs  -> bool
  total_employees, salaried_employees, num_clients  -> str "None"|"1-2"|"3-5"|"6-10"|"+10"

BAND_ORDER dict is pre-defined: {"None":0,"1-2":1,"3-5":2,"6-10":3,"+10":4}
Use: BAND_ORDER.get(app.get("total_employees","None"),0) >= BAND_ORDER["3-5"]
"""

_SYSTEM_PROMPT = f"""You are a Python function generator for a startup filter pipeline.

Write a function that takes a startup dict and returns (True, reason) or (False, rejection).

FIELD REFERENCE:
{APP_FIELDS}

STRICT RULES:
- Function signature: def run(app):
- Return type: tuple of (bool, str)  
- Use ONLY ASCII characters — no unicode dashes, no smart quotes
- Use plain hyphens in band keys: "1-2" "3-5" "6-10" "+10"
- NO import statements
- NO semicolons — use newlines and proper indentation
- BAND_ORDER is available as a pre-defined variable

OUTPUT: one line of JSON only, no markdown:
{{"label":"<max 40 chars>","code":"<function with \\n for newlines and 4 spaces indent>"}}

EXAMPLE:
{{"label":"Min 3 employees","code":"def run(app):\\n    emp = BAND_ORDER.get(app.get(\\"total_employees\\",\\"None\\"),0)\\n    if emp < BAND_ORDER[\\"3-5\\"]:\\n        return (False,\\"Less than 3 employees\\")\\n    return (True,\\"OK\\")"}}

If unmappable: {{"error":"reason"}}
"""


def _normalize_code(code: str) -> str:
    """Turn LLM output into valid executable Python."""
    # Real newlines from escaped sequences
    code = code.replace("\\n", "\n")
    # ASCII dashes in band keys
    for bad, good in [("\u20132","-2"),("\u20135","-5"),("\u201310","-10"),("\u2013","-"),("\u2014","-")]:
        code = code.replace(bad, good)
    # ASCII quotes
    for bad, good in [("\u201c",'"'),("\u201d",'"'),("\u2018","'"),("\u2019","'")]:
        code = code.replace(bad, good)
    return code


def _call_groq(messages: list, groq_key: str) -> str:
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Content-Type":"application/json","Authorization":f"Bearer {groq_key}"},
        data=json.dumps({"model":"llama-3.3-70b-versatile","messages":messages,
                         "max_tokens":800,"temperature":0}).encode(),
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json().get("choices",[{}])[0].get("message",{}).get("content","").strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.splitlines() if not l.strip().startswith("```")).strip()
    return text


def generate_filter_code(prompt: str) -> dict:
    """Call Groq, normalize output, auto-retry on syntax error."""
    groq_key = os.environ.get("GROQ_API_KEY","")
    if not groq_key:
        raise ValueError("GROQ_API_KEY not set.")

    msgs = [{"role":"system","content":_SYSTEM_PROMPT},
            {"role":"user","content":prompt.strip()}]
    text = _call_groq(msgs, groq_key)

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON: {e}\nRaw: {text[:300]}")

    if "error" in result:
        raise ValueError(f"LLM could not generate filter: {result['error']}")
    if "code" not in result or "label" not in result:
        raise ValueError(f"Missing 'code' or 'label' in: {result}")

    code = _normalize_code(result["code"])

    # Auto-fix pass if validation fails
    ok, err = validate_code(code)
    if not ok:
        fix_msg = (
            f"This Python function has a syntax error:\n\n{code}\n\n"
            f"Error:\n{err[:400]}\n\n"
            "Fix it. Return ONLY the corrected JSON, no explanation."
        )
        fix_text = _call_groq(msgs + [
            {"role":"assistant","content":text},
            {"role":"user","content":fix_msg},
        ], groq_key)
        try:
            fix_result = json.loads(fix_text)
            code = _normalize_code(fix_result.get("code", code))
            result["label"] = fix_result.get("label", result["label"])
        except Exception:
            pass  # keep original — UI will show the validation error

    result["code"] = code
    return result


# ── Sandbox ───────────────────────────────────────────────────────────────────

_BAND_ORDER = {"None":0,"1-2":1,"3-5":2,"6-10":3,"+10":4}

_SAFE_GLOBALS = {
    "__builtins__": {
        "str":str,"int":int,"float":float,"bool":bool,
        "len":len,"any":any,"all":all,"isinstance":isinstance,
        "True":True,"False":False,"None":None,
        "dict":dict,"list":list,"tuple":tuple,
        "min":min,"max":max,"abs":abs,"print":print,
    },
    "BAND_ORDER": _BAND_ORDER,
}


def validate_code(code: str) -> tuple:
    code = _normalize_code(code)
    dummy = {
        "startup_name":"TestCo","age":"2-5 years","sector":"AI/Data",
        "governorate":"Tunis","maturity":"Functional MVP",
        "legally_created":True,"full_time_founder":True,
        "founder_in_tunisia":True,"gender_mixed":False,
        "generating_revenue":False,"raised_funding":False,
        "startup_label":False,"participated_programs":False,
        "total_employees":"3-5","salaried_employees":"1-2",
        "num_clients":"1-2","founded_year":"2022",
        "website":"","linkedin":"","problem":"","solution":"",
    }
    try:
        ns = {}
        exec(compile(code,"<ai_filter>","exec"), dict(_SAFE_GLOBALS), ns)
        if "run" not in ns:
            return False, "No 'run' function defined."
        r = ns["run"](dummy)
        if not isinstance(r, tuple) or len(r) != 2:
            return False, f"run() must return (bool, str), got {r!r}"
        if not isinstance(r[0], bool):
            return False, f"First element must be bool, got {type(r[0])}"
        if not isinstance(r[1], str):
            return False, f"Second element must be str, got {type(r[1])}"
        return True, ""
    except Exception:
        return False, traceback.format_exc()


def run_ai_filter(code: str, app: dict) -> tuple:
    code = _normalize_code(code)
    # Normalize Windows line endings
    code = code.replace("\r\n", "\n").replace("\r", "\n")
    if not code.strip():
        raise RuntimeError("Empty code after normalization")
    ns = {}
    try:
        compiled = compile(code, "<ai_filter>", "exec")
        exec(compiled, dict(_SAFE_GLOBALS), ns)
        if "run" not in ns:
            raise RuntimeError("No 'run' function defined in AI filter code")
        result = ns["run"](app)
        if not isinstance(result, tuple) or len(result) != 2:
            raise RuntimeError(f"run() must return (bool, str), got {result!r}")
        return bool(result[0]), str(result[1])
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"AI filter execution error: {type(e).__name__}: {e}")


def engine_runner(app, params, age_grp, maturity):
    from engine import _Reject
    code = params.get("code", "")
    if not code:
        return None, "⚠️ No code stored for this AI filter"
    try:
        passed, msg = run_ai_filter(code, app)
        if not passed:
            raise _Reject(msg)
        msg_lower = msg.strip().lower()
        if "selected" in msg_lower:
            decision = "Selected"
        elif "shortlisted" in msg_lower:
            decision = "Shortlisted"
        else:
            decision = None
        return decision, f"✅ {msg}"
    except _Reject:
        raise
    except Exception as e:
        return None, f"⚠️ AI filter skipped ({type(e).__name__}: {e})"