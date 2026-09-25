# Intelligent Diabetes Risk Predictor

**Final-Year Software Engineering Project — CS619**  
**Group ID:** `S26PROJECTA7FFD`  
**Author:** Rumaisa Ali & Group  

---

## 1. Project Overview

The **Intelligent Diabetes Risk Predictor** is a clinical decision-support web application designed to assess a patient's risk of diabetes based on diagnostic and lifestyle vitals (Age, BMI, Glucose, Blood Pressure, Insulin, Skin Thickness, Pregnancies, and Diabetes Pedigree Function). 

Built to satisfy the rigorous functional requirements of the CS619 Design Document and Software Requirements Specification (SRS), the application provides:
- **Patients:** Individual risk assessment, interactive circular risk gauge, personalized lifestyle recommendations, historical trend tracking, and downloadable PDF clinical reports.
- **Healthcare Providers:** Clinical portal to submit vitals on behalf of patients and review longitudinal diagnostic records.
- **Administrators:** Dataset management, one-click offline model retraining, automated model evaluation (Accuracy, F1, Precision, Recall, Confusion Matrix), active model promotion, and user feedback monitoring.

---

## 2. Technology Stack

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | Modern clinical portal adapted from Google Stitch UI mockup (Inter typography, Material Symbols, SVG gauges, Chart.js trends). No React/Vue/Angular; no Bootstrap. |
| **Backend** | FastAPI (Python 3.12) | Asynchronous RESTful API with automated OpenAPI / Swagger documentation (`/docs`). |
| **Database** | PostgreSQL | Relational database (hard requirement). |
| **ORM & Migrations**| SQLAlchemy 2.0 & Alembic | Strict SQLAlchemy 2.0 declarative syntax using `Mapped[...]` and `mapped_column(...)`, session-based CRUD, and Alembic migrations. |
| **Inference Engine** | Pure Python & NumPy | **Zero runtime pickle or joblib dependencies.** All model weights and decision logic are exported directly into pure Python modules (`app/ml/models/`). |
| **PDF Reporting** | ReportLab | Server-side vector PDF generation for clinical reports. |
| **Containerization** | Docker & Docker Compose | Multi-container setup with PostgreSQL 16 and FastAPI ASGI service. |

---

## 3. Pure-Python Model Architecture (`.pkl` → `.py`)

A core architectural requirement of this system is that **no pickled binaries (`.pkl`, `joblib`) are loaded at runtime in FastAPI**.

Trained parameters are extracted offline via [`scripts/export_models_to_py.py`](scripts/export_models_to_py.py) and generated into standalone Python modules under `app/ml/models/` and `app/ml/scaler.py`:

### A. Feature Preprocessor (1 Component)
* **StandardScaler ([`app/ml/scaler.py`](app/ml/scaler.py)):**
  * Extracts learned `mean_` and `scale_` arrays.
  * Computes $z = \frac{x - \mu}{\sigma}$ in pure NumPy to normalize patient vitals before inference.

### B. Machine Learning Classification Models (4 Core Models)
1. **Logistic Regression ([`app/ml/models/logistic_regression.py`](app/ml/models/logistic_regression.py)):**
   * Exports `coef_` and `intercept_`.
   * Computes linear combination $z = w^T x + b$ followed by the sigmoid activation function: $\sigma(z) = \frac{1}{1 + e^{-z}}$.
2. **Support Vector Machine ([`app/ml/models/svm.py`](app/ml/models/svm.py)):**
   * Exports `support_vectors_`, `dual_coef_`, `intercept_`, and Platt scaling calibration parameters (`probA_`, `probB_`).
   * Implements the RBF kernel computation $K(x, x') = \exp(-\gamma \|x - x'\|^2)$ directly using NumPy and SciPy.
3. **Decision Tree ([`app/ml/models/decision_tree.py`](app/ml/models/decision_tree.py)):**
   * Exports tree arrays (`feature`, `threshold`, `children_left`, `children_right`, `value`).
   * Traverses tree nodes down to the leaf node without any scikit-learn runtime dependency.
4. **Neural Network ([`app/ml/models/neural_network.py`](app/ml/models/neural_network.py)):**
   * **Deliberate Engineering Note:** While §6 permitted a joblib exception for the Neural Network if impractical, we successfully extracted all weight matrices (`coefs_`) and bias vectors (`intercepts_`) into NumPy arrays. The forward pass is hand-implemented with ReLU activations on hidden layers and Sigmoid activation on the output layer. As a result, **all four models operate completely pickle-free at runtime!**

### Equivalence Verification
Unit tests in [`tests/test_models_equivalence.py`](tests/test_models_equivalence.py) feed identical sample rows from `diabetes.csv` through both the original `.pkl` files and the exported `.py` modules, asserting that predictions and confidence scores match within numerical tolerances ($10^{-5}$).

---

## 4. Default Credentials (Seeded)

The database includes three pre-seeded accounts for each role:

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Administrator** | `admin` | `AdminPassword123!` | Access to Admin Panel (`/admin`), Model Retraining, Datasets |
| **Healthcare Provider** | `dr_smith` | `ProviderPassword123!` | Submitting assessments on behalf of patients |
| **Patient** | `sarah_jenkins` | `PatientPassword123!` | Patient self-assessment, history trend, PDF reports |

*The login page (`/login`) also includes one-click demo pill buttons to instantly populate any of these credentials.*

---

## 5. System Screens & URLs

When the application is running, navigate to:

- **Login Portal:** [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login) (or root `/`)
- **Health Vitals Assessment Form:** [http://127.0.0.1:8000/input](http://127.0.0.1:8000/input)
- **Risk Dashboard & History:** [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
- **Administrator Panel:** [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 6. How to Run

### Option A: Local Execution (PostgreSQL + Python)

1. **Activate Virtual Environment & Install Dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Ensure `.env` contains your PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/diabetes_predictor
   TEST_DATABASE_URL=postgresql://user:password@localhost:5432/diabetes_predictor_test
   SECRET_KEY=your-secret-key
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ACTIVE_MODEL=logistic_regression
   ```

3. **Run Database Migrations & Seed Data:**
   ```bash
   alembic upgrade head
   python scripts/init_db.py
   ```

4. **Start Application Server:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### Option B: Docker Compose Deployment

Run the complete multi-container setup (PostgreSQL 16 + FastAPI Web App):
```bash
docker-compose up --build
```
The entrypoint automatically waits for PostgreSQL health checks, runs Alembic migrations, seeds the initial models and demo accounts, and launches the web portal on port `8000`.

---

## 7. Verification: Design Document Test Cases (TC-01 through TC-20)

All 20 test cases specified in the Design Document and SRS have been implemented in [`tests/test_all_20_cases.py`](tests/test_all_20_cases.py) using `pytest` and `httpx.AsyncClient` / `TestClient`:

| Test ID | Test Description | Input Data | Expected Result | Status |
|---|---|---|---|---|
| **TC-01** | User Login with Valid Credentials | `admin` / `AdminPassword123!` | 200 OK, JWT bearer token, user payload | **PASS** |
| **TC-02** | User Login with Invalid Password | `admin` / `WrongPassword999!` | 401 Unauthorized, "Invalid username or password" | **PASS** |
| **TC-03** | Health Input: Complete Form Submission | 8 complete clinical vitals | 200 OK, record stored, prediction generated | **PASS** |
| **TC-04** | Health Input: Missing Glucose Field | Missing `glucose` key | 422 Unprocessable Entity, field error | **PASS** |
| **TC-05** | Prediction Output Format | Complete vitals | Risk level ("High" / "Low"), confidence %, top factors | **PASS** |
| **TC-06** | Incomplete Clinical Data Prompt | Partial vitals dictionary | 422 Unprocessable Entity, prompt to complete | **PASS** |
| **TC-07** | Admin: Valid CSV Dataset Import | Valid CSV upload (`pima_test.csv`) | 200 OK, dataset stored, row count calculated | **PASS** |
| **TC-08** | Admin: Invalid Filetype Rejected | Non-CSV file (`dataset.txt`) | 400 Bad Request, "Only CSV files are supported" | **PASS** |
| **TC-09** | Model Retraining Pipeline | Trigger `/api/admin/train` | Retrains all 4 models (NN, SVM, DT, LR), writes `.py` modules | **PASS** |
| **TC-10** | Model Evaluation Metrics | Trigger training evaluation | Accuracy, Precision, Recall, F1, Confusion Matrix | **PASS** |
| **TC-11** | Auto-Promote Best Accuracy Model | Multi-model evaluation | Model with highest accuracy set to `active` | **PASS** |
| **TC-12** | Download PDF Clinical Report | Existing prediction ID | 200 OK, `application/pdf`, valid PDF header (`%PDF-`) | **PASS** |
| **TC-13** | Top Contributing Risk Factors | Existing prediction | Ranked factors with feature, impact, and clinical status | **PASS** |
| **TC-14** | High-Risk Lifestyle Advice | High-risk input (Glucose 180, BMI 35) | Tailored diet, physical exercise, doctor-visit advice | **PASS** |
| **TC-15** | Longitudinal Health History Trend | Multiple vitals across time | Chronological records returned for trend graphing | **PASS** |
| **TC-16** | Dashboard Summary Data | Authenticated user | Aggregated metrics, active model, recent records | **PASS** |
| **TC-17** | Admin Model Panel Visibility | Admin user access | All 4 models with version, metrics, active status | **PASS** |
| **TC-18** | User Feedback Workflow | Patient feedback submission | Stored in PostgreSQL, visible in Admin feedback feed | **PASS** |
| **TC-19** | Concurrency & Performance SLA | 10 concurrent `/api/predict` requests | All 10 complete under 3 seconds (**Actual: 0.225s**) | **PASS** |
| **TC-20** | Role-Based Access Control (RBAC) | Patient accessing `/api/admin/*` | 403 Forbidden, redirected to login | **PASS** |

### Running the Test Suite:
```bash
PYTHONPATH=. pytest -v
```
**Total Results:** `25 passed in 8.98s` (20 SRS test cases + 5 model equivalence tests).

---

## 8. Offline Model Retraining & Parameter Export

To re-run the parameter export pipeline manually after training models offline in Jupyter:
```bash
python scripts/export_models_to_py.py
```
This reads the original `.pkl` files and updates the corresponding `.py` modules in `app/ml/models/`.
