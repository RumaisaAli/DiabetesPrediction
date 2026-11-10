"""
Patient Record Schemas
Pydantic models for provider clinical patient listing and detailed medical history.
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.health import HealthHistoryItem


class PatientSummary(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    total_assessments: int
    latest_risk_level: Optional[str] = None
    latest_confidence: Optional[float] = None
    last_assessment_date: Optional[datetime] = None
    latest_age: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class PatientDetail(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    total_assessments: int
    latest_risk_level: Optional[str] = None
    latest_confidence: Optional[float] = None
    last_assessment_date: Optional[datetime] = None
    latest_vitals: Optional[dict[str, Any]] = None
    history: list[HealthHistoryItem] = []

    model_config = ConfigDict(from_attributes=True)

