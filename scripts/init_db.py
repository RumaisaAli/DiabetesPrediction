"""
Database Seeding Script
Initializes default roles, users, and baseline model metadata.
"""
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security import get_password_hash
from app.database import SessionLocal
from app.models import User, MLModel, HealthRecord, Prediction, Dataset


def seed_db():
    db = SessionLocal()
    try:
        # Check if users already seeded
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@gluco.ai",
                password_hash=get_password_hash("AdminPassword123!"),
                role="admin",
                created_at=datetime.now(timezone.utc)
            )
            db.add(admin_user)
            db.flush()

        provider_user = db.query(User).filter(User.username == "dr_smith").first()
        if not provider_user:
            provider_user = User(
                username="dr_smith",
                email="provider@gluco.ai",
                password_hash=get_password_hash("ProviderPassword123!"),
                role="provider",
                created_at=datetime.now(timezone.utc)
            )
            db.add(provider_user)
            db.flush()

        patient_user = db.query(User).filter(User.username == "sarah_jenkins").first()
        if not patient_user:
            patient_user = User(
                username="sarah_jenkins",
                email="patient@gluco.ai",
                password_hash=get_password_hash("PatientPassword123!"),
                role="patient",
                created_at=datetime.now(timezone.utc)
            )
            db.add(patient_user)
            db.flush()

        # Seed baseline models
        existing_models = db.query(MLModel).all()
        if not existing_models:
            models_data = [
                {
                    "name": "Decision Tree",
                    "version": "1.0.0",
                    "accuracy": 76.62,
                    "f1_score": 0.68,
                    "precision": 0.72,
                    "recall": 0.65,
                    "status": "active",
                    "trained_at": datetime.now(timezone.utc),
                    "module_path": "app.ml.models.decision_tree"
                },
                {
                    "name": "Logistic Regression",
                    "version": "1.0.0",
                    "accuracy": 75.32,
                    "f1_score": 0.66,
                    "precision": 0.70,
                    "recall": 0.62,
                    "status": "trained",
                    "trained_at": datetime.now(timezone.utc),
                    "module_path": "app.ml.models.logistic_regression"
                },
                {
                    "name": "Neural Network",
                    "version": "1.0.0",
                    "accuracy": 74.68,
                    "f1_score": 0.64,
                    "precision": 0.69,
                    "recall": 0.60,
                    "status": "trained",
                    "trained_at": datetime.now(timezone.utc),
                    "module_path": "app.ml.models.neural_network"
                },
                {
                    "name": "SVM",
                    "version": "1.0.0",
                    "accuracy": 73.38,
                    "f1_score": 0.63,
                    "precision": 0.68,
                    "recall": 0.59,
                    "status": "trained",
                    "trained_at": datetime.now(timezone.utc),
                    "module_path": "app.ml.models.svm"
                }
            ]
            for m in models_data:
                db.add(MLModel(**m))

        # Seed historical records for sarah_jenkins to demonstrate trend visualization
        if patient_user and not patient_user.health_records:
            now = datetime.now(timezone.utc)
            sample_history = [
                (25, 2, 27.5, 110.0, 74.0, 85.0, 22.0, 0.35, 30.0, "Low", 82.5, "Optimal"),
                (14, 2, 28.1, 125.0, 76.0, 92.0, 24.0, 0.35, 30.0, "Low", 78.0, "Optimal"),
                (3,  2, 29.0, 138.0, 78.0, 105.0, 25.0, 0.35, 30.0, "High", 65.4, "Elevated"),
            ]
            for days_ago, preg, bmi, glu, bp, ins, skin, dpf, age, risk, conf, status in sample_history:
                submitted_time = now - timedelta(days=days_ago)
                hr = HealthRecord(
                    user_id=patient_user.id,
                    pregnancies=preg,
                    glucose=glu,
                    blood_pressure=bp,
                    skin_thickness=skin,
                    insulin=ins,
                    bmi=bmi,
                    diabetes_pedigree_function=dpf,
                    age=age,
                    submitted_at=submitted_time,
                    submitted_by=patient_user.id
                )
                db.add(hr)
                db.flush()
                pred = Prediction(
                    health_record_id=hr.id,
                    risk_level=risk,
                    confidence=conf,
                    top_factors=[
                        {"feature": "Glucose", "label": "Blood Glucose Level", "value": glu, "impact": 42.0, "status": status},
                        {"feature": "BMI", "label": "Body Mass Index", "value": bmi, "impact": 28.0, "status": "Optimal"},
                        {"feature": "Age", "label": "Patient Age", "value": age, "impact": 18.0, "status": "Optimal"},
                    ],
                    model_used="Decision Tree",
                    predicted_at=submitted_time
                )
                db.add(pred)

        # Seed initial dataset record for diabetes.csv
        existing_dataset = db.query(Dataset).first()
        if not existing_dataset and admin_user:
            dataset_path = os.path.abspath("diabetes.csv")
            if os.path.exists(dataset_path):
                import pandas as pd
                df = pd.read_csv(dataset_path)
                db.add(Dataset(
                    filename="diabetes.csv",
                    filepath=dataset_path,
                    uploaded_by=admin_user.id,
                    uploaded_at=datetime.now(timezone.utc),
                    row_count=len(df),
                    validated=True
                ))

        db.commit()
        print("Database successfully seeded with default users, models, and sample history!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
