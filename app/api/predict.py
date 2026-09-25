"""
Prediction and Health Record Routes
Handles clinical data submission, inference routing, health tracking, and PDF report downloads.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, HealthRecord, Prediction, MLModel
from app.schemas.health import (
    HealthRecordCreate,
    PredictionDetailResponse,
    HealthHistoryItem,
)
from app.api.deps import get_current_user, get_active_model_name
from app.ml.inference import predict_diabetes_risk
from app.ml.report_generator import generate_pdf_report

router = APIRouter(tags=["Prediction & Health Records"])


@router.get("/active-model")
def get_current_active_model(db: Session = Depends(get_db)):
    """Returns the name and status of the currently active model (accessible to all authenticated users)."""
    active_name = get_active_model_name(db)
    model_obj = db.query(MLModel).filter(MLModel.name == active_name).first()
    return {
        "active_model": active_name,
        "version": model_obj.version if model_obj else "1.0.0",
        "accuracy": model_obj.accuracy if model_obj else 0.0
    }


@router.post("/predict", response_model=PredictionDetailResponse, status_code=status.HTTP_201_CREATED)
def create_prediction(
    record_in: HealthRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits patient health record, triggers ML inference with active model,
    persists record and prediction to PostgreSQL, and returns detailed risk results (TC-03, TC-05).
    """
    # Determine which patient this record is for
    target_user_id = current_user.id
    if record_in.patient_id and current_user.role in ["provider", "admin"]:
        patient = db.query(User).filter(User.id == record_in.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient with ID {record_in.patient_id} not found."
            )
        target_user_id = patient.id

    # Active model selection from DB
    active_model_name = get_active_model_name(db)

    # 1. Execute ML Inference (no pickle/joblib used at runtime!)
    vitals_dict = record_in.model_dump()
    ml_result = predict_diabetes_risk(vitals_dict, model_name=active_model_name)

    now = datetime.now(timezone.utc)

    # 2. Persist Health Record in PostgreSQL
    health_record = HealthRecord(
        user_id=target_user_id,
        pregnancies=record_in.pregnancies,
        glucose=record_in.glucose,
        blood_pressure=record_in.blood_pressure,
        skin_thickness=record_in.skin_thickness,
        insulin=record_in.insulin,
        bmi=record_in.bmi,
        diabetes_pedigree_function=record_in.diabetes_pedigree_function,
        age=record_in.age,
        submitted_at=now,
        submitted_by=current_user.id
    )
    db.add(health_record)
    db.flush()

    # 3. Persist Prediction Result with JSONB top_factors in PostgreSQL
    prediction = Prediction(
        health_record_id=health_record.id,
        risk_level=ml_result["risk_level"],
        confidence=ml_result["confidence"],
        top_factors=ml_result["top_factors"],
        model_used=ml_result["model_used"],
        predicted_at=now
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return PredictionDetailResponse(
        id=prediction.id,
        health_record_id=health_record.id,
        risk_level=prediction.risk_level,
        confidence=prediction.confidence,
        raw_score=ml_result["raw_score"],
        top_factors=prediction.top_factors,
        recommendations=ml_result["recommendations"],
        model_used=prediction.model_used,
        predicted_at=prediction.predicted_at,
        vitals=record_in
    )


@router.get("/records", response_model=list[HealthHistoryItem])
def get_user_records(
    patient_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves chronological past health records and prediction trends (TC-15, TC-16).
    """
    target_user_id = current_user.id
    if patient_id and current_user.role in ["provider", "admin"]:
        target_user_id = patient_id

    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == target_user_id)
        .order_by(HealthRecord.submitted_at.desc())
        .all()
    )

    history = []
    for r in records:
        if r.prediction:
            history.append(HealthHistoryItem(
                id=r.prediction.id,
                record_id=r.id,
                date=r.submitted_at,
                risk_level=r.prediction.risk_level,
                confidence=r.prediction.confidence,
                glucose=r.glucose,
                bmi=r.bmi,
                blood_pressure=r.blood_pressure,
                model_used=r.prediction.model_used
            ))

    return history


@router.get("/report/{prediction_id}/pdf")
def download_pdf_report(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates and downloads an official clinical assessment PDF report (TC-12).
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction report not found.")

    record = prediction.health_record
    # Authorization check: user must own record, or be provider/admin
    if current_user.role == "patient" and record.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this report.")

    patient_user = record.user
    vitals_dict = {
        "pregnancies": record.pregnancies,
        "glucose": record.glucose,
        "blood_pressure": record.blood_pressure,
        "skin_thickness": record.skin_thickness,
        "insulin": record.insulin,
        "bmi": record.bmi,
        "diabetes_pedigree_function": record.diabetes_pedigree_function,
        "age": record.age,
    }

    # Re-generate recommendations if not directly stored in prediction table
    from app.ml.recommendations import generate_recommendations
    recs = generate_recommendations(prediction.risk_level, prediction.top_factors, vitals_dict)

    pred_dict = {
        "risk_level": prediction.risk_level,
        "confidence": prediction.confidence,
        "top_factors": prediction.top_factors,
        "recommendations": recs,
        "model_used": prediction.model_used,
    }

    pdf_bytes = generate_pdf_report(
        patient_name=patient_user.username,
        patient_email=patient_user.email,
        vitals=vitals_dict,
        prediction=pred_dict,
        report_id=f"GLUCO-REP-{prediction.id:04d}"
    )

    filename = f"Diabetes_Report_{patient_user.username}_{prediction.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
