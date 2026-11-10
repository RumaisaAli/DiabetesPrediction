"""
Healthcare Provider Patient Records Router
Provides patient listing, search/filter, and comprehensive clinical history retrieval.
Gated strictly to healthcare providers and administrators via require_role("provider", "admin").
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, HealthRecord, Prediction
from app.schemas.patients import PatientSummary, PatientDetail
from app.schemas.health import HealthHistoryItem
from app.api.deps import require_role

router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
    dependencies=[Depends(require_role("provider", "admin"))]
)


@router.get("", response_model=list[PatientSummary])
def list_patients(
    search: Optional[str] = Query(None, description="Search by username or email (case-insensitive)"),
    risk: Optional[str] = Query(None, description="Filter by latest risk level (High or Low)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Lists registered patients with their assessment totals and latest risk metrics (TC-21, TC-22, TC-23).
    Restricted to providers and administrators. Uses window subqueries to avoid N+1 queries.
    """
    # 1. Rank health records to locate the latest assessment per patient
    latest_record_subquery = (
        select(
            HealthRecord.user_id,
            HealthRecord.id.label("health_record_id"),
            HealthRecord.submitted_at,
            HealthRecord.age,
            Prediction.risk_level,
            Prediction.confidence,
            func.row_number().over(
                partition_by=HealthRecord.user_id,
                order_by=HealthRecord.submitted_at.desc()
            ).label("rn")
        )
        .outerjoin(Prediction, Prediction.health_record_id == HealthRecord.id)
        .subquery("latest_record_ranked")
    )
    latest_rec = (
        select(latest_record_subquery)
        .where(latest_record_subquery.c.rn == 1)
        .subquery("latest_rec")
    )

    # 2. Count total assessments per patient
    total_subquery = (
        select(
            HealthRecord.user_id,
            func.count(HealthRecord.id).label("total_assessments")
        )
        .group_by(HealthRecord.user_id)
        .subquery("total_counts")
    )

    # 3. Main patient query
    query = (
        select(
            User.id,
            User.username,
            User.email,
            User.created_at,
            func.coalesce(total_subquery.c.total_assessments, 0).label("total_assessments"),
            latest_rec.c.risk_level.label("latest_risk_level"),
            latest_rec.c.confidence.label("latest_confidence"),
            latest_rec.c.submitted_at.label("last_assessment_date"),
            latest_rec.c.age.label("latest_age"),
        )
        .outerjoin(total_subquery, total_subquery.c.user_id == User.id)
        .outerjoin(latest_rec, latest_rec.c.user_id == User.id)
        .where(User.role == "patient")
    )

    # Search filter (case-insensitive ILIKE across username and email)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(or_(User.username.ilike(term), User.email.ilike(term)))

    # Risk filter (High or Low)
    if risk and risk.strip():
        clean_risk = risk.strip().capitalize()
        if clean_risk in ("High", "Low"):
            query = query.where(latest_rec.c.risk_level == clean_risk)

    # Order by latest assessment date desc (nulls last), then user creation date
    query = query.order_by(
        latest_rec.c.submitted_at.desc().nulls_last(),
        User.created_at.desc()
    )
    query = query.offset(skip).limit(limit)

    rows = db.execute(query).mappings().all()
    return [PatientSummary(**row) for row in rows]


@router.get("/{patient_id}", response_model=PatientDetail)
def get_patient_detail(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves complete clinical profile, latest vitals, and chronological history for a patient (TC-24, TC-25).
    Returns 404 if patient not found or if the requested user is not a patient.
    """
    user = db.query(User).filter(User.id == patient_id).first()
    if not user or user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {patient_id} not found."
        )

    records = (
        db.query(HealthRecord)
        .filter(HealthRecord.user_id == user.id)
        .order_by(HealthRecord.submitted_at.desc())
        .all()
    )

    history = []
    latest_vitals = None

    for idx, r in enumerate(records):
        if idx == 0:
            latest_vitals = {
                "pregnancies": r.pregnancies,
                "glucose": r.glucose,
                "blood_pressure": r.blood_pressure,
                "skin_thickness": r.skin_thickness,
                "insulin": r.insulin,
                "bmi": r.bmi,
                "diabetes_pedigree_function": r.diabetes_pedigree_function,
                "age": r.age,
            }
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

    latest_item = history[0] if history else None

    return PatientDetail(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        total_assessments=len(records),
        latest_risk_level=latest_item.risk_level if latest_item else None,
        latest_confidence=latest_item.confidence if latest_item else None,
        last_assessment_date=latest_item.date if latest_item else None,
        latest_vitals=latest_vitals,
        history=history
    )

