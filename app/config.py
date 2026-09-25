"""
Application Configuration
Loads settings from environment variables or .env file with type safety via Pydantic.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelligent Diabetes Risk Predictor"
    GROUP_ID: str = "S26PROJECTA7FFD"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str = "postgresql://user:password@localhost:5432/diabetes_predictor"
    TEST_DATABASE_URL: Optional[str] = "postgresql://user:password@localhost:5432/diabetes_predictor_test"

    SECRET_KEY: str = "diabetes-predictor-super-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    ACTIVE_MODEL_NAME: str = "Decision Tree"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
