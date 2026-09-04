import os
from typing import Dict, Tuple

import pandas as pd

from app.core.config import settings

REQUIRED_FEATURES = [
    "deployment_months",
    "duty_hours",
    "night_shifts",
    "sleep_hours",
    "traumatic_incidents",
    "social_support",
    "wellness_score",
    "family_separated",
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
    s = 0.0
    s += (f["deployment_months"] / 36) * 28
    s += (max(0, f["duty_hours"] - 8) / 8) * 22
    s += (f["night_shifts"] / 20) * 14
    s += f["family_separated"] * 10
    s += (f["traumatic_incidents"] / 10) * 14
    s -= ((f["sleep_hours"] - 3) / 7) * 16
    s -= (f["social_support"] / 10) * 8
    s -= (f["wellness_score"] / 10) * 10
    return max(0.0, min(100.0, round(s, 1)))


def _ml_score(f: Dict) -> Tuple[float, str]:
    row = pd.DataFrame([f])[_ml_artifact["features"]]
    scaler = _ml_artifact.get("scaler")
    if scaler is not None:
        row = scaler.transform(row)
    risk = _ml_artifact["model"].predict(row)[0]
    proba = dict(zip(_ml_artifact["classes"], _ml_artifact["model"].predict_proba(row)[0]))
    score = round(proba.get("Medium", 0) * 50 + proba.get("High", 0) * 100, 1)
    return score, str(risk)


def predict(features: Dict) -> Tuple[float, str]:
    missing = [k for k in REQUIRED_FEATURES if k not in features]
    if missing:
        raise ValueError(f"Missing required features: {missing}")

    if _ml_artifact is not None:
        return _ml_score(features)

    score = _rule_based_score(features)
    risk = "High" if score >= 60 else "Medium" if score >= 35 else "Low"
    return score, risk


def alert_reason(features: Dict, risk: str) -> str:
    if features["deployment_months"] >= 24:
        return f"{int(features['deployment_months'])}-month continuous deployment"
    if features["duty_hours"] >= 13:
        return f"{features['duty_hours']}h avg duty, {features['sleep_hours']}h sleep"
    if features["family_separated"]:
        return "Extended family separation"
    if features["night_shifts"] >= 15:
        return f"Night shift load {int(features['night_shifts'])}/month"
    return f"Composite {risk.lower()}-risk profile flagged"