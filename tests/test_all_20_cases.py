"""
Comprehensive Test Suite for CS619 Group S26PROJECTA7FFD
Satisfies all 20 Test Cases (TC-01 to TC-20) from the Design Document & SRS.
"""
import io
import time
import asyncio
import pytest
import httpx
from datetime import datetime, timezone
from app.models import User, HealthRecord, Prediction, MLModel, Feedback, Dataset

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


# TC-01: User Login - Valid credentials
def test_tc01_user_login_valid_credentials(client):
    res = client.post("/api/auth/login", json={
        "username": "test_patient",
        "password": "PatientPass123!"
    })
    assert res.status_code == 200, f"Expected 200 OK, got: {res.text}"
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "test_patient"
    assert data["user"]["role"] == "patient"


# TC-02: User Login - Wrong password
def test_tc02_user_login_wrong_password(client):
    res = client.post("/api/auth/login", json={
        "username": "test_patient",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401, f"Expected 401 Unauthorized, got: {res.text}"
    assert "Invalid username or password" in res.json()["detail"]


# TC-03: Health Data Input - All 8 fields complete -> Saves and triggers prediction
def test_tc03_health_data_input_complete_saves_and_triggers_prediction(client, patient_token, db_session):
    res = client.post(
        "/api/predict",
        json=SAMPLE_HIGH_RISK_VITALS,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 201, f"Expected 201 Created, got: {res.text}"
    data = res.json()
    assert "id" in data
    assert "health_record_id" in data
    assert data["risk_level"] in ["High", "Low"]
    assert data["confidence"] > 0

    # Verify persisted in PostgreSQL
    db_record = db_session.query(HealthRecord).filter(HealthRecord.id == data["health_record_id"]).first()
    assert db_record is not None, "HealthRecord not saved to PostgreSQL database"
    assert db_record.glucose == 148.0


# TC-04: Health Data Input - Missing glucose field -> Rejected with validation error
def test_tc04_health_data_input_missing_glucose_rejected(client, patient_token):
    invalid_data = SAMPLE_HIGH_RISK_VITALS.copy()
    del invalid_data["glucose"]  # missing required glucose

    res = client.post(
        "/api/predict",
        json=invalid_data,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 422, f"Expected 422 Unprocessable Entity, got: {res.status_code}"
    errors = res.json()["detail"]
    assert any("glucose" in err["loc"] for err in errors), "Glucose field error missing"


# TC-05: Diabetes Prediction - Valid complete data -> Risk level High/Low shown with confidence %
def test_tc05_diabetes_prediction_returns_risk_and_confidence(client, patient_token):
    res = client.post(
        "/api/predict",
        json=SAMPLE_LOW_RISK_VITALS,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["risk_level"] in ["High", "Low"]
    assert 0.0 <= data["confidence"] <= 100.0
    assert 0.0 <= data["raw_score"] <= 1.0


# TC-06: Diabetes Prediction - Incomplete data submitted -> Prompt to complete all required fields
def test_tc06_diabetes_prediction_incomplete_data_prompts_completion(client, patient_token):
    res = client.post(
        "/api/predict",
        json={"glucose": 120.0},  # missing 7 required fields
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 422
    data = res.json()
    missing_fields = [err["loc"][-1] for err in data["detail"]]
    assert "bmi" in missing_fields
    assert "blood_pressure" in missing_fields
    assert "age" in missing_fields


# TC-07: Dataset Import - Valid CSV file uploaded by admin -> Stored, available for training
def test_tc07_dataset_import_valid_csv(client, admin_token, db_session):
    csv_content = (
        "Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction,Age,Outcome\n"
        "2,120,70,20,80,25.5,0.4,30,0\n"
        "5,160,85,30,150,32.0,0.6,45,1\n"
    )
    files = {"file": ("test_dataset.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/admin/datasets",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 201, f"Expected 201 Created, got: {res.text}"
    data = res.json()
    assert data["filename"] == "test_dataset.csv"
    assert data["row_count"] == 2
    assert data["validated"] is True

    # Verify stored in DB
    db_ds = db_session.query(Dataset).filter(Dataset.id == data["id"]).first()
    assert db_ds is not None


# TC-08: Dataset Import - Invalid file type (.txt) -> File rejected with error message
def test_tc08_dataset_import_invalid_filetype_rejected(client, admin_token):
    txt_content = "This is a plain text file, not a CSV."
    files = {"file": ("invalid_dataset.txt", io.BytesIO(txt_content.encode("utf-8")), "text/plain")}
    res = client.post(
        "/api/admin/datasets",
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 400, f"Expected 400 Bad Request, got: {res.status_code}"
    assert "Invalid file format" in res.json()["detail"]


# TC-09: Model Training - Admin triggers training with valid data -> All 4 models trained
def test_tc09_model_training_trains_all_4_models(client, admin_token):
    res = client.post(
        "/api/admin/train",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200, f"Expected 200 OK, got: {res.text}"
    data = res.json()
    assert "models_evaluated" in data
    evaluated = data["models_evaluated"]
    assert "Decision Tree" in evaluated
    assert "Logistic Regression" in evaluated
    assert "SVM" in evaluated
    assert "Neural Network" in evaluated


# TC-10: Model Evaluation - Training complete -> Accuracy, Precision, Recall, F1, Confusion Matrix shown
def test_tc10_model_evaluation_metrics_and_confusion_matrix(client, admin_token):
    res = client.post(
        "/api/admin/train",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    for name, metrics in data["models_evaluated"].items():
        assert "accuracy" in metrics, f"Accuracy missing in {name}"
        assert "precision" in metrics, f"Precision missing in {name}"
        assert "recall" in metrics, f"Recall missing in {name}"
        assert "f1_score" in metrics, f"F1 score missing in {name}"
        assert "confusion_matrix" in metrics, f"Confusion matrix missing in {name}"
        assert len(metrics["confusion_matrix"]) == 2, f"Expected 2x2 confusion matrix in {name}"


# TC-11: Best Model Selection - Evaluation complete -> Highest accuracy model selected as active
def test_tc11_best_model_auto_selected_as_active(client, admin_token, db_session):
    res = client.post(
        "/api/admin/train",
        json={},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    data = res.json()
    active_model_name = data["active_model"]

    # Verify that in database, this model has status 'active' and highest or equal accuracy
    active_in_db = db_session.query(MLModel).filter(MLModel.status == "active").first()
    assert active_in_db is not None
    assert active_in_db.name == active_model_name

    all_models = db_session.query(MLModel).all()
    for m in all_models:
        assert active_in_db.accuracy >= m.accuracy or np.isclose(active_in_db.accuracy, m.accuracy, atol=0.01)


# TC-12: Report Generation - User requests report after prediction -> Valid PDF downloaded
def test_tc12_report_download_returns_valid_pdf(client, patient_token):
    # 1. Create prediction first
    pred_res = client.post(
        "/api/predict",
        json=SAMPLE_HIGH_RISK_VITALS,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert pred_res.status_code == 201
    pred_id = pred_res.json()["id"]

    # 2. Download report PDF
    pdf_res = client.get(
        f"/api/report/{pred_id}/pdf",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    content = pdf_res.content
    assert content.startswith(b"%PDF-"), "Downloaded file is not a valid PDF document"
    assert len(content) > 1000, "PDF document unexpectedly empty"


# TC-13: Risk Factor Analysis - Prediction result available -> Top features shown
def test_tc13_risk_factor_bar_chart_data_present(client, patient_token):
    res = client.post(
        "/api/predict",
        json=SAMPLE_HIGH_RISK_VITALS,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert "top_factors" in data
    top_factors = data["top_factors"]
    assert len(top_factors) >= 4, "Expected at least 4 top factors"
    for f in top_factors:
        assert "feature" in f
        assert "impact" in f
        assert "value" in f
        assert "status" in f
        assert 0 <= f["impact"] <= 100


# TC-14: Recommendations - High risk result includes diet, exercise, doctor visit suggestions
def test_tc14_high_risk_recommendations_diet_exercise_doctor(client, patient_token):
    res = client.post(
        "/api/predict",
        json=SAMPLE_HIGH_RISK_VITALS,
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["risk_level"] == "High"
    recs = " ".join(data["recommendations"]).lower()

    # Assert diet, exercise, and doctor/endocrinologist suggestions exist (TC-14)
    assert "diet" in recs or "nutrition" in recs or "glycemic" in recs, "Diet advice missing in high risk result"
    assert "exercise" in recs or "physical" in recs or "aerobic" in recs, "Exercise advice missing in high risk result"
    assert "doctor" in recs or "physician" in recs or "endocrinologist" in recs, "Doctor consultation missing in high risk result"


# TC-15: Health Tracking - Multiple past records exist -> Trend graph records returned
def test_tc15_health_tracking_trend_across_past_records(client, patient_token):
    # Submit two distinct records
    client.post("/api/predict", json=SAMPLE_LOW_RISK_VITALS, headers={"Authorization": f"Bearer {patient_token}"})
    client.post("/api/predict", json=SAMPLE_HIGH_RISK_VITALS, headers={"Authorization": f"Bearer {patient_token}"})

    res = client.get("/api/records", headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 200
    records = res.json()
    assert len(records) >= 2
    for r in records:
        assert "glucose" in r
        assert "bmi" in r
        assert "risk_level" in r
        assert "confidence" in r
        assert "date" in r


# TC-16: Dashboard View - User logged in with predictions -> Summaries and charts render
def test_tc16_dashboard_view_renders_correctly_for_logged_in_user(client, patient_token):
    # 1. Fetch dashboard HTML
    res = client.get("/dashboard")
    assert res.status_code == 200
    assert "Patient Health Dashboard" in res.text

    # 2. Verify API records backing the dashboard charts
    rec_res = client.get("/api/records", headers={"Authorization": f"Bearer {patient_token}"})
    assert rec_res.status_code == 200
    assert isinstance(rec_res.json(), list)


# TC-17: Admin Model Mgmt - Admin opens model panel -> All models, datasets, performance stats visible
def test_tc17_admin_model_panel_shows_all_models_and_stats(client, admin_token):
    # 1. Fetch all models
    models_res = client.get("/api/admin/models", headers={"Authorization": f"Bearer {admin_token}"})
    assert models_res.status_code == 200
    models = models_res.json()
    assert len(models) >= 4
    model_names = [m["name"] for m in models]
    assert "Decision Tree" in model_names
    assert "Logistic Regression" in model_names

    # 2. Fetch datasets
    ds_res = client.get("/api/admin/datasets", headers={"Authorization": f"Bearer {admin_token}"})
    assert ds_res.status_code == 200

    # 3. Fetch performance
    perf_res = client.get("/api/admin/performance", headers={"Authorization": f"Bearer {admin_token}"})
    assert perf_res.status_code == 200
    perf = perf_res.json()
    assert "active_model" in perf
    assert "total_predictions" in perf


# TC-18: Feedback Submission - User submits feedback -> Stored and visible to admin
def test_tc18_feedback_submission_stored_and_visible_to_admin(client, patient_token, admin_token, db_session):
    feedback_text = "The prediction interface is very intuitive and clear for clinical follow-up."
    # 1. Patient submits feedback
    sub_res = client.post(
        "/api/feedback",
        json={"message": feedback_text},
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert sub_res.status_code == 201

    # 2. Admin retrieves feedback list
    admin_res = client.get(
        "/api/admin/feedback",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert admin_res.status_code == 200
    feedbacks = admin_res.json()
    assert any(f["message"] == feedback_text for f in feedbacks), "Submitted feedback not visible to admin"


# TC-19: Performance Test - 10 concurrent prediction requests all complete within 3 seconds
def test_tc19_concurrency_performance_10_requests_under_3_seconds(client, patient_token):
    # Using concurrent threads / requests against the FastAPI app
    import concurrent.futures

    start_time = time.time()

    def make_prediction_request():
        return client.post(
            "/api/predict",
            json=SAMPLE_HIGH_RISK_VITALS,
            headers={"Authorization": f"Bearer {patient_token}"}
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_prediction_request) for _ in range(10)]
        results = [f.result() for f in futures]

    total_duration = time.time() - start_time

    assert len(results) == 10
    for r in results:
        assert r.status_code == 201

    # Performance constraint: 10 concurrent requests must all complete within 3 seconds
    assert total_duration < 3.0, f"10 concurrent requests took {total_duration:.2f}s, exceeding 3.0s SLA!"
    print(f"\n[TC-19 Performance] 10 concurrent requests completed in {total_duration:.3f} seconds (< 3.0s SLA)")


# TC-20: Security Test - Non-admin accessing admin route is denied (403) and redirected to login
def test_tc20_security_non_admin_denied_admin_route(client, patient_token):
    # Patient attempting to access admin route
    res = client.get(
        "/api/admin/models",
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for non-admin, got: {res.status_code}"
    assert "Access denied" in res.json()["detail"]

    # Patient attempting to trigger retraining
    train_res = client.post(
        "/api/admin/train",
        json={},
        headers={"Authorization": f"Bearer {patient_token}"}
    )
    assert train_res.status_code == 403, f"Expected 403 Forbidden for non-admin retraining, got: {train_res.status_code}"

    # Unauthenticated user accessing admin route
    unauth_res = client.get("/api/admin/models")
    assert unauth_res.status_code == 401, f"Expected 401 for unauthenticated user, got: {unauth_res.status_code}"
