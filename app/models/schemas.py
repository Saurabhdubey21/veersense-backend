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
    """
    Raw inputs collected from HRMS + the wellness self-assessment app.
    Matches app.core.risk_engine.REQUIRED_RAW_FEATURES exactly --
    if you add/remove a field here, update REQUIRED_RAW_FEATURES too.
    """
    age: int = Field(..., ge=18, le=60)
    years_of_service: float = Field(..., ge=0, le=40)
    rank_encoded: int = Field(..., ge=0, le=6)
    deployment_months: float = Field(..., ge=0, le=60)
    duty_hours: float = Field(..., ge=6, le=20)
    night_shifts_per_month: float = Field(..., ge=0, le=31)
    sleep_hours: float = Field(..., ge=0, le=12)
    incidents_exposed: float = Field(..., ge=0, le=20)
    leaves_taken: int = Field(..., ge=0, le=60)
    leaves_entitled: int = Field(..., ge=1, le=60)
    transfers_last_2yr: int = Field(..., ge=0, le=10)
    training_days_yr: int = Field(..., ge=0, le=120)
    exercise_freq_per_wk: int = Field(..., ge=0, le=7)
    social_support_score: float = Field(..., ge=0, le=10)
    family_separated: int = Field(..., ge=0, le=1)
    wellness_score: float = Field(..., ge=0, le=10)


class AssessmentResponse(BaseModel):
    score: float
    risk_level: str
    model_version: str
    created_at: datetime

    class Config:
        from_attributes = True
        protected_namespaces = ()


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