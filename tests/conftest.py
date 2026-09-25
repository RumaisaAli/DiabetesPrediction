"""
Pytest configuration and shared fixtures for all 20 test cases.
Sets up test PostgreSQL database, FastAPI TestClient, and role-based auth tokens.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.models import User, MLModel, HealthRecord, Prediction, Dataset
from app.security import get_password_hash, create_access_token

TEST_DB_URL = "postgresql://user:password@localhost:5432/diabetes_predictor_test"

test_engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Ensures test database tables exist and seeds baseline models and accounts."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        # Seed test users
        if not db.query(User).filter(User.username == "test_admin").first():
            db.add(User(
                username="test_admin",
                email="admin@test.com",
                password_hash=get_password_hash("AdminPass123!"),
                role="admin"
            ))

        if not db.query(User).filter(User.username == "test_provider").first():
            db.add(User(
                username="test_provider",
                email="provider@test.com",
                password_hash=get_password_hash("ProviderPass123!"),
                role="provider"
            ))

        if not db.query(User).filter(User.username == "test_patient").first():
            db.add(User(
                username="test_patient",
                email="patient@test.com",
                password_hash=get_password_hash("PatientPass123!"),
                role="patient"
            ))

        # Seed baseline test models
        if not db.query(MLModel).first():
            db.add(MLModel(
                name="Decision Tree",
                version="1.0.0",
                accuracy=76.62,
                f1_score=0.68,
                precision=0.72,
                recall=0.65,
                status="active",
                module_path="app.ml.models.decision_tree"
            ))
            db.add(MLModel(
                name="Logistic Regression",
                version="1.0.0",
                accuracy=75.32,
                f1_score=0.66,
                precision=0.70,
                recall=0.62,
                status="trained",
                module_path="app.ml.models.logistic_regression"
            ))
            db.add(MLModel(
                name="Neural Network",
                version="1.0.0",
                accuracy=74.68,
                f1_score=0.64,
                precision=0.69,
                recall=0.60,
                status="trained",
                module_path="app.ml.models.neural_network"
            ))
            db.add(MLModel(
                name="SVM",
                version="1.0.0",
                accuracy=73.38,
                f1_score=0.63,
                precision=0.68,
                recall=0.59,
                status="trained",
                module_path="app.ml.models.svm"
            ))

        db.commit()
    finally:
        db.close()

    yield


@pytest.fixture
def db_session():
    """Provides a transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client():
    """FastAPI TestClient with overridden get_db dependency pointing to test PostgreSQL DB."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db_session):
    admin = db_session.query(User).filter(User.username == "test_admin").first()
    return create_access_token(subject=admin.id, role=admin.role)


@pytest.fixture
def provider_token(db_session):
    provider = db_session.query(User).filter(User.username == "test_provider").first()
    return create_access_token(subject=provider.id, role=provider.role)


@pytest.fixture
def patient_token(db_session):
    patient = db_session.query(User).filter(User.username == "test_patient").first()
    return create_access_token(subject=patient.id, role=patient.role)


@pytest.fixture
def patient_user(db_session):
    return db_session.query(User).filter(User.username == "test_patient").first()
