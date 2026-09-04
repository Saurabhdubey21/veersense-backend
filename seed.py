import random

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.core import risk_engine
from app.models.models import User, Assessment, Alert

Base.metadata.create_all(bind=engine)
db = SessionLocal()

UNITS = ["42 Bn CRPF", "Signals Wing", "Border Detachment C", "Unit 4", "HQ Coy"]
RANKS = ["Constable", "Head Constable", "ASI", "SI", "Inspector"]


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

    for i in range(1, 41):
        username = f"CAPF{1000 + i}"
        unit = random.choice(UNITS)
        rank = random.choice(RANKS)
        user = get_or_create_user(username, "pass1234", "personnel", rank=rank, unit=unit)

        features = {
            "deployment_months": random.randint(1, 34),
            "duty_hours": round(random.uniform(9, 16), 1),
            "night_shifts": random.randint(0, 18),
            "sleep_hours": round(random.uniform(4, 8), 1),
            "traumatic_incidents": random.randint(0, 6),
            "social_support": random.randint(3, 10),
            "wellness_score": random.randint(3, 10),
            "family_separated": random.choice([0, 0, 1]),
        }
        score, risk = risk_engine.predict(features)
        record = Assessment(
            user_id=user.id, unit=unit, features=features,
            score=score, risk_level=risk, model_version="rule-engine-v0",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        if risk in ("High", "Medium"):
            db.add(Alert(
                assessment_id=record.id, unit=unit, rank=rank,
                urgency=risk, reason=risk_engine.alert_reason(features, risk),
            ))
            db.commit()

    print("Seeded 40 demo personnel with assessments + alerts.")
    print("Sample personnel login -> username: CAPF1001 | password: pass1234")


if __name__ == "__main__":
    main()
    db.close()