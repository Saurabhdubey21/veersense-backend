from fastapi import APIRouter
from app.core.database import get_db
from app.models.models import User, Assessment, Alert
from sqlalchemy.orm import Session
from fastapi import Depends
from sqlalchemy import func

router = APIRouter()

@router.get('/api/status')
def status():
    return {'message': 'Backend connected'}

@router.get('/api/personnel')
def get_personnel(db: Session = Depends(get_db)):
    from sqlalchemy import func
    latest_ids = (
        db.query(func.max(Assessment.id))
        .group_by(Assessment.user_id)
        .subquery()
    )
    latest = db.query(Assessment).filter(Assessment.id.in_(latest_ids)).all()
    result = []
    for a in latest:
        user = db.query(User).filter(User.id == a.user_id).first()
        result.append({
            'id': a.user_id,
            'service_no': user.username if user else 'Unknown',
            'rank': user.rank if user else 'Unknown',
            'unit': user.unit if user else 'Unknown',
            'risk_level': a.risk_level,
            'stress_score': a.score,
        })
    return result
