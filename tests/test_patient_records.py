"""
Test Cases for Healthcare Provider Patient Records Feature
Satisfies Test Cases TC-21 to TC-28.
Tests patient directory listing, search, risk filtering, patient detail profile,
authorization guards (provider & admin allowed, patient 403, unauthenticated 401),
and GET /patients page routing.
"""
import pytest
from app.models import User, HealthRecord, Prediction
from app.security import get_password_hash, create_access_token
from tests.conftest import TestingSessionLocal

SAMPLE_HIGH_RISK_VITALS = {
    "pregnancies": 6,
    "glucose": 148.0,
    "blood_pressure": 72.0,
    "skin_thickness": 35.0,
    "insulin": 0.0,
    "bmi": 33.6,
    "diabetes_pedigree_function": 0.627,
    "age": 50
}

SAMPLE_LOW_RISK_VITALS = {
    "pregnancies": 1,
    "glucose": 85.0,
    "blood_pressure": 66.0,
    "skin_thickness": 29.0,
    "insulin": 0.0,
    "bmi": 26.6,
    "diabetes_pedigree_function": 0.351,
    "age": 31
}


@pytest.fixture
def seeded_patients_with_assessments(client, patient_token):
    """
    Ensures at least two patient accounts exist with known predictions:
    1. test_patient: Low risk assessment
    2. sarah_jenkins: High risk assessment
    """
    db = TestingSessionLocal()
    try:
        sarah = db.query(User).filter(User.username == "sarah_jenkins").first()
        if not sarah:
            sarah = User(
                username="sarah_jenkins",
                email="sarah.jenkins@example.com",
                password_hash=get_password_hash("PatientPassword123!"),
                role="patient"
            )
            db.add(sarah)
            db.commit()
            db.refresh(sarah)

        sarah_token = create_access_token(subject=sarah.id, role=sarah.role)

        # Submit high risk assessment for sarah
        client.post(
            "/api/predict",
            json=SAMPLE_HIGH_RISK_VITALS,
            headers={"Authorization": f"Bearer {sarah_token}"}
        )

        # Submit low risk assessment for test_patient
        client.post(
            "/api/predict",
            json=SAMPLE_LOW_RISK_VITALS,
            headers={"Authorization": f"Bearer {patient_token}"}
        )

        return {"sarah": sarah}
    finally:
        db.close()


# TC-21: Provider Patient Directory - Provider lists patients (200), only role="patient" users appear
def test_tc21_provider_lists_patients_only_patients_returned(client, provider_token, seeded_patients_with_assessments):
    """TC-21: Verify provider can list patients and results only contain role='patient' users."""
    res = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res.status_code == 200, f"Expected 200 OK, got: {res.text}"
    patients = res.json()
    assert isinstance(patients, list)
    assert len(patients) >= 2

    # Verify no admin or provider is in the returned list
    usernames = [p["username"] for p in patients]
    assert "test_patient" in usernames
    assert "sarah_jenkins" in usernames
    assert "test_admin" not in usernames
    assert "test_provider" not in usernames

    # Verify summary fields
    first = patients[0]
    assert "id" in first
    assert "username" in first
    assert "email" in first
    assert "total_assessments" in first
    assert "latest_risk_level" in first
    assert "latest_confidence" in first


# TC-22: Search Filter - Search by username and by email (case-insensitive)
def test_tc22_patient_search_by_username_and_email(client, provider_token, seeded_patients_with_assessments):
    """TC-22: Verify search parameter filters by username or email case-insensitively."""
    # 1. Search by username prefix
    res_user = client.get(
        "/api/patients?search=sarah",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_user.status_code == 200
    data_user = res_user.json()
    assert len(data_user) >= 1
    assert all("sarah" in p["username"].lower() or "sarah" in p["email"].lower() for p in data_user)

    # 2. Search by email domain/handle
    res_email = client.get(
        "/api/patients?search=jenkins@example",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_email.status_code == 200
    data_email = res_email.json()
    assert len(data_email) == 1
    assert data_email[0]["username"] == "sarah_jenkins"

    # 3. Search with non-matching term returns empty list
    res_none = client.get(
        "/api/patients?search=nonexistent_xyz_999",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_none.status_code == 200
    assert len(res_none.json()) == 0


# TC-23: Risk Filter - Filter by latest risk level (High / Low)
def test_tc23_patient_risk_filter(client, provider_token, seeded_patients_with_assessments):
    """TC-23: Verify filtering patients by latest risk level ('High' or 'Low')."""
    # 1. Filter High risk
    res_high = client.get(
        "/api/patients?risk=High",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_high.status_code == 200
    high_patients = res_high.json()
    assert len(high_patients) >= 1
    for p in high_patients:
        assert p["latest_risk_level"] == "High"

    # 2. Filter Low risk
    res_low = client.get(
        "/api/patients?risk=Low",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_low.status_code == 200
    low_patients = res_low.json()
    assert len(low_patients) >= 1
    for p in low_patients:
        assert p["latest_risk_level"] == "Low"


# TC-24: Patient Detail Profile - Provider opens patient detail (200) with full history
def test_tc24_provider_can_open_patient_detail_with_history(client, provider_token, patient_user, seeded_patients_with_assessments):
    """TC-24: Verify provider can open a patient's detail view including vitals and history."""
    res = client.get(
        f"/api/patients/{patient_user.id}",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res.status_code == 200, f"Expected 200 OK, got: {res.text}"
    detail = res.json()
    assert detail["id"] == patient_user.id
    assert detail["username"] == patient_user.username
    assert detail["email"] == patient_user.email
    assert detail["total_assessments"] >= 1
    assert detail["latest_vitals"] is not None
    assert "glucose" in detail["latest_vitals"]
    assert "bmi" in detail["latest_vitals"]

    # History list check
    assert isinstance(detail["history"], list)
    assert len(detail["history"]) >= 1
    hist_item = detail["history"][0]
    assert "risk_level" in hist_item
    assert "confidence" in hist_item
    assert "model_used" in hist_item
    assert "date" in hist_item


# TC-25: Patient Detail 404 - Unknown ID and non-patient ID return 404
def test_tc25_patient_detail_not_found_or_non_patient(client, provider_token, db_session):
    """TC-25: Verify 404 is returned when patient ID does not exist or user is not a patient."""
    # 1. Non-existent ID
    res_missing = client.get(
        "/api/patients/999999",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_missing.status_code == 404
    assert "not found" in res_missing.json()["detail"].lower()

    # 2. Existing user who is an admin (role != "patient")
    admin = db_session.query(User).filter(User.role == "admin").first()
    assert admin is not None
    res_admin = client.get(
        f"/api/patients/{admin.id}",
        headers={"Authorization": f"Bearer {provider_token}"}
    )
    assert res_admin.status_code == 404
    assert "not found" in res_admin.json()["detail"].lower()


# TC-26: Security & RBAC - Patient gets 403, unauthenticated gets 401
def test_tc26_patients_api_security_rbac(client, patient_token, patient_user):
    """TC-26: Verify patient is denied access (403) and anonymous request is denied (401)."""
    # 1. Patient attempting to list patients -> 403 Forbidden
    res_list_patient = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res_list_patient.status_code == 403
    assert "Access denied" in res_list_patient.json()["detail"]

    # 2. Patient attempting to view another patient's detail -> 403 Forbidden
    res_detail_patient = client.get(
        f"/api/patients/{patient_user.id}",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res_detail_patient.status_code == 403
    assert "Access denied" in res_detail_patient.json()["detail"]

    # 3. Anonymous (no token) -> 401 Unauthorized
    res_unauth_list = client.get("/api/patients")
    assert res_unauth_list.status_code == 401

    res_unauth_detail = client.get(f"/api/patients/{patient_user.id}")
    assert res_unauth_detail.status_code == 401


# TC-27: Page Routing - GET /patients: provider 200, patient redirected, anonymous redirected
def test_tc27_patients_page_routing_and_redirects(client, provider_token, patient_token):
    """TC-27: Verify GET /patients HTML route allows providers and redirects patients/anonymous."""
    browser_headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64)"}

    # 1. Provider with valid cookie -> 200 OK
    res_provider = client.get(
        "/patients",
        headers=browser_headers,
        cookies={"access_token": f"Bearer {provider_token}"},
        follow_redirects=False
    )
    assert res_provider.status_code == 200
    assert "Patient Records" in res_provider.text

    # 2. Patient with cookie -> 303 Redirect to login with access denied
    res_patient = client.get(
        "/patients",
        headers=browser_headers,
        cookies={"access_token": f"Bearer {patient_token}"},
        follow_redirects=False
    )
    assert res_patient.status_code == 303
    assert "login" in res_patient.headers["location"]
    assert "Access" in res_patient.headers["location"] and "denied" in res_patient.headers["location"]

    # 3. Anonymous user -> 303 Redirect to login
    res_anon = client.get(
        "/patients",
        headers=browser_headers,
        follow_redirects=False
    )
    assert res_anon.status_code == 303
    assert "login" in res_anon.headers["location"]


# TC-28: Admin Access - Admin can also list patients and view details
def test_tc28_admin_can_access_patients_api_and_page(client, admin_token, patient_user, seeded_patients_with_assessments):
    """TC-28: Verify administrator role also possesses dual access to patient records."""
    # 1. Admin lists patients
    res_list = client.get(
        "/api/patients",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 2. Admin gets patient detail
    res_detail = client.get(
        f"/api/patients/{patient_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == patient_user.id

    # 3. Admin opens /patients HTML page
    browser_headers = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64)"}
    res_page = client.get(
        "/patients",
        headers=browser_headers,
        cookies={"access_token": f"Bearer {admin_token}"},
        follow_redirects=False
    )
    assert res_page.status_code == 200
