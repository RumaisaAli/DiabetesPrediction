"""
HealthRecord model storing patient clinical vitals and demographic data.
"""
from datetime import datetime, timezone
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    age: Mapped[float] = mapped_column(Float, nullable=False)
    bmi: Mapped[float] = mapped_column(Float, nullable=False)
    glucose: Mapped[float] = mapped_column(Float, nullable=False)
    blood_pressure: Mapped[float] = mapped_column(Float, nullable=False)
    insulin: Mapped[float] = mapped_column(Float, nullable=False)
    skin_thickness: Mapped[float] = mapped_column(Float, nullable=False)
    pregnancies: Mapped[float] = mapped_column(Float, nullable=False)
    diabetes_pedigree_function: Mapped[float] = mapped_column(Float, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    submitted_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="health_records")
    prediction: Mapped["Prediction"] = relationship("Prediction", back_populates="health_record", uselist=False, cascade="all, delete-orphan")
