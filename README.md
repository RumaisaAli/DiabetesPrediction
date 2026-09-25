# Intelligent Diabetes Risk Predictor

**Final-Year Software Engineering Project — CS619**  
**Group ID:** `S26PROJECTA7FFD`  
**Author:** Rumaisa Ali & Group  

---

> [!IMPORTANT]
> ### Clinical Decision-Support & Medical Disclaimer
> The **Intelligent Diabetes Risk Predictor** is developed strictly for **clinical decision-support and educational purposes**. The system estimates diabetes risk probabilities based on diagnostic and lifestyle vitals, but **it is NOT a substitute for professional medical diagnosis, clinical judgment, or laboratory-confirmed diagnostic testing**. Patients and healthcare providers must consult licensed medical professionals for definitive diagnoses, individualized treatment plans, or prescription adjustments.

---

## 1. System Overview

The **Intelligent Diabetes Risk Predictor** is a full-stack clinical decision-support web application that evaluates diabetes risk based on 8 diagnostic parameters from the Pima Indians Diabetes dataset:
- Pregnancies
- Glucose Concentration
- Blood Pressure (Diastolic)
- Skin Fold Thickness (Triceps)
- 2-Hour Serum Insulin
- Body Mass Index (BMI)
- Diabetes Pedigree Function
- Age

Built strictly to satisfy the functional requirements of the CS619 Design Document and Software Requirements Specification (SRS), the platform provides dedicated role-based portals for **Patients**, **Healthcare Providers**, and **System Administrators**.

---

## 2. System Architecture

The platform follows a modern, decoupled client-server architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                 Client Layer (Browser)                      │
│   Vanilla HTML5 / Modern CSS3 / Vanilla ES6 JavaScript      │
│   • Adapted Clinical Stitch UI    • Chart.js Trends         │
│   • SVG Dynamic Risk Gauges       • Session & RBAC Guards   │
└──────────────────────────────▲──────────────────────────────┘
                               │ HTTP / JSON REST APIs
┌──────────────────────────────▼──────────────────────────────┐
│                 Backend Layer (FastAPI)                     │
│   • Asynchronous REST API Engine   • JWT & Cookie Auth      │
│   • Server Route & Role Guards     • ReportLab PDF Service  │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
┌──────────────▼──────────────┐ ┌──────────────▼──────────────┐
│   Pure-Python ML Engine     │ │   Persistence (PostgreSQL)  │
│   • StandardScaler (NumPy)  │ │   • SQLAlchemy 2.0 ORM      │
│   • 4 Hand-Crafted Models   │ │   • Alembic Migrations      │
│   • Zero Runtime Pickle     │ │   • Relational Integrity    │
└─────────────────────────────┘ └─────────────────────────────┘
```

### Key Architectural Pillars:
1. **Frontend:** Zero-framework Vanilla HTML5/CSS3/JavaScript ensuring high performance, zero build-step overhead, and full compliance with project constraints.
2. **Backend:** Asynchronous FastAPI service leveraging Pydantic v2 schemas and OpenAPI specification.
3. **Zero-Pickle Runtime ML:** High-security inference engine executing purely via mathematical NumPy routines in plain Python—completely eliminating arbitrary code execution risks from runtime pickle/joblib deserialization.
4. **Relational Persistence:** PostgreSQL with strict SQLAlchemy 2.0 `Mapped` and `mapped_column` type annotations and versioned Alembic schema migrations.

---

## 3. Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Backend Framework** | Python 3.12 / FastAPI | Asynchronous RESTful API engine with automatic OpenAPI documentation |
| **ORM & Migrations** | SQLAlchemy 2.0 & Alembic | Strict declarative database models and schema revision control |
| **Database** | PostgreSQL 15+ | Relational data persistence for users, health records, predictions, and models |
| **ML Inference** | Pure Python & NumPy | In-memory mathematical evaluation of models without pickle or joblib |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript | Lightweight, dependency-free clinical user interface (Inter font, Material Symbols) |
| **Visualizations** | Chart.js & Dynamic SVG | Interactive longitudinal health trends and animated risk gauges |
| **Document Generation** | ReportLab | Server-side vector PDF generation for clinical assessment reports |
| **Containerization** | Docker & Docker Compose | Multi-service orchestration (FastAPI + PostgreSQL) |
| **Testing** | Pytest, AnyIO, Starlette TestClient | Automated test suite verifying all 20 SRS test cases and ML equivalence |

---

## 4. Machine-Learning Workflow & Supported Models

The predictive workflow runs entirely offline for training and exports deterministic, self-contained Python modules for runtime evaluation:

```
[Training Data: diabetes.csv] 
         │
         ▼
[Offline Training & Evaluation] ──► [scripts/export_models_to_py.py]
                                                   │
         ┌─────────────────────────────────────────┴─────────────────────────────────────────┐
         ▼                                         ▼                                         ▼
  app/ml/scaler.py                     app/ml/models/*.py                          app/models/ml_model.py
  (StandardScaler)                     (Pure Python Inference)                     (DB Metrics & Status)
```

### A. Preprocessing Pipeline
- **StandardScaler ([`app/ml/scaler.py`](app/ml/scaler.py)):** Normalizes input vitals using precomputed mean ($\mu$) and standard deviation ($\sigma$) vectors:
  $$z = \frac{x - \mu}{\sigma}$$

### B. Supported Classification Models
All 4 models are implemented as pure-Python forward passes under [`app/ml/models/`](app/ml/models/):

1. **Logistic Regression ([`app/ml/models/logistic_regression.py`](app/ml/models/logistic_regression.py)):**
   - Computes log-odds linear dot product $z = w^T x + b$.
   - Yields risk probability via sigmoid activation: $\sigma(z) = \frac{1}{1 + e^{-z}}$.
2. **Support Vector Machine ([`app/ml/models/svm.py`](app/ml/models/svm.py)):**
   - Radial Basis Function (RBF) kernel evaluation: $K(x_i, x) = \exp(-\gamma \|x_i - x\|^2)$ against support vectors.
   - Calibrated posterior probabilities computed via Platt scaling parameters ($A, B$).
3. **Decision Tree ([`app/ml/models/decision_tree.py`](app/ml/models/decision_tree.py)):**
   - Recursive binary decision path traversal using feature index and threshold arrays down to leaf probability distributions.
4. **Neural Network / Multi-Layer Perceptron ([`app/ml/models/neural_network.py`](app/ml/models/neural_network.py)):**
   - Multi-layer forward pass with hidden layer ReLU activations and output Sigmoid activation using extracted weight matrices and bias vectors.

### C. Retraining & Auto-Promotion
Administrators can initiate model retraining from the Admin Panel. The system evaluates all 4 algorithms against standard metrics (Accuracy, Precision, Recall, F1-Score, and Confusion Matrix), stores evaluation history, and automatically promotes the highest-accuracy model to **active** status.

---

## 5. User Roles & Main Features

### User Roles
- **Patient:** Self-service portal to submit vitals, view instantaneous risk results, analyze contributing risk factors, track health metrics over time, and download formal clinical reports.
- **Healthcare Provider (Doctor):** Clinical workflow to input diagnostic records for patients and monitor patient risk progression.
- **Administrator:** System-level oversight, including dataset CSV uploads, model retraining, active algorithm promotion, and user feedback review.

### Main Features
- **Real-Time Risk Scoring:** Instant classification into Low, Moderate, or High Risk with an exact confidence percentage.
- **Contributing Risk Factor Analysis:** Visual breakdown pinpointing specific vitals (e.g., elevated Glucose or BMI) driving the risk score.
- **Personalized Clinical Recommendations:** Evidence-based lifestyle guidance spanning diet, physical exercise, and recommended clinical follow-ups.
- **Longitudinal Trend Analytics:** Interactive Chart.js visualizations showing historic vitals and risk evolution across assessments.
- **Downloadable Clinical PDF Reports:** Clean, printable medical summaries containing patient vitals, active model details, risk breakdown, and timestamp.
- **Robust Security & Navigation Guards:** JWT session handling, anti-caching HTTP headers (`Cache-Control: no-store`), server-enforced route protection, and bfcache guards on logout.

---

## 6. Project Structure

```
DiabetesPrediction/
├── app/
│   ├── api/                     # REST API route handlers
│   │   ├── admin.py             # Model retraining, datasets, feedback
│   │   ├── auth.py              # Login, registration, token verification
│   │   ├── health_records.py    # Health input and patient vitals
│   │   ├── predict.py           # ML inference endpoint
│   │   └── reports.py           # Vector PDF report generation
│   ├── ml/                      # Machine learning engine
│   │   ├── models/              # Pure Python models (LR, SVM, DT, NN)
│   │   ├── model_runner.py      # Dynamic active model loader & evaluator
│   │   └── scaler.py            # Pure Python StandardScaler
│   ├── models/                  # SQLAlchemy 2.0 ORM entities
│   │   ├── user.py              # Users and roles
│   │   ├── health_record.py     # Patient vitals records
│   │   ├── prediction.py        # Prediction results and factors
│   │   ├── ml_model.py          # Model performance and status metadata
│   │   ├── dataset.py           # Uploaded training datasets
│   │   └── feedback.py          # User feedback entries
│   ├── static/                  # Vanilla frontend assets
│   │   ├── login.html           # Authentication portal
│   │   ├── input.html           # Clinical vitals input form
│   │   ├── dashboard.html       # Patient results, gauge, trends, reports
│   │   ├── admin.html           # Administrator panel & model controls
│   │   ├── css/styles.css       # Core clinical design system
│   │   └── js/                  # Vanilla ES6 JavaScript modules
│   ├── config.py                # Environment settings & configuration
│   ├── database.py              # SQLAlchemy engine & session factory
│   ├── main.py                  # FastAPI application entrypoint
│   └── security.py              # Password hashing & JWT token handling
├── migrations/                  # Alembic database migrations
├── scripts/
│   ├── export_models_to_py.py   # Offline model parameter exporter
│   └── init_db.py               # Database initialization & seed script
├── tests/
│   ├── conftest.py              # Test fixtures & test DB setup
│   ├── test_all_20_cases.py     # Full SRS test suite (TC-01 to TC-20)
│   └── test_models_equivalence.py # Model numerical parity verification
├── .env.example                 # Example environment configuration
├── docker-compose.yml           # Multi-container Docker orchestration
├── Dockerfile                   # Application container definition
├── docker-entrypoint.sh         # Container boot & migration script
├── requirements.txt             # Python runtime dependencies
└── README.md                    # Project documentation
```

---

## 7. Installation & Deployment Instructions

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ (running locally or via container)
- Docker & Docker Compose (optional, for containerized run)

---

### Option A: Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/RumaisaAli/DiabetesPrediction.git
   cd DiabetesPrediction
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to supply your local PostgreSQL database credentials and a strong random `SECRET_KEY`.

5. **Run database migrations and seed baseline data:**
   ```bash
   alembic upgrade head
   python scripts/init_db.py
   ```

6. **Start the application server:**
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your web browser.

---

### Option B: Docker Compose Deployment

Run the complete multi-container stack with a single command:
```bash
docker compose up --build
```

The container entrypoint automatically:
1. Waits for PostgreSQL to become healthy.
2. Applies Alembic migrations (`alembic upgrade head`).
3. Seeds baseline models and demo users (`scripts/init_db.py`).
4. Starts Uvicorn on port `8000`.

Access the application at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 8. Configuration & Security Considerations

> [!WARNING]
> ### Security & Secret Management Notice
> Demo accounts and default credentials listed below are provided strictly for local development, academic demonstration, and automated test execution. **Do NOT use demo credentials, sample database URLs, or default secret keys in a production environment.**
>
> In production environments:
> - Generate a cryptographically secure random `SECRET_KEY` (e.g., `openssl rand -hex 32`).
> - Store database credentials, JWT secrets, and sensitive tokens exclusively in securely managed environment variables.
> - Enforce HTTPS/TLS encryption to protect credentials and medical vitals in transit.

### Local Demo Credentials (Seeded)

| Role | Username / Email | Password | Access Privileges |
|---|---|---|---|
| **System Administrator** | `admin` / `admin@gluco.ai` | `AdminPassword123!` | Model Retraining, Dataset Management, Feedback, System URLs |
| **Healthcare Provider** | `dr_smith` / `provider@gluco.ai` | `ProviderPassword123!` | Clinical Input for Patients, History Review |
| **Patient** | `sarah_jenkins` / `patient@gluco.ai` | `PatientPassword123!` | Self-Assessment, Dashboard, Trend Tracking, PDF Download |

*(The login page at `/login` includes 1-click demo buttons to automatically populate these credentials).*

---

## 9. API Reference & Interactive Documentation

FastAPI automatically generates comprehensive interactive documentation:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Primary REST Endpoints

| Category | Method | Endpoint | Access Role | Description |
|---|---|---|---|---|
| **Auth** | `POST` | `/api/auth/login` | Public | Authenticates credentials and returns JWT bearer token / session cookie |
| **Auth** | `POST` | `/api/auth/register` | Public | Registers a new patient user account |
| **Auth** | `GET` | `/api/auth/me` | Authenticated | Retrieves profile information for current session |
| **Prediction** | `POST` | `/api/predict` | Authenticated | Evaluates 8 patient vitals against active ML model and returns risk |
| **Records** | `POST` | `/api/health-records` | Authenticated | Persists clinical vitals record and triggers assessment |
| **Records** | `GET` | `/api/health-records/patient/{id}` | Authenticated | Retrieves longitudinal vitals history for trend analysis |
| **Reports** | `GET` | `/api/reports/download/{id}` | Authenticated | Generates and downloads formal ReportLab vector PDF report |
| **Models** | `GET` | `/api/active-model` | Public | Returns current active model metadata and accuracy |
| **Admin** | `GET` | `/api/admin/models` | Admin Only | Lists all trained models, versions, metrics, and active states |
| **Admin** | `POST` | `/api/admin/models/{id}/activate` | Admin Only | Promotes a specific model to active production status |
| **Admin** | `POST` | `/api/admin/train` | Admin Only | Triggers offline retraining of all 4 models and auto-promotes best |
| **Admin** | `POST` | `/api/admin/datasets` | Admin Only | Uploads and registers new training dataset CSV |
| **Feedback** | `POST` | `/api/feedback` | Authenticated | Submits patient feedback on assessment accuracy |

---

## 10. Automated Testing & Verification

The project includes an end-to-end automated test suite verifying compliance with the CS619 Design Document, SRS requirements, and model mathematical equivalence:

### Test Suite Execution
```bash
PYTHONPATH=. pytest tests/ -v
```

### Coverage Overview:
- **SRS Functional Test Cases (TC-01 through TC-20):**
  - `TC-01`: Valid authentication and token issuance.
  - `TC-02`: Rejection of invalid passwords with 401 Unauthorized.
  - `TC-03`: Health data complete submission and record persistence.
  - `TC-04`: Missing required vitals validation (422 Unprocessable Entity).
  - `TC-05`: Risk prediction output format (Risk Level, Confidence %, Factors).
  - `TC-06`: Incomplete clinical input handling.
  - `TC-07`: Valid CSV dataset import and row indexing.
  - `TC-08`: Non-CSV dataset upload rejection.
  - `TC-09`: Automated model training across all 4 algorithms.
  - `TC-10`: Comprehensive evaluation metrics calculation.
  - `TC-11`: Automatic promotion of highest-accuracy model.
  - `TC-12`: ReportLab vector PDF generation and HTTP response headers.
  - `TC-13`: Ranked risk factor breakdown generation.
  - `TC-14`: High-risk lifestyle recommendations.
  - `TC-15`: Longitudinal history retrieval for trend charting.
  - `TC-16`: Patient dashboard summary aggregation.
  - `TC-17`: Admin model management panel visibility.
  - `TC-18`: User feedback recording and administration view.
  - `TC-19`: High-concurrency performance SLA (10 requests under 3 seconds).
  - `TC-20`: Role-Based Access Control security enforcement.
- **Model Equivalence Tests (`tests/test_models_equivalence.py`):**
  - Confirms zero-divergence ($\le 10^{-5}$) between exported pure-Python modules and original scikit-learn models across test samples.

**Result:** `25 passed in ~12 seconds` (100% test pass rate).
