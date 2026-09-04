from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.core import risk_engine
from app.models.models import User, Assessment, Alert
from app.models.schemas import AssessmentRequest, AssessmentResponse

router = APIRouter(prefix="/personnel", tags=["personnel"])


@router.post("/assessment", response_model=AssessmentResponse)
def submit_assessment(
    body: AssessmentRequest,
    user: User = Depends(require_role("personnel")),
    db: Session = Depends(get_db),
):
    features = body.dict()
    try:
        score, risk = risk_engine.predict(features)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record = Assessment(
        user_id=user.id,
        unit=user.unit,
        features=features,
        score=score,
        risk_level=risk,
        model_version=risk_engine.model_version(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    if risk in ("High", "Medium"):
        alert = Alert(
            assessment_id=record.id,
            unit=user.unit,
            rank=user.rank,
            urgency=risk,
            reason=risk_engine.alert_reason(features, risk),
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