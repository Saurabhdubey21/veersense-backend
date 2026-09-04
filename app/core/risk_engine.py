import os
from typing import Dict, Tuple

import pandas as pd

from app.core.config import settings
from app.core.feature_engineering import compute_derived_features, MODEL_FEATURES

# RAW inputs collected from HRMS + the wellness self-assessment app.
# feature_engineering.compute_derived_features() turns these into the
# full 17-field set the ML model expects (see MODEL_FEATURES).
REQUIRED_RAW_FEATURES = [
    "age",
    "years_of_service",
    "rank_encoded",
    "deployment_months",
    "duty_hours",
    "night_shifts_per_month",
    "sleep_hours",
    "incidents_exposed",
    "leaves_taken",
    "leaves_entitled",
    "transfers_last_2yr",
    "training_days_yr",
    "exercise_freq_per_wk",
    "social_support_score",
    "family_separated",
    "wellness_score",
]

_ml_artifact = None
_model_version = "rule-engine-v0"

if os.path.exists(settings.MODEL_PATH):
    try:
        import joblib
        _ml_artifact = joblib.load(settings.MODEL_PATH)
        _model_version = f"{_ml_artifact.get('model_name', 'ml-model')}-v1"
        print(f"[risk_engine] Loaded trained model from {settings.MODEL_PATH}")
    except Exception as e:
        print(f"[risk_engine] Found {settings.MODEL_PATH} but failed to load it ({e}); "
              f"falling back to rule-engine.")
        _ml_artifact = None
else:
    print(f"[risk_engine] No trained model at {settings.MODEL_PATH} yet — "
          f"using rule-engine-v0.")


def model_version() -> str:
    return _model_version


def _rule_based_score(f: Dict) -> float:
    """
    Transparent fallback scorer, used when no trained model is loaded.
    Operates on the derived (17-field) feature set so its output is
    directly comparable to the ML model's.
    """
    s = 0.0
    s += (f["deployment_months"] / 36) * 18
    s += (f["overwork_score"] / 100) * 16
    s += (f["burnout_index"] / 100) * 20
    s += (f["workload_stress"] / 100) * 14
    s += (f["isolation_score"] / 100) * 12
    s += (f["incidents_exposed"] / 10) * 10
    s -= (f["recovery_index"] / 100) * 10
    s -= (f["resilience_score"] / 100) * 10
    s -= (f["social_support_score"] / 10) * 6
    return max(0.0, min(100.0, round(s, 1)))


def _ml_score(f: Dict) -> Tuple[float, str]:
    row = pd.DataFrame([f])[MODEL_FEATURES]
    scaler = _ml_artifact.get("scaler")
    if scaler is not None:
        row = scaler.transform(row)
    risk = _ml_artifact["model"].predict(row)[0]
    proba = dict(zip(_ml_artifact["classes"], _ml_artifact["model"].predict_proba(row)[0]))
    score = round(proba.get("Medium", 0) * 50 + proba.get("High", 0) * 100, 1)
    return score, str(risk)


def predict(raw_features: Dict) -> Tuple[float, str]:
    """
    raw_features: dict containing REQUIRED_RAW_FEATURES (what HRMS / the
    app actually collects). This function derives the full 17-field
    feature set internally before scoring.
    """
    missing = [k for k in REQUIRED_RAW_FEATURES if k not in raw_features]
    if missing:
        raise ValueError(f"Missing required raw features: {missing}")

    features = compute_derived_features(raw_features)

    if _ml_artifact is not None:
        return _ml_score(features)

    score = _rule_based_score(features)
    risk = "High" if score >= 60 else "Medium" if score >= 35 else "Low"
    return score, risk


def alert_reason(features: Dict, risk: str) -> str:
    """
    features here should be the DERIVED feature dict (output of
    compute_derived_features), so it has access to composite scores.
    """
    if features.get("deployment_months", 0) >= 24:
        return f"{int(features['deployment_months'])}-month continuous deployment"
    if features.get("burnout_index", 0) >= 70:
        return f"High burnout index ({features['burnout_index']}/100)"
    if features.get("family_separation"):
        return "Extended family separation"
    if features.get("night_shifts_per_month", 0) >= 15:
        return f"Night shift load {int(features['night_shifts_per_month'])}/month"
    if features.get("isolation_score", 0) >= 60:
        return f"Elevated isolation risk ({features['isolation_score']}/100)"
    return f"Composite {risk.lower()}-risk profile flagged"