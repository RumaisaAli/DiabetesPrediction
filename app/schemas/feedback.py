"""
Feedback Schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FeedbackCreate(BaseModel):
    message: str = Field(..., min_length=3, max_length=1000)


class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    username: str
    message: str
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)
