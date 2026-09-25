"""
Health Record and Prediction Schemas
Strict Pydantic models for clinical inputs and risk outputs.
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class HealthRecordCreate(BaseModel):
    pregnancies: float = Field(..., ge=0, le=25, description="Number of pregnancies")
    glucose: float = Field(..., gt=0, le=500, description="Plasma glucose concentration (mg/dL)")
    blood_pressure: float = Field(..., gt=0, le=300, description="Diastolic blood pressure (mm Hg)")
    skin_thickness: float = Field(..., ge=0, le=100, description="Triceps skin fold thickness (mm)")
    insulin: float = Field(..., ge=0, le=1000, description="2-Hour serum insulin (mu U/ml)")
    bmi: float = Field(..., gt=0, le=100, description="Body mass index (weight in kg/(height in m)^2)")
    diabetes_pedigree_function: float = Field(..., ge=0, le=5.0, description="Diabetes pedigree function score")
    age: float = Field(..., ge=1, le=130, description="Patient age in years")
    # For providers submitting on behalf of another patient
    patient_id: Optional[int] = None


class FactorDetail(BaseModel):
    feature: str
    label: str
    value: float
    impact: float
    status: str


class PredictionResult(BaseModel):
    risk_level: str
    confidence: float
    raw_score: float
    top_factors: list[FactorDetail]
    recommendations: list[str]
    model_used: str
    predicted_at: datetime


class HealthRecordResponse(BaseModel):
    id: int
    user_id: int
    pregnancies: float
    glucose: float
    blood_pressure: float
    skin_thickness: float
    insulin: float
    bmi: float
    diabetes_pedigree_function: float
    age: float
    submitted_at: datetime
    submitted_by: int
    prediction: Optional[PredictionResult] = None

    model_config = ConfigDict(from_attributes=True)


class PredictionDetailResponse(BaseModel):
    id: int
    health_record_id: int
    risk_level: str
    confidence: float
    raw_score: float
    top_factors: list[Any]
    recommendations: list[str]
    model_used: str
    predicted_at: datetime
    vitals: HealthRecordCreate


class HealthHistoryItem(BaseModel):
    id: int
    record_id: int
    date: datetime
    risk_level: str
    confidence: float
    glucose: float
    bmi: float
    blood_pressure: float
    model_used: str
