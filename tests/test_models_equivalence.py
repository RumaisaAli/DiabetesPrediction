"""
Model Equivalence Tests
Validates that exported plain-Python model modules produce identical predictions
and confidence scores (within small numerical tolerance) to original pickled sklearn models.
"""
import pytest
import joblib
import numpy as np
import pandas as pd
from app.ml import scaler as exported_scaler
from app.ml.models import (
    logistic_regression as exported_lr,
    svm as exported_svm,
    decision_tree as exported_dt,
    neural_network as exported_nn,
)

@pytest.fixture(scope="module")
def dataset_sample():
    df = pd.read_csv("diabetes.csv")
    # Take first 5 rows for multi-sample validation
    X = df.iloc[:5, :8].values
    y = df.iloc[:5, 8].values
    return X, y

@pytest.fixture(scope="module")
def original_artifacts():
    return {
        "scaler": joblib.load("scaler.pkl"),
        "lr": joblib.load("model_logreg.pkl"),
        "svm": joblib.load("model_svm.pkl"),
        "dt": joblib.load("model_dt.pkl"),
        "nn": joblib.load("model_nn.pkl"),
    }

def test_scaler_equivalence(dataset_sample, original_artifacts):
    X, _ = dataset_sample
    sklearn_scaler = original_artifacts["scaler"]
    for row in X:
        sklearn_scaled = sklearn_scaler.transform([row])[0]
        py_scaled = exported_scaler.transform(row.tolist())
        assert np.allclose(sklearn_scaled, py_scaled, atol=1e-5), "Scaler outputs mismatch!"

def test_logistic_regression_equivalence(dataset_sample, original_artifacts):
    X, _ = dataset_sample
    sklearn_scaler = original_artifacts["scaler"]
    sklearn_lr = original_artifacts["lr"]

    for row in X:
        row_list = row.tolist()
        scaled = sklearn_scaler.transform([row])
        expected_prob = sklearn_lr.predict_proba(scaled)[0, 1]
        expected_class = "High" if expected_prob >= 0.5 else "Low"

        result = exported_lr.predict(row_list)
        assert result["risk_level"] == expected_class, f"LR risk_level mismatch on row: {row_list}"
        assert np.isclose(result["raw_score"], expected_prob, atol=1e-4), f"LR probability mismatch: {result['raw_score']} vs {expected_prob}"

def test_svm_equivalence(dataset_sample, original_artifacts):
    X, _ = dataset_sample
    sklearn_scaler = original_artifacts["scaler"]
    sklearn_svm = original_artifacts["svm"]

    for row in X:
        row_list = row.tolist()
        scaled = sklearn_scaler.transform([row])
        expected_decision = sklearn_svm.decision_function(scaled)[0]
        expected_class = "High" if expected_decision >= 0.0 else "Low"

        result = exported_svm.predict(row_list)
        assert result["risk_level"] == expected_class, f"SVM class mismatch on row: {row_list}"
        # Probability estimated via Platt calibration within tolerance 0.05
        expected_prob = sklearn_svm.predict_proba(scaled)[0, 1]
        assert np.isclose(result["raw_score"], expected_prob, atol=0.05), f"SVM prob mismatch: {result['raw_score']} vs {expected_prob}"

def test_decision_tree_equivalence(dataset_sample, original_artifacts):
    X, _ = dataset_sample
    sklearn_scaler = original_artifacts["scaler"]
    sklearn_dt = original_artifacts["dt"]

    for row in X:
        row_list = row.tolist()
        scaled = sklearn_scaler.transform([row])
        expected_prob = sklearn_dt.predict_proba(scaled)[0, 1]
        expected_class = "High" if expected_prob >= 0.5 else "Low"

        result = exported_dt.predict(row_list)
        assert result["risk_level"] == expected_class, f"DT class mismatch on row: {row_list}"
        assert np.isclose(result["raw_score"], expected_prob, atol=1e-5), f"DT prob mismatch: {result['raw_score']} vs {expected_prob}"

def test_neural_network_equivalence(dataset_sample, original_artifacts):
    X, _ = dataset_sample
    sklearn_scaler = original_artifacts["scaler"]
    sklearn_nn = original_artifacts["nn"]

    for row in X:
        row_list = row.tolist()
        scaled = sklearn_scaler.transform([row])
        expected_prob = sklearn_nn.predict_proba(scaled)[0, 1]
        expected_class = "High" if expected_prob >= 0.5 else "Low"

        result = exported_nn.predict(row_list)
        assert result["risk_level"] == expected_class, f"NN class mismatch on row: {row_list}"
        assert np.isclose(result["raw_score"], expected_prob, atol=1e-4), f"NN prob mismatch: {result['raw_score']} vs {expected_prob}"
