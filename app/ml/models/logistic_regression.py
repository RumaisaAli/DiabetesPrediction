"""
Auto-generated Logistic Regression module from model_logreg.pkl.
Pure-Python / NumPy forward pass without sklearn dependency at runtime.
"""
import numpy as np
from app.ml.scaler import transform

COEF = np.array([[0.37317821047635, 1.1441512736875823, -0.19763683090179182, 0.06653497138971799, -0.12730823048049883, 0.7138934066356618, 0.255526746692169, 0.18417898610631533]], dtype=np.float64)
INTERCEPT = np.array([-0.8749604861204673], dtype=np.float64)
CLASSES = [0, 1]
FEATURE_NAMES = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

FEATURE_LABELS = {'Pregnancies': 'Pregnancies', 'Glucose': 'Blood Glucose Level', 'BloodPressure': 'Blood Pressure', 'SkinThickness': 'Skin Fold Thickness', 'Insulin': 'Serum Insulin', 'BMI': 'Body Mass Index', 'DiabetesPedigreeFunction': 'Diabetes Pedigree Function', 'Age': 'Patient Age'}
NORMAL_RANGES = {'Pregnancies': (0, 2), 'Glucose': (70, 99), 'BloodPressure': (60, 80), 'SkinThickness': (10, 25), 'Insulin': (16, 166), 'BMI': (18.5, 24.9), 'DiabetesPedigreeFunction': (0.0, 0.5), 'Age': (21, 45)}


def _compute_factors(raw_features: list[float], scaled: np.ndarray) -> list[dict]:
    weights = np.maximum(0.0, COEF[0])
    # Fallback to absolute value if weight is negative to capture risk impact
    weights = np.where(weights > 0, weights, np.abs(COEF[0]) * 0.5)
    impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        raw_val = float(raw_features[i])
        z_val = float(scaled[i])
        w = float(weights[i])
        score = max(0.0, z_val * w)
        low, high = NORMAL_RANGES.get(name, (0, 100))
        if raw_val > high:
            status = "Elevated" if raw_val <= high * 1.25 else "High"
        elif raw_val < low:
            status = "Low"
        else:
            status = "Optimal"
        impacts.append({
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": round(raw_val, 2),
            "score": score,
            "status": status
        })
    total = sum(item["score"] for item in impacts)
    for item in impacts:
        item["impact"] = round((item["score"] / total * 100) if total > 0 else (100.0 / len(impacts)), 1)
        del item["score"]
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts


def predict(features: list[float]) -> dict:
    """
    Predict diabetes risk for given 8 clinical features.
    Returns:
        dict: {"risk_level": "High"|"Low", "confidence": float, "raw_score": float, "top_factors": list}
    """
    scaled = transform(features)
    z = np.dot(scaled, COEF[0]) + INTERCEPT[0]
    prob = float(1.0 / (1.0 + np.exp(-z)))
    risk_level = "High" if prob >= 0.5 else "Low"
    confidence = float(prob if prob >= 0.5 else 1.0 - prob)
    factors = _compute_factors(features, scaled)
    return {
        "risk_level": risk_level,
        "confidence": round(confidence * 100.0, 2),
        "raw_score": round(prob, 4),
        "top_factors": factors
    }
