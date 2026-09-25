"""
Admin Panel Schemas for Model Training, Datasets, and System Performance
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class MLModelResponse(BaseModel):
    id: int
    name: str
    version: str
    accuracy: float
    f1_score: float
    precision: float
    recall: float
    status: str
    trained_at: datetime
    module_path: str

    model_config = ConfigDict(from_attributes=True)


class DatasetResponse(BaseModel):
    id: int
    filename: str
    uploaded_by: int
    uploaded_at: datetime
    row_count: int
    validated: bool

    model_config = ConfigDict(from_attributes=True)


class RetrainRequest(BaseModel):
    dataset_id: Optional[int] = None


class EvaluationMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: list[list[int]]


class RetrainResponse(BaseModel):
    message: str
    dataset_used: str
    models_evaluated: dict[str, EvaluationMetrics]
    active_model: str
    best_accuracy: float


class PerformanceStats(BaseModel):
    active_model: str
    total_predictions: int
    total_patients: int
    total_datasets: int
    avg_latency_ms: float
    system_status: str
