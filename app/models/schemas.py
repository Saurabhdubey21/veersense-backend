from datetime import datetime
from typing import Optional, Dict, List

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., description="Officer ID or Service Number")
    password: str = Field(..., min_length=4)
    role: str = Field(..., pattern="^(officer|personnel)$")
    rank: Optional[str] = None
    unit: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class MeResponse(BaseModel):
    id: int
    username: str
    role: str
    rank: Optional[str]
    unit: Optional[str]

    class Config:
        from_attributes = True


class AssessmentRequest(BaseModel):
    deployment_months: float = Field(..., ge=0, le=60)
    duty_hours: float = Field(..., ge=6, le=20)
    night_shifts: float = Field(..., ge=0, le=31)
    sleep_hours: float = Field(..., ge=0, le=12)
    traumatic_incidents: float = Field(..., ge=0, le=20)
    social_support: float = Field(..., ge=1, le=10)
    wellness_score: float = Field(..., ge=1, le=10)
    family_separated: int = Field(..., ge=0, le=1)


class AssessmentResponse(BaseModel):
    score: float
    risk_level: str
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True


class OverviewResponse(BaseModel):
    force_wellness_index: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_assessed: int
    weekly_trend: List[float]


class AlertResponse(BaseModel):
    id: int
    unit: Optional[str]
    rank: Optional[str]
    urgency: str
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AlertUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(open|flagged|resolved)$")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    reply: str