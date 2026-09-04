import random

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.core import risk_engine
from app.core.feature_engineering import compute_derived_features
from app.models.models import User, Assessment, Alert

Base.metadata.create_all(bind=engine)
db = SessionLocal()

UNITS = ["42 Bn CRPF", "Signals Wing", "Border Detachment C", "Unit 4", "HQ Coy"]
RANKS = ["Constable", "Head Constable", "ASI", "SI", "Inspector"]
RANK_ENCODING = {r: i for i, r in enumerate(RANKS)}

FORCE_CODES = ["CRPF", "BSF", "CISF", "ITBP", "SSB"]


def make_service_id(used_ids):
    while True:
        force = random.choice(FORCE_CODES)
        number = random.randint(100000, 999999)
        sid = f"{force}-{number}"
        if sid not in used_ids:
            used_ids.add(sid)
            return sid


def get_or_create_user(username, password, role, rank=None, unit=None):
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return existing
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=role,
        rank=rank,
        unit=unit,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main():
    get_or_create_user("admin", "1234", "officer", rank="Commandant", unit="HQ")
    print("Officer account ready -> username: admin | password: 1234")

    used_ids = set()

    for i in range(1, 1001):
        username = make_service_id(used_ids)
        unit = random.choice(UNITS)
        rank = random.choice(RANKS)
        user = get_or_create_user(username, "pass1234", "personnel", rank=rank, unit=unit)

        leaves_entitled = random.randint(15, 30)
        leaves_taken = random.randint(0, leaves_entitled)

        raw_features = {
            "age": random.randint(22, 55),
            "years_of_service": round(random.uniform(1, 30), 1),
            "rank_encoded": RANK_ENCODING[rank],
            "deployment_months": random.randint(1, 34),
            "duty_hours": round(random.uniform(9, 16), 1),
            "night_shifts_per_month": random.randint(0, 18),
            "sleep_hours": round(random.uniform(4, 8), 1),
            "incidents_exposed": random.randint(0, 6),
            "leaves_taken": leaves_taken,
            "leaves_entitled": leaves_entitled,
            "transfers_last_2yr": random.randint(0, 4),
            "training_days_yr": random.randint(0, 45),
            "exercise_freq_per_wk": random.randint(0, 7),
            "social_support_score": random.randint(3, 10),
            "family_separated": random.choice([0, 0, 1]),
            "wellness_score": random.randint(3, 10),
        }

        score, risk = risk_engine.predict(raw_features)
        derived_features = compute_derived_features(raw_features)

        record = Assessment(
            user_id=user.id, unit=unit, features=raw_features,
            score=score, risk_level=risk, model_version=risk_engine.model_version(),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        if risk in ("High", "Medium"):
            db.add(Alert(
                assessment_id=record.id, unit=unit, rank=rank,
                urgency=risk, reason=risk_engine.alert_reason(derived_features, risk),
            ))
            db.commit()

    print("Seeded 1000 demo personnel with assessments + alerts.")
    print("Sample personnel login -> check the database for a generated service ID, password: pass1234")


if __name__ == "__main__":
    main()
    db.close()
