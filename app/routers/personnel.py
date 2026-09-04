from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core import risk_engine
from app.core.feature_engineering import compute_derived_features
from app.models.models import User, Assessment, Alert
from app.models.schemas import AssessmentRequest, AssessmentResponse

router = APIRouter(prefix="/personnel", tags=["personnel"])


@router.post("/assessment", response_model=AssessmentResponse)
def submit_assessment(
    body: AssessmentRequest,
    user: User = Depends(require_role("personnel")),
    db: Session = Depends(get_db),
):
    raw_features = body.dict()
    try:
        score, risk = risk_engine.predict(raw_features)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record = Assessment(
        user_id=user.id,
        unit=user.unit,
        features=raw_features,
        score=score,
        risk_level=risk,
        model_version=risk_engine.model_version(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if risk in ("High", "Medium"):
        # alert_reason needs the derived composite scores
        # (burnout_index, isolation_score, etc.), not raw inputs.
        derived_features = compute_derived_features(raw_features)
        alert = Alert(
            assessment_id=record.id,
            unit=user.unit,
            rank=user.rank,
            urgency=risk,
            reason=risk_engine.alert_reason(derived_features, risk),
        )
        db.add(alert)
        db.commit()

    return record


@router.get("/assessment/history", response_model=List[AssessmentResponse])
def my_history(
    user: User = Depends(require_role("personnel")),
    db: Session = Depends(get_db),
):
    return (
        db.query(Assessment)
        .filter(Assessment.user_id == user.id)
        .order_by(Assessment.created_at.desc())
        .limit(20)
        .all()
    )