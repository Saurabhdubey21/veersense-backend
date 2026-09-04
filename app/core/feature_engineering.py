"""
Drop-in replacement for the feature-building section of seed.py.

Wherever seed.py currently builds the `features` dict passed to
risk_engine.predict(), replace it with something shaped like this.
Adjust the mock-data ranges/logic to match however your seed script
currently generates personnel records (this is illustrative).
"""

import random


def build_mock_raw_features(personnel_record: dict) -> dict:
    """
    personnel_record: whatever dict/object seed.py already has per
    officer (name, id, posting, etc.) — pull real fields from it where
    they exist, and mock the rest for demo/seed purposes.
    """
    rank_map = {"Constable": 0, "Head Constable": 1, "ASI": 2, "SI": 3,
                "Inspector": 4, "DSP": 5, "SP": 6}

    leaves_entitled = random.randint(15, 30)
    leaves_taken = random.randint(0, leaves_entitled)

    return {
        "age": personnel_record.get("age", random.randint(22, 55)),
        "years_of_service": personnel_record.get(
            "years_of_service", round(random.uniform(1, 30), 1)
        ),
        "rank_encoded": rank_map.get(personnel_record.get("rank"), random.randint(0, 6)),
        "deployment_months": round(random.uniform(0, 36), 1),
        "duty_hours": round(random.uniform(6, 16), 1),
        "night_shifts_per_month": random.randint(0, 20),
        "sleep_hours": round(random.uniform(3, 8), 1),
        "incidents_exposed": random.randint(0, 10),
        "leaves_taken": leaves_taken,
        "leaves_entitled": leaves_entitled,
        "transfers_last_2yr": random.randint(0, 4),
        "training_days_yr": random.randint(0, 60),
        "exercise_freq_per_wk": random.randint(0, 7),
        "social_support_score": round(random.uniform(0, 10), 1),
        "family_separated": random.random() < 0.4,
        "wellness_score": round(random.uniform(0, 10), 1),
    }


# Example usage inside seed.py's main() loop:
#
#   from app.core import risk_engine
#
#   for personnel in personnel_records:
#       raw = build_mock_raw_features(personnel)
#       score, risk = risk_engine.predict(raw)
#       print(personnel["name"], score, risk)