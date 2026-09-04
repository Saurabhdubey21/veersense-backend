from datetime import datetime, timedelta
from typing import List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import require_role
from app.models.models import User, Assessment, Alert
from app.models.schemas import OverviewResponse, AlertResponse, AlertUpdateRequest

router = APIRouter(prefix="/officer", tags=["officer"])


@router.get("/overview", response_model=OverviewResponse)
def overview(
    user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db),
):
    latest_ids = (
        db.query(func.max(Assessment.id))
        .group_by(Assessment.user_id)
        .subquery()
    )
    latest = db.query(Assessment).filter(Assessment.id.in_(latest_ids)).all()

    total = len(latest)
    high = sum(1 for a in latest if a.risk_level == "High")
    medium = sum(1 for a in latest if a.risk_level == "Medium")
    low = total - high - medium
    avg_score = sum(a.score for a in latest) / total if total else 0
    wellness_index = round(100 - avg_score, 1)

    trend = []
    now = datetime.utcnow()
    for w in range(7, -1, -1):
        start = now - timedelta(weeks=w + 1)
        end = now - timedelta(weeks=w)
        week_scores = [
            a.score for a in
            db.query(Assessment).filter(Assessment.created_at >= start, Assessment.created_at < end).all()
        ]
        trend.append(round(sum(week_scores) / len(week_scores), 1) if week_scores else 0)

    return OverviewResponse(
        force_wellness_index=wellness_index,
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
        total_assessed=total,
        weekly_trend=trend,
    )


@router.get("/overview/by-unit")
def overview_by_unit(
    user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db),
):
    latest_ids = (
        db.query(func.max(Assessment.id))
        .group_by(Assessment.user_id)
        .subquery()
    )
    latest = db.query(Assessment).filter(Assessment.id.in_(latest_ids)).all()

    by_unit = defaultdict(lambda: {"High": 0, "Medium": 0, "Low": 0})
    for a in latest:
        unit = a.unit or "Unassigned"
        by_unit[unit][a.risk_level] += 1

    return [{"unit": u, **counts} for u, counts in by_unit.items()]


@router.get("/alerts", response_model=List[AlertResponse])
def alerts(
    status_filter: str = "open",
    user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db),
):
    q = db.query(Alert)
    if status_filter != "all":
        q = q.filter(Alert.status == status_filter)
    return q.order_by(Alert.created_at.desc()).limit(100).all()


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    body: AlertUpdateRequest,
    user: User = Depends(require_role("officer")),
    db: Session = Depends(get_db),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = body.status
    db.commit()
    db.refresh(alert)
    return alert