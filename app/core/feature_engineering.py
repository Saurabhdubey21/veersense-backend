"""
feature_engineering.py

Converts RAW personnel data (what HRMS / the wellness app actually collects)
into the 17-field feature set the risk model expects.

Design principle: every derived score below is a documented, transparent
weighted formula -- not a black box. This matters for SIH judging on
"ethical and transparent AI decision-making" and for explaining results to
welfare officers who are not data scientists.

RAW INPUTS (collect these — from HRMS + self-assessment app):
    age                      int, years
    years_of_service         float, years
    rank_encoded             int, 0=Constable/Jawan ... N=Officer (ordinal encoding)
    deployment_months        float, current continuous deployment length
    duty_hours               float, avg daily duty hours
    night_shifts_per_month   int
    sleep_hours              float, avg nightly sleep
    incidents_exposed        int, count of traumatic/critical incidents exposed to (period)
    leaves_taken             int, leaves actually taken (period)
    leaves_entitled          int, leaves entitled/sanctioned (period)
    transfers_last_2yr       int, count of postings/transfers in last 2 years
    training_days_yr         int, days spent in training (last 12mo)
    exercise_freq_per_wk     int, self-reported exercise sessions/week (0-7)
    social_support_score     float 0-10, self-assessment (peer/family closeness)
    family_separated         bool, currently separated from family due to posting
    wellness_score           float 0-10, self-assessment app composite mood/energy score

DERIVED / COMPOSITE FEATURES (the 8 that make this model richer than a
simple rule engine):
    leave_cancel_ratio   -- how much of entitled leave was actually denied/cancelled
    overwork_score       -- duty hour + night shift load, normalized 0-100
    recovery_index       -- how well the person is recovering (sleep + exercise), 0-100
    isolation_score      -- social/family isolation risk, 0-100
    workload_stress      -- combined workload pressure (duty + training + leave denial), 0-100
    burnout_index         -- overwork sustained without recovery, 0-100
    resilience_score     -- protective factors (recovery, support, experience), 0-100
    family_separation    -- pass-through/normalized version of family_separated for the model
"""

from typing import Dict


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def compute_derived_features(raw: Dict) -> Dict:
    """
    raw: dict containing the RAW INPUTS listed in the module docstring.
    Returns: dict with the 8 derived composite features added.
    Does NOT mutate the input dict.
    """
    out = dict(raw)

    leaves_entitled = max(raw.get("leaves_entitled", 0), 1)  # avoid div/0
    leaves_taken = raw.get("leaves_taken", 0)
    leave_cancel_ratio = _clip(
        (1 - (leaves_taken / leaves_entitled)) * 100
    )

    # Overwork: hours beyond a healthy 8h baseline + night shift load
    duty_hours = raw.get("duty_hours", 8)
    night_shifts = raw.get("night_shifts_per_month", 0)
    overwork_score = _clip(
        (max(0, duty_hours - 8) / 8) * 60 + (night_shifts / 20) * 40
    )

    # Recovery: sleep quality + physical activity, both protective
    sleep_hours = raw.get("sleep_hours", 6)
    exercise = raw.get("exercise_freq_per_wk", 0)
    recovery_index = _clip(
        (min(sleep_hours, 8) / 8) * 60 + (min(exercise, 5) / 5) * 40
    )

    # Isolation: family separation + low social support + frequent transfers
    social_support = raw.get("social_support_score", 5)
    transfers = raw.get("transfers_last_2yr", 0)
    family_separated = 1 if raw.get("family_separated") else 0
    isolation_score = _clip(
        family_separated * 40
        + (1 - min(social_support, 10) / 10) * 40
        + (min(transfers, 4) / 4) * 20
    )

    # Workload stress: duty load + training burden + denied leave
    training_days = raw.get("training_days_yr", 0)
    workload_stress = _clip(
        overwork_score * 0.5
        + (min(training_days, 60) / 60) * 25
        + (leave_cancel_ratio / 100) * 25
    )

    # Burnout: sustained overwork/exposure without adequate recovery
    incidents = raw.get("incidents_exposed", 0)
    burnout_index = _clip(
        overwork_score * 0.4
        + (min(incidents, 10) / 10) * 30
        + (1 - recovery_index / 100) * 30
    )

    # Resilience: protective factors that offset risk (higher = more protected)
    years_of_service = raw.get("years_of_service", 0)
    resilience_score = _clip(
        recovery_index * 0.4
        + (min(social_support, 10) / 10) * 100 * 0.35
        + (min(years_of_service, 15) / 15) * 100 * 0.25
    )

    out.update({
        "leave_cancel_ratio": round(leave_cancel_ratio, 1),
        "overwork_score": round(overwork_score, 1),
        "recovery_index": round(recovery_index, 1),
        "isolation_score": round(isolation_score, 1),
        "workload_stress": round(workload_stress, 1),
        "burnout_index": round(burnout_index, 1),
        "resilience_score": round(resilience_score, 1),
        "family_separation": family_separated,
    })
    return out


# The 17 fields the trained model (stress_model.pkl) expects, in the
# order/spelling it was trained on.
MODEL_FEATURES = [
    "age",
    "years_of_service",
    "deployment_months",
    "family_separation",
    "leave_cancel_ratio",
    "overwork_score",
    "transfers_last_2yr",
    "night_shifts_per_month",
    "incidents_exposed",
    "training_days_yr",
    "wellness_score",
    "sleep_hours",
    "exercise_freq_per_wk",
    "social_support_score",
    "rank_encoded",
    "burnout_index",
    "recovery_index",
    "isolation_score",
    "workload_stress",
    "resilience_score",
]