"""
Feedback Submission API Router
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    fb_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submits patient or provider feedback for clinical and system improvements (TC-18)."""
    feedback = Feedback(
        user_id=current_user.id,
        message=fb_in.message,
        submitted_at=datetime.now(timezone.utc)
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        username=current_user.username,
        message=feedback.message,
        submitted_at=feedback.submitted_at
    )
