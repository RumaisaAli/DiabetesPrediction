"""
Model Retraining and Evaluation Pipeline
Ports notebook training logic, trains all 4 models, evaluates metrics,
triggers the .pkl -> .py export step, and promotes the best model to active.
"""
import os
import importlib
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
from sqlalchemy.orm import Session
from app.models import MLModel
import joblib
from scripts.export_models_to_py import (
    export_scaler,
    export_logistic_regression,
    export_svm,
    export_decision_tree,
    export_neural_network,
)
import app.ml.inference as inference_service

REQUIRED_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
    "Outcome",
]

MODULE_MAP = {
    "Decision Tree": "app.ml.models.decision_tree",
    "Logistic Regression": "app.ml.models.logistic_regression",
    "SVM": "app.ml.models.svm",
    "Neural Network": "app.ml.models.neural_network",
}


def retrain_models(dataset_path: str, db: Session) -> dict:
    """
    Retrains all four models on the uploaded/specified dataset, computes performance metrics,
    exports parameters to .py files, updates database records, and sets the best model as active.
    """
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")

    # 1. Load dataset
    df = pd.read_csv(dataset_path)

    # Validate columns
    col_map = {c.lower(): c for c in df.columns}
    missing = [c for c in REQUIRED_COLUMNS if c.lower() not in col_map]
    if missing:
        raise ValueError(f"Uploaded CSV is missing required clinical columns: {missing}")

    # Standardize column naming
    clean_cols = [col_map[c.lower()] for c in REQUIRED_COLUMNS]
    df = df[clean_cols]
    df.columns = REQUIRED_COLUMNS

    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]

    # 2. Train / Test split
    class_counts = y.value_counts()
    can_stratify = (len(class_counts) > 1) and (class_counts.min() >= 2) and (len(df) >= 10)
    test_size = 0.2 if len(df) >= 10 else 0.5
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y if can_stratify else None
    )

    # 3. Fit Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save scaler artifact
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    scaler_pkl = os.path.join(root_dir, "scaler.pkl")
    joblib.dump(scaler, scaler_pkl)
    export_scaler(scaler_pkl, os.path.join(root_dir, "app", "ml", "scaler.py"))

    # 4. Train all 4 models
    models = {
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
        "SVM": SVC(kernel="rbf", probability=True, random_state=42),
        "Neural Network": MLPClassifier(max_iter=500, random_state=42),
    }

    results = {}
    best_acc = -1.0
    best_name = "Decision Tree"

    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        preds = model.predict(X_test_scaled)

        acc = float(accuracy_score(y_test, preds) * 100.0)
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        cm = confusion_matrix(y_test, preds).tolist()

        results[name] = {
            "accuracy": round(acc, 2),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
        }

        # Save and export model to .py
        if name == "Decision Tree":
            pkl_path = os.path.join(root_dir, "model_dt.pkl")
            joblib.dump(model, pkl_path)
            export_decision_tree(pkl_path, os.path.join(root_dir, "app", "ml", "models", "decision_tree.py"))
        elif name == "Logistic Regression":
            pkl_path = os.path.join(root_dir, "model_logreg.pkl")
            joblib.dump(model, pkl_path)
            export_logistic_regression(pkl_path, os.path.join(root_dir, "app", "ml", "models", "logistic_regression.py"))
        elif name == "SVM":
            pkl_path = os.path.join(root_dir, "model_svm.pkl")
            joblib.dump(model, pkl_path)
            export_svm(pkl_path, os.path.join(root_dir, "app", "ml", "models", "svm.py"))
        elif name == "Neural Network":
            pkl_path = os.path.join(root_dir, "model_nn.pkl")
            joblib.dump(model, pkl_path)
            export_neural_network(pkl_path, os.path.join(root_dir, "app", "ml", "models", "neural_network.py"))

        if acc > best_acc:
            best_acc = acc
            best_name = name

    # 5. Reload modules in running inference service so runtime uses newly trained parameters
    try:
        from app.ml.models import decision_tree, logistic_regression, svm, neural_network
        importlib.reload(decision_tree)
        importlib.reload(logistic_regression)
        importlib.reload(svm)
        importlib.reload(neural_network)
        inference_service.MODEL_REGISTRY.update({
            "Decision Tree": decision_tree,
            "Logistic Regression": logistic_regression,
            "SVM": svm,
            "Neural Network": neural_network,
            "app.ml.models.decision_tree": decision_tree,
            "app.ml.models.logistic_regression": logistic_regression,
            "app.ml.models.svm": svm,
            "app.ml.models.neural_network": neural_network,
        })
    except Exception as e:
        print(f"Warning reloading model modules: {e}")

    # 6. Update DB models table and set highest accuracy model active
    now = datetime.now(timezone.utc)
    for name, metrics in results.items():
        db_model = db.query(MLModel).filter(MLModel.name == name).first()
        status_val = "active" if name == best_name else "trained"
        if db_model:
            db_model.accuracy = metrics["accuracy"]
            db_model.precision = metrics["precision"]
            db_model.recall = metrics["recall"]
            db_model.f1_score = metrics["f1_score"]
            db_model.status = status_val
            db_model.trained_at = now
        else:
            db.add(MLModel(
                name=name,
                version="1.0.0",
                accuracy=metrics["accuracy"],
                precision=metrics["precision"],
                recall=metrics["recall"],
                f1_score=metrics["f1_score"],
                status=status_val,
                trained_at=now,
                module_path=MODULE_MAP[name]
            ))

    db.commit()

    return {
        "message": f"Successfully trained and evaluated all 4 models. Best model '{best_name}' ({best_acc:.2f}%) set as active.",
        "dataset_used": os.path.basename(dataset_path),
        "models_evaluated": results,
        "active_model": best_name,
        "best_accuracy": round(best_acc, 2),
    }
