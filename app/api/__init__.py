"""
API Routes Package
"""
from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.predict import router as predict_router
from app.api.admin import router as admin_router
from app.api.feedback import router as feedback_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(predict_router)
api_router.include_router(admin_router)
api_router.include_router(feedback_router)

__all__ = ["api_router"]
