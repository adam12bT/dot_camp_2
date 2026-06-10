"""
engine.py – Dot Camp Selection Engine (Dynamic Filter Pipeline)

evaluate(app, config) runs each filter in config["filters"] in order.
To add a new filter type: write _run_yourtype(), add it to FILTER_RUNNERS.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ── Option lists (used by UI dropdowns) ───────────────────────────────────────
MATURITY_OPTIONS = [
    "Idea",
    "POC finalized",
    "Functional MVP",
    "MVP currently being tested",
    "Go To Market (Early sales)",
    "Product/Service on the market",
    "International Expansion",
]

AGE_OPTIONS = [
    "Less than 2 years",
    "2–5 years",
    "5–7 years",
    "More than 7 years",
]

EMPLOYEE_RANGES = ["None", "1–2", "3–5", "6–10", "+10"]
CLIENT_RANGES   = ["None", "1–2", "3–5", "6–10", "+10"]

# ── Internal lookups ──────────────────────────────────────────────────────────
_BAND_ORDER = {
    "None": 0,
    "1–2": 1, "1-2": 1,
    "3–5": 2, "3-5": 2,
    "6–10": 3, "6-10": 3,
    "+10": 4,
}

_AGE_GROUP = {
    "Less than 2 years":  "<2",
    "Less than  2 years": "<2",
    "Moins de 2 ans":     "<2",
    "2–5 years": "2-5", "2-5 years": "2-5",
    "2–5 ans":   "2-5", "2-5 ans":   "2-5",
    "5–7 years": "5-7", "5-7 years": "5-7",
    "5–7 ans":   "5-7", "5-7 ans":   "5-7",
    "More than 7 years": ">7",
    "Plus de 7 ans":     ">7",
}

_MATURITY_NORM = {
    "Idée":                                          "Idea",
    "POC finalisé":                                  "POC finalized",
    "MVP fonctionnel":                               "Functional MVP",
    "MVP en cours de test":                          "MVP currently being tested",
    "Go To Market (Premières ventes)":               "Go To Market (Early sales)",
    "Produit / Service sur le marché":               "Product/Service on the market",
    "Produit / Service commercialisé":               "Product/Service on the market",
    "Produit / Service en expansion internationale": "International Expansion",
}
for _v in MATURITY_OPTIONS:
    _MATURITY_NORM[_v] = _v


# ── Result dataclass ──────────────────────────────────────────────────────────
@dataclass
class EvaluationResult:
    startup_name:     str
    final_decision:   str   # Selected ★ | Selected | Shortlisted ✓ | Shortlisted | Rejected
    emoji:            str
    bonus_score:      int
    bonus_details:    List[str]
    rejection_reason: Optional[str]
    filter_results:   List[Tuple[str, str]]  # [(label, result_string), ...]

    # Backward-compatible aliases so existing app.py code still works
    @property
    def filter1_result(self): return self.filter_results[0][1] if len(self.filter_results) > 0 else "—"
    @property
    def filter2_result(self): return self.filter_results[1][1] if len(self.filter_results) > 1 else "—"
    @property
    def filter3_result(self): return self.filter_results[2][1] if len(self.filter_results) > 2 else "—"
    @property
    def filter4_result(self): return self.filter_results[3][1] if len(self.filter_results) > 3 else "—"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _truthy(v) -> bool:
    if isinstance(v, bool):   return v
    if isinstance(v, (int, float)): return bool(v)
    return str(v).strip().lower() in {"yes", "oui", "true", "1", "1.0", "vrai"}

def _has_value(v) -> bool:
    s = str(v).strip().lower() if v is not None else ""
    return s not in {"none", "aucun", "0", "nan", "", "null"}


# ── Internal exception for early rejection ────────────────────────────────────
class _Reject(Exception):
    pass


# ── Filter runner functions ───────────────────────────────────────────────────
# Signature: (app, params, age_grp, maturity) → (base_decision_or_None, result_str)
# Raise _Reject(message) to reject the startup.

def _run_age_reject(app, params, age_grp, maturity):
    if age_grp in params.get("reject_groups", []):
        raise _Reject(f"Age group '{app.get('age', '')}' is not eligible for this camp")
    return None, f"✅ Pass (age: {app.get('age', '')})"


def _run_legal_check(app, params, age_grp, maturity):
    if age_grp in params.get("required_for", []):
        if not _truthy(app.get("legally_created", False)):
            raise _Reject("Startup must be legally established for this age group")
        return None, "✅ Pass (legally created)"
    return None, "➖ N/A (not required for this age group)"


def _run_boolean_field(app, params, age_grp, maturity):
    field_key = params.get("field", "")
    label     = params.get("label", field_key)
    message   = params.get("message", f"{label} requirement not met")
    if not _truthy(app.get(field_key, False)):
        raise _Reject(message)
    return None, f"✅ Pass ({label})"


def _run_multi_boolean(app, params, age_grp, maturity):
    fields  = params.get("fields", [])
    labels  = params.get("labels", fields)
    mode    = params.get("mode", "all")
    values  = [_truthy(app.get(f, False)) for f in fields]
    if mode == "all":
        failed = [labels[i] for i, v in enumerate(values) if not v]
        if failed:
            msg = params.get("message") or f"Required: {', '.join(failed)}"
            raise _Reject(msg)
    else:
        if not any(values):
            msg = params.get("message") or f"At least one required: {', '.join(labels)}"
            raise _Reject(msg)
    return None, "✅ Pass"


def _run_maturity_outcome(app, params, age_grp, maturity):
    outcomes = params.get("outcomes", {})
    decision = outcomes.get((age_grp, maturity), "Rejected")
    if decision == "Rejected":
        raise _Reject(
            f"Maturity '{maturity}' not eligible for age group "
            f"'{app.get('age', '')}' in this camp"
        )
    icon = "✅" if decision == "Selected" else "⚠️"
    return decision, f"{icon} {decision} ({maturity})"


def _run_field_in(app, params, age_grp, maturity):
    field_key = params.get("field", "")
    allowed   = set(params.get("allowed", []))
    message   = params.get("message", f"'{field_key}' value not in allowed list")
    value     = str(app.get(field_key, "")).strip()
    if value not in allowed:
        raise _Reject(f"{message} (got: '{value}')")
    return None, f"✅ Pass ({field_key}: {value})"


def _run_field_not_in(app, params, age_grp, maturity):
    field_key = params.get("field", "")
    blocked   = set(params.get("blocked", []))
    message   = params.get("message", f"'{field_key}' value is blocked")
    value     = str(app.get(field_key, "")).strip()
    if value in blocked:
        raise _Reject(f"{message} (got: '{value}')")
    return None, f"✅ Pass ({field_key}: {value})"


def _run_min_employees(app, params, age_grp, maturity):
    field_key = params.get("field", "total_employees")
    min_band  = params.get("min_band", "1–2")
    message   = params.get("message", f"Minimum team size not met ({min_band})")
    value     = str(app.get(field_key, "None")).strip()
    val_rank  = _BAND_ORDER.get(value.replace("–", "-"), _BAND_ORDER.get(value, 0))
    min_rank  = _BAND_ORDER.get(min_band.replace("–", "-"), _BAND_ORDER.get(min_band, 0))
    if val_rank < min_rank:
        raise _Reject(message)
    return None, f"✅ Pass (employees: {value})"


# ── Registry — add new filter types here ─────────────────────────────────────
FILTER_RUNNERS = {
    "age_reject":       _run_age_reject,
    "legal_check":      _run_legal_check,
    "boolean_field":    _run_boolean_field,
    "multi_boolean":    _run_multi_boolean,
    "maturity_outcome": _run_maturity_outcome,
    "field_in":         _run_field_in,
    "field_not_in":     _run_field_not_in,
    "min_employees":    _run_min_employees,
}


# ── Main evaluate ─────────────────────────────────────────────────────────────
def evaluate(app: dict, config: dict = None) -> EvaluationResult:
    if config is None:
        from camp_config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    name     = app.get("startup_name", "Unknown")
    age_raw  = str(app.get("age", "")).strip()
    age_grp  = _AGE_GROUP.get(age_raw, age_raw)
    mat_raw  = str(app.get("maturity", "")).strip()
    maturity = _MATURITY_NORM.get(mat_raw, mat_raw)

    results_so_far: List[Tuple[str, str]] = []
    base_decision: Optional[str] = None

    for f in config.get("filters", []):
        ftype  = f.get("type", "")
        label  = f.get("label", ftype)
        params = f.get("params", {})
        runner = FILTER_RUNNERS.get(ftype)

        if runner is None:
            results_so_far.append((label, f"⚠️ Unknown filter type '{ftype}'"))
            continue

        try:
            decision, result_str = runner(app, params, age_grp, maturity)
        except _Reject as e:
            results_so_far.append((label, f"❌ Rejected — {e}"))
            return EvaluationResult(
                startup_name=name,
                final_decision="Rejected",
                emoji="❌",
                bonus_score=0,
                bonus_details=[],
                rejection_reason=str(e),
                filter_results=results_so_far,
            )

        results_so_far.append((label, result_str))
        if decision in ("Selected", "Shortlisted"):
            base_decision = decision

    if base_decision is None:
        base_decision = "Shortlisted"

    # ── Bonus ─────────────────────────────────────────────────────────────────
    bonus       = 0
    bonus_items = []
    check_fns   = {"truthy": _truthy, "has_value": _has_value}

    for field_key, blabel, fn_name in config.get("bonus_fields", []):
        fn = check_fns.get(fn_name, _truthy)
        if fn(app.get(field_key)):
            bonus += 1
            bonus_items.append(blabel)

    star_thresh  = config.get("star_threshold", 3)
    check_thresh = config.get("checkmark_threshold", 2)

    if base_decision == "Selected":
        final = "Selected ★" if bonus >= star_thresh else "Selected"
        emoji = "⭐" if bonus >= star_thresh else "✅"
    else:
        final = "Shortlisted ✓" if bonus >= check_thresh else "Shortlisted"
        emoji = "🌟" if bonus >= check_thresh else "⚠️"

    return EvaluationResult(
        startup_name=name,
        final_decision=final,
        emoji=emoji,
        bonus_score=bonus,
        bonus_details=bonus_items,
        rejection_reason=None,
        filter_results=results_so_far,
    )

# ── AI code filter runner (registered at import time) ─────────────────────────
def _run_ai_code(app, params, age_grp, maturity):
    from ai_code_filter import engine_runner
    return engine_runner(app, params, age_grp, maturity)

FILTER_RUNNERS["ai_code"] = _run_ai_code
