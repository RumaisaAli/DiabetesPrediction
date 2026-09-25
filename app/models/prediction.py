"""
Prediction model storing risk assessment results, confidence scores, and top contributing factors.
"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    health_record_id: Mapped[int] = mapped_column(Integer, ForeignKey("health_records.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # "High" or "Low"
    confidence: Mapped[float] = mapped_column(Float, nullable=False)    # e.g. 76.62 (%)
    top_factors: Mapped[Any] = mapped_column(JSONB, nullable=False)      # JSON list of factor dicts
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    health_record: Mapped["HealthRecord"] = relationship("HealthRecord", back_populates="prediction")
