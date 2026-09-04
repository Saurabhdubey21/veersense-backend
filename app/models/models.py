from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    rank = Column(String, nullable=True)
    unit = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    assessments = relationship("Assessment", back_populates="user")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    unit = Column(String, nullable=True, index=True)

    features = Column(JSON, nullable=False)

    score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    model_version = Column(String, default="rule-engine-v0")

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assessments")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False)
    unit = Column(String, nullable=True, index=True)
    rank = Column(String, nullable=True)
    urgency = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)