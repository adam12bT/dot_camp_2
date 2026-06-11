"""
utils.py – Pure helpers, lookup maps, and shared constants.
No Streamlit imports here; this module is safe to import anywhere.
"""

from engine import MATURITY_OPTIONS, AGE_OPTIONS, EMPLOYEE_RANGES, CLIENT_RANGES  # re-export

# ── Age group display labels ──────────────────────────────────────────────────
AGE_LABEL_MAP: dict[str, str] = {
    "<2":  "Less than 2 years",
    "2-5": "2–5 years",
    "5-7": "5–7 years",
    ">7":  "More than 7 years",
}
ALL_AGE_GROUPS = ["<2", "2-5", "5-7", ">7"]

# ── Sector / Governorate picklists ────────────────────────────────────────────
SECTORS = [
    "AI/Data", "FinTech", "HealthTech", "EdTech", "GreenTech",
    "Agri/FoodTech", "HR Tech", "DeepTech", "SaaS", "TravelTech",
    "PropTech", "Industry 4.0", "ICC", "Transport Tech",
    "Industries créatives & culturelles (ICC)", "Other",
]
GOVERNORATES = [
    "Tunis", "Ariana", "Ben Arous", "Manouba", "Nabeul", "Bizerte",
    "Sousse", "Monastir", "Sfax", "Kairouan", "Mahdia", "Médenine",
    "Gafsa", "Jendouba", "Other",
]

# ── Decision colours ──────────────────────────────────────────────────────────
DECISION_COLORS: dict[str, str] = {
    "Selected":    "#00e5a0",
    "Shortlisted": "#f5c842",
    "Rejected":    "#ff4d6d",
}
OVERRIDE_OPTIONS = list(DECISION_COLORS.keys())

# ── Normalisation maps ────────────────────────────────────────────────────────
MATURITY_MAP: dict[str, str] = {
    'Idée': 'Idea',
    'POC finalisé': 'POC finalized',
    'MVP fonctionnel': 'Functional MVP',
    'MVP en cours de test': 'MVP currently being tested',
    'Go To Market (Premières ventes)': 'Go To Market (Early sales)',
    'Produit / Service sur le marché': 'Product/Service on the market',
    'Produit / Service commercialisé': 'Product/Service on the market',
    'Produit / Service en expansion internationale': 'International Expansion',
}
for _v in MATURITY_OPTIONS:
    MATURITY_MAP[_v] = _v

AGE_MAP: dict[str, str] = {
    'Moins de 2 ans': 'Less than 2 years',
    'Less than  2 years': 'Less than 2 years',
    '2-5 ans': '2–5 years', '2–5 ans': '2–5 years',
    '5-7 ans': '5–7 years', '5–7 ans': '5–7 years',
    'Plus de 7 ans': 'More than 7 years',
}
for _v in AGE_OPTIONS:
    AGE_MAP[_v] = _v

# ── Pure helpers ──────────────────────────────────────────────────────────────

def parse_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower() if v else ''
    return s in {'yes', 'oui', 'true', '1', 'vrai', '1.0'}


def parse_range(v) -> str:
    s = str(v).strip() if v else 'None'
    if s.lower() in {'aucun', 'none', '0', 'nan', '', 'null'}:
        return 'None'
    for k in ['1–2', '3–5', '6–10', '+10']:
        if k in s or k.replace('–', '-') in s:
            return k
    return 'None'


def bool_str(v) -> str:
    return "Yes" if v else "No"


def color_decision(val: str) -> str:
    """Pandas Styler-compatible cell formatter."""
    c = DECISION_COLORS.get(val, "")
    return f"background-color: {c}22; color: {c}; font-weight: bold;" if c else ""