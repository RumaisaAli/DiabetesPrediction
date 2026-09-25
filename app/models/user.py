"""
User model representing patients, healthcare providers, and administrators.
"""
from datetime import datetime, timezone
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="patient", nullable=False)  # "patient", "provider", "admin"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    health_records: Mapped[list["HealthRecord"]] = relationship(
        "HealthRecord",
        foreign_keys="[HealthRecord.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    feedback_submissions: Mapped[list["Feedback"]] = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    uploaded_datasets: Mapped[list["Dataset"]] = relationship(
        "Dataset",
        back_populates="uploader"
    )
