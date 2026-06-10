"""
camp_config.py – Dot Camp Selection Rules

Filters are a plain list. The engine runs them in order.
Add / remove / reorder filters here — no changes needed in engine.py.

BUILT-IN FILTER TYPES
─────────────────────
age_reject        Reject age groups in reject_groups list
legal_check       Require legal status for given age groups
boolean_field     Reject if one boolean field is False
multi_boolean     Reject unless all/any of several boolean fields are True
maturity_outcome  Map (age_group, maturity) → Selected | Shortlisted | Rejected
field_in          Reject if field value not in allowed set
field_not_in      Reject if field value is in blocked set
min_employees     Reject if employee band below minimum
"""

AGE_LT2 = "<2"
AGE_2_5 = "2-5"
AGE_5_7 = "5-7"
AGE_GT7 = ">7"

IDEA      = "Idea"
POC       = "POC finalized"
MVP_FUNC  = "Functional MVP"
MVP_TEST  = "MVP currently being tested"
GTM       = "Go To Market (Early sales)"
ON_MARKET = "Product/Service on the market"
INTL      = "International Expansion"

SELECTED    = "Selected"
SHORTLISTED = "Shortlisted"
REJECTED    = "Rejected"

# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "name": "Dot Camp 5 (default)",
    "filters": [
        {
            "type":  "age_reject",
            "label": "F1 · Age",
            "params": {"reject_groups": [AGE_GT7]},
        },
        {
            "type":  "legal_check",
            "label": "F2 · Legal status",
            "params": {"required_for": [AGE_2_5]},
        },
        {
            "type":  "multi_boolean",
            "label": "F3 · Founder",
            "params": {
                "fields": ["full_time_founder", "founder_in_tunisia"],
                "labels": ["Full-time founder", "Founder in Tunisia"],
                "mode":   "all",
            },
        },
        {
            "type":  "maturity_outcome",
            "label": "F4 · Maturity",
            "params": {
                "outcomes": {
                    (AGE_LT2, POC):       SHORTLISTED,
                    (AGE_LT2, MVP_FUNC):  SHORTLISTED,
                    (AGE_LT2, MVP_TEST):  SHORTLISTED,
                    (AGE_LT2, GTM):       SHORTLISTED,
                    (AGE_LT2, ON_MARKET): SHORTLISTED,
                    (AGE_LT2, INTL):      SHORTLISTED,
                    (AGE_2_5, POC):       SHORTLISTED,
                    (AGE_2_5, MVP_FUNC):  SELECTED,
                    (AGE_2_5, MVP_TEST):  SELECTED,
                    (AGE_2_5, GTM):       SELECTED,
                    (AGE_2_5, ON_MARKET): SELECTED,
                    (AGE_2_5, INTL):      SELECTED,
                    (AGE_5_7, POC):       SHORTLISTED,
                    (AGE_5_7, MVP_FUNC):  SHORTLISTED,
                    (AGE_5_7, MVP_TEST):  SHORTLISTED,
                    (AGE_5_7, GTM):       SHORTLISTED,
                    (AGE_5_7, ON_MARKET): SHORTLISTED,
                    (AGE_5_7, INTL):      SHORTLISTED,
                },
            },
        },
    ],
    "bonus_fields": [
        ("total_employees",       "Has employees",       "has_value"),
        ("salaried_employees",    "Has salaried staff",  "has_value"),
        ("gender_mixed",          "Gender-mixed team",   "truthy"),
        ("num_clients",           "Has clients",         "has_value"),
        ("generating_revenue",    "Generating revenue",  "truthy"),
        ("startup_label",         "Startup Act label",   "truthy"),
        ("raised_funding",        "Raised funding",      "truthy"),
        ("participated_programs", "In programs",         "truthy"),
    ],
    "star_threshold":      3,
    "checkmark_threshold": 2,
}

# ─────────────────────────────────────────────────────────────────────────────
CAMP_6_CONFIG = {
    "name": "Dot Camp 6 (sector-focused)",
    "filters": [
        {
            "type":  "field_in",
            "label": "F1 · Sector",
            "params": {
                "field":   "sector",
                "allowed": ["AI/Data","HealthTech","GreenTech","Agri/FoodTech","DeepTech","Industry 4.0"],
                "message": "Sector not in scope for Camp 6",
            },
        },
        {
            "type":  "legal_check",
            "label": "F2 · Legal status",
            "params": {"required_for": [AGE_LT2, AGE_2_5, AGE_5_7, AGE_GT7]},
        },
        {
            "type":  "boolean_field",
            "label": "F3 · Full-time founder",
            "params": {
                "field":   "full_time_founder",
                "label":   "Full-time founder",
                "message": "No full-time founder on the team",
            },
        },
        {
            "type":  "min_employees",
            "label": "F4 · Team size",
            "params": {
                "field":    "total_employees",
                "min_band": "3–5",
                "message":  "Team too small (minimum 3 employees required)",
            },
        },
        {
            "type":  "maturity_outcome",
            "label": "F5 · Maturity",
            "params": {
                "outcomes": {
                    (AGE_LT2, POC):       SHORTLISTED,
                    (AGE_LT2, MVP_FUNC):  SELECTED,
                    (AGE_LT2, MVP_TEST):  SELECTED,
                    (AGE_LT2, GTM):       SELECTED,
                    (AGE_LT2, ON_MARKET): SELECTED,
                    (AGE_LT2, INTL):      SELECTED,
                    (AGE_2_5, POC):       SHORTLISTED,
                    (AGE_2_5, MVP_FUNC):  SELECTED,
                    (AGE_2_5, MVP_TEST):  SELECTED,
                    (AGE_2_5, GTM):       SELECTED,
                    (AGE_2_5, ON_MARKET): SELECTED,
                    (AGE_2_5, INTL):      SELECTED,
                    (AGE_5_7, POC):       SHORTLISTED,
                    (AGE_5_7, MVP_FUNC):  SELECTED,
                    (AGE_5_7, MVP_TEST):  SELECTED,
                    (AGE_5_7, GTM):       SELECTED,
                    (AGE_5_7, ON_MARKET): SELECTED,
                    (AGE_5_7, INTL):      SELECTED,
                    (AGE_GT7, ON_MARKET): SHORTLISTED,
                    (AGE_GT7, INTL):      SHORTLISTED,
                },
            },
        },
    ],
    "bonus_fields": [
        ("total_employees",    "Has employees",      "has_value"),
        ("gender_mixed",       "Gender-mixed team",  "truthy"),
        ("num_clients",        "Has clients",        "has_value"),
        ("generating_revenue", "Generating revenue", "truthy"),
        ("raised_funding",     "Raised funding",     "truthy"),
    ],
    "star_threshold":      2,
    "checkmark_threshold": 2,
}

# ─────────────────────────────────────────────────────────────────────────────
ACCELERATOR_CONFIG = {
    "name": "Accelerator track (strict)",
    "filters": [
        {
            "type":  "age_reject",
            "label": "F1 · Age",
            "params": {"reject_groups": [AGE_LT2, AGE_GT7]},
        },
        {
            "type":  "legal_check",
            "label": "F2 · Legal status",
            "params": {"required_for": [AGE_2_5, AGE_5_7]},
        },
        {
            "type":  "multi_boolean",
            "label": "F3 · Founder",
            "params": {
                "fields": ["full_time_founder", "founder_in_tunisia"],
                "labels": ["Full-time", "Resident"],
                "mode":   "all",
            },
        },
        {
            "type":  "boolean_field",
            "label": "F4 · Revenue",
            "params": {
                "field":   "generating_revenue",
                "label":   "Generating revenue",
                "message": "Accelerator track requires revenue",
            },
        },
        {
            "type":  "boolean_field",
            "label": "F5 · Funding",
            "params": {
                "field":   "raised_funding",
                "label":   "Raised funding",
                "message": "Accelerator track requires prior funding",
            },
        },
        {
            "type":  "maturity_outcome",
            "label": "F6 · Maturity",
            "params": {
                "outcomes": {
                    (AGE_2_5, GTM):       SELECTED,
                    (AGE_2_5, ON_MARKET): SELECTED,
                    (AGE_2_5, INTL):      SELECTED,
                    (AGE_5_7, GTM):       SELECTED,
                    (AGE_5_7, ON_MARKET): SELECTED,
                    (AGE_5_7, INTL):      SELECTED,
                },
            },
        },
    ],
    "bonus_fields": [
        ("total_employees", "Has employees",     "has_value"),
        ("gender_mixed",    "Gender-mixed team", "truthy"),
        ("num_clients",     "Has clients",       "has_value"),
        ("startup_label",   "Startup Act label", "truthy"),
    ],
    "star_threshold":      2,
    "checkmark_threshold": 1,
}

# ─────────────────────────────────────────────────────────────────────────────
ALL_CONFIGS = {
    "Dot Camp 5 (default)":        DEFAULT_CONFIG,
    "Dot Camp 6 (sector-focused)": CAMP_6_CONFIG,
    "Accelerator track (strict)":  ACCELERATOR_CONFIG,
}
