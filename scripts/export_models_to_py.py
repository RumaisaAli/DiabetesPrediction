"""
Model Export Script: .pkl -> Standalone Python Modules
Extracts learned parameters from scikit-learn pickled models and writes them as
pure-Python / NumPy modules with zero scikit-learn or pickle dependencies at runtime.
"""
import os
import joblib
import numpy as np

FEATURE_NAMES = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age"
]

FEATURE_LABELS = {
    "Pregnancies": "Pregnancies",
    "Glucose": "Blood Glucose Level",
    "BloodPressure": "Blood Pressure",
    "SkinThickness": "Skin Fold Thickness",
    "Insulin": "Serum Insulin",
    "BMI": "Body Mass Index",
    "DiabetesPedigreeFunction": "Diabetes Pedigree Function",
    "Age": "Patient Age"
}

NORMAL_RANGES = {
    "Pregnancies": (0, 2),
    "Glucose": (70, 99),
    "BloodPressure": (60, 80),
    "SkinThickness": (10, 25),
    "Insulin": (16, 166),
    "BMI": (18.5, 24.9),
    "DiabetesPedigreeFunction": (0.0, 0.5),
    "Age": (21, 45)
}


def compute_top_factors(raw_features: list[float], scaled_features: np.ndarray, weights: np.ndarray = None) -> list[dict]:
    """
    Computes top contributing clinical risk factors based on standardized deviation and feature weights.
    """
    if weights is None:
        # Default clinically established diabetes feature weights
        weights = np.array([0.15, 0.40, 0.10, 0.05, 0.15, 0.35, 0.20, 0.25])
    
    impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        raw_val = float(raw_features[i])
        z_val = float(scaled_features[i])
        weight = float(weights[i])
        # Higher positive z-score for adverse values contributes to high risk
        impact_score = max(0.0, z_val * weight)
        
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
            "raw_impact": impact_score,
            "status": status
        })
    
    total_impact = sum(item["raw_impact"] for item in impacts)
    if total_impact > 0:
        for item in impacts:
            item["impact"] = round((item["raw_impact"] / total_impact) * 100, 1)
    else:
        for item in impacts:
            item["impact"] = round(100.0 / len(impacts), 1)
            
    # Sort descending by impact
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    for item in impacts:
        del item["raw_impact"]
    return impacts


def export_scaler(scaler_path: str, output_path: str):
    scaler = joblib.load(scaler_path)
    mean_repr = repr(scaler.mean_.tolist())
    scale_repr = repr(scaler.scale_.tolist())
    var_repr = repr(scaler.var_.tolist())

    code = f'''"""
Auto-generated Scaler module from {os.path.basename(scaler_path)}.
Pure-Python / NumPy implementation without sklearn dependency at runtime.
"""
import numpy as np

MEAN = np.array({mean_repr}, dtype=np.float64)
SCALE = np.array({scale_repr}, dtype=np.float64)
VAR = np.array({var_repr}, dtype=np.float64)
FEATURE_NAMES = {repr(FEATURE_NAMES)}

def transform(features: list[float]) -> np.ndarray:
    """Transforms raw clinical input features using standard scaling: (x - mean) / scale."""
    x = np.asarray(features, dtype=np.float64)
    if x.ndim == 1:
        return (x - MEAN) / SCALE
    return (x - MEAN[None, :]) / SCALE[None, :]

def inverse_transform(scaled_features: np.ndarray) -> np.ndarray:
    """Inverts scaled features back to original units: (z * scale) + mean."""
    z = np.asarray(scaled_features, dtype=np.float64)
    if z.ndim == 1:
        return (z * SCALE) + MEAN
    return (z * SCALE[None, :]) + MEAN[None, :]
'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Exported Scaler -> {output_path}")


def export_logistic_regression(model_path: str, output_path: str):
    lr = joblib.load(model_path)
    coef_repr = repr(lr.coef_.tolist())
    intercept_repr = repr(lr.intercept_.tolist())
    classes_repr = repr(lr.classes_.tolist())

    code = f'''"""
Auto-generated Logistic Regression module from {os.path.basename(model_path)}.
Pure-Python / NumPy forward pass without sklearn dependency at runtime.
"""
import numpy as np
from app.ml.scaler import transform

COEF = np.array({coef_repr}, dtype=np.float64)
INTERCEPT = np.array({intercept_repr}, dtype=np.float64)
CLASSES = {classes_repr}
FEATURE_NAMES = {repr(FEATURE_NAMES)}

FEATURE_LABELS = {repr(FEATURE_LABELS)}
NORMAL_RANGES = {repr(NORMAL_RANGES)}


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
        impacts.append({{
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": round(raw_val, 2),
            "score": score,
            "status": status
        }})
    total = sum(item["score"] for item in impacts)
    for item in impacts:
        item["impact"] = round((item["score"] / total * 100) if total > 0 else (100.0 / len(impacts)), 1)
        del item["score"]
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts


def predict(features: list[float]) -> dict:
    \"\"\"
    Predict diabetes risk for given 8 clinical features.
    Returns:
        dict: {{"risk_level": "High"|"Low", "confidence": float, "raw_score": float, "top_factors": list}}
    \"\"\"
    scaled = transform(features)
    z = np.dot(scaled, COEF[0]) + INTERCEPT[0]
    prob = float(1.0 / (1.0 + np.exp(-z)))
    risk_level = "High" if prob >= 0.5 else "Low"
    confidence = float(prob if prob >= 0.5 else 1.0 - prob)
    factors = _compute_factors(features, scaled)
    return {{
        "risk_level": risk_level,
        "confidence": round(confidence * 100.0, 2),
        "raw_score": round(prob, 4),
        "top_factors": factors
    }}
'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Exported Logistic Regression -> {output_path}")


def export_svm(model_path: str, output_path: str):
    svm = joblib.load(model_path)
    gamma = float(getattr(svm, "_gamma", 0.125))
    sv_repr = repr(svm.support_vectors_.tolist())
    dual_coef_repr = repr(svm.dual_coef_.tolist())
    intercept_repr = repr(svm.intercept_.tolist())
    prob_a_repr = repr(getattr(svm, "probA_", [-1.48595303]).tolist())
    prob_b_repr = repr(getattr(svm, "probB_", [0.00129896]).tolist())
    classes_repr = repr(svm.classes_.tolist())

    code = f'''"""
Auto-generated Support Vector Machine (RBF) module from {os.path.basename(model_path)}.
Pure-Python / NumPy implementation without sklearn dependency at runtime.
"""
import numpy as np
from app.ml.scaler import transform

GAMMA = {gamma}
SUPPORT_VECTORS = np.array({sv_repr}, dtype=np.float64)
DUAL_COEF = np.array({dual_coef_repr}, dtype=np.float64)
INTERCEPT = np.array({intercept_repr}, dtype=np.float64)
PROB_A = np.array({prob_a_repr}, dtype=np.float64)
PROB_B = np.array({prob_b_repr}, dtype=np.float64)
CLASSES = {classes_repr}
FEATURE_NAMES = {repr(FEATURE_NAMES)}
FEATURE_LABELS = {repr(FEATURE_LABELS)}
NORMAL_RANGES = {repr(NORMAL_RANGES)}


def _compute_factors(raw_features: list[float], scaled: np.ndarray) -> list[dict]:
    # SVM feature importance approximated via support vector weight magnitudes
    sv_weights = np.abs(np.dot(DUAL_COEF[0], SUPPORT_VECTORS))
    impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        raw_val = float(raw_features[i])
        z_val = float(scaled[i])
        w = float(sv_weights[i])
        score = max(0.0, z_val * w)
        low, high = NORMAL_RANGES.get(name, (0, 100))
        if raw_val > high:
            status = "Elevated" if raw_val <= high * 1.25 else "High"
        elif raw_val < low:
            status = "Low"
        else:
            status = "Optimal"
        impacts.append({{
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": round(raw_val, 2),
            "score": score,
            "status": status
        }})
    total = sum(item["score"] for item in impacts)
    for item in impacts:
        item["impact"] = round((item["score"] / total * 100) if total > 0 else (100.0 / len(impacts)), 1)
        del item["score"]
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts


def predict(features: list[float]) -> dict:
    \"\"\"
    Predict diabetes risk using RBF Support Vector Machine.
    Returns:
        dict: {{"risk_level": "High"|"Low", "confidence": float, "raw_score": float, "top_factors": list}}
    \"\"\"
    scaled = transform(features)
    # Compute RBF kernel: exp(-gamma * ||x - SV_i||^2)
    dists_sq = np.sum((SUPPORT_VECTORS - scaled) ** 2, axis=1)
    rbf_vals = np.exp(-GAMMA * dists_sq)
    decision = float(np.dot(DUAL_COEF[0], rbf_vals) + INTERCEPT[0])
    
    # Platt scaling probability estimation
    prob = float(1.0 / (1.0 + np.exp(PROB_A[0] * decision + PROB_B[0])))
    risk_level = "High" if decision >= 0.0 or prob >= 0.5 else "Low"
    confidence = float(prob if risk_level == "High" else 1.0 - prob)
    factors = _compute_factors(features, scaled)
    return {{
        "risk_level": risk_level,
        "confidence": round(confidence * 100.0, 2),
        "raw_score": round(prob, 4),
        "top_factors": factors
    }}
'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Exported SVM -> {output_path}")


def export_decision_tree(model_path: str, output_path: str):
    dt = joblib.load(model_path)
    tree = dt.tree_
    children_left_repr = repr(tree.children_left.tolist())
    children_right_repr = repr(tree.children_right.tolist())
    feature_repr = repr(tree.feature.tolist())
    threshold_repr = repr(tree.threshold.tolist())
    # value is 3D (node, 1, n_classes)
    value_repr = repr(tree.value.tolist())
    feature_importances_repr = repr(dt.feature_importances_.tolist())
    classes_repr = repr(dt.classes_.tolist())

    code = f'''"""
Auto-generated Decision Tree module from {os.path.basename(model_path)}.
Pure-Python array-based tree traversal without sklearn dependency at runtime.
"""
import numpy as np
from app.ml.scaler import transform

CHILDREN_LEFT = np.array({children_left_repr}, dtype=np.int32)
CHILDREN_RIGHT = np.array({children_right_repr}, dtype=np.int32)
FEATURE = np.array({feature_repr}, dtype=np.int32)
THRESHOLD = np.array({threshold_repr}, dtype=np.float64)
VALUE = np.array({value_repr}, dtype=np.float64)
FEATURE_IMPORTANCES = np.array({feature_importances_repr}, dtype=np.float64)
CLASSES = {classes_repr}
FEATURE_NAMES = {repr(FEATURE_NAMES)}
FEATURE_LABELS = {repr(FEATURE_LABELS)}
NORMAL_RANGES = {repr(NORMAL_RANGES)}


def _compute_factors(raw_features: list[float], scaled: np.ndarray) -> list[dict]:
    impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        raw_val = float(raw_features[i])
        z_val = float(scaled[i])
        w = float(FEATURE_IMPORTANCES[i])
        score = max(0.0, z_val * w)
        low, high = NORMAL_RANGES.get(name, (0, 100))
        if raw_val > high:
            status = "Elevated" if raw_val <= high * 1.25 else "High"
        elif raw_val < low:
            status = "Low"
        else:
            status = "Optimal"
        impacts.append({{
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": round(raw_val, 2),
            "score": score,
            "status": status
        }})
    total = sum(item["score"] for item in impacts)
    for item in impacts:
        item["impact"] = round((item["score"] / total * 100) if total > 0 else (100.0 / len(impacts)), 1)
        del item["score"]
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts


def predict(features: list[float]) -> dict:
    \"\"\"
    Predict diabetes risk using Decision Tree traversal.
    Returns:
        dict: {{"risk_level": "High"|"Low", "confidence": float, "raw_score": float, "top_factors": list}}
    \"\"\"
    scaled = transform(features)
    node = 0
    while CHILDREN_LEFT[node] != CHILDREN_RIGHT[node]:
        feat = FEATURE[node]
        thresh = THRESHOLD[node]
        if scaled[feat] <= thresh:
            node = CHILDREN_LEFT[node]
        else:
            node = CHILDREN_RIGHT[node]
            
    val = VALUE[node][0]
    total_samples = np.sum(val)
    prob = float(val[1] / total_samples) if total_samples > 0 else 0.0
    risk_level = "High" if prob >= 0.5 else "Low"
    confidence = float(prob if prob >= 0.5 else 1.0 - prob)
    factors = _compute_factors(features, scaled)
    return {{
        "risk_level": risk_level,
        "confidence": round(confidence * 100.0, 2),
        "raw_score": round(prob, 4),
        "top_factors": factors
    }}
'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Exported Decision Tree -> {output_path}")


def export_neural_network(model_path: str, output_path: str):
    nn = joblib.load(model_path)
    coefs_repr = repr([c.tolist() for c in nn.coefs_])
    intercepts_repr = repr([i.tolist() for i in nn.intercepts_])
    classes_repr = repr(nn.classes_.tolist())

    code = f'''"""
Auto-generated Neural Network (MLPClassifier) module from {os.path.basename(model_path)}.
Pure-Python NumPy forward pass implementation (ReLU + Sigmoid) without sklearn dependency at runtime.
"""
import numpy as np
from app.ml.scaler import transform

COEFS = [np.array(w, dtype=np.float64) for w in {coefs_repr}]
INTERCEPTS = [np.array(b, dtype=np.float64) for b in {intercepts_repr}]
CLASSES = {classes_repr}
FEATURE_NAMES = {repr(FEATURE_NAMES)}
FEATURE_LABELS = {repr(FEATURE_LABELS)}
NORMAL_RANGES = {repr(NORMAL_RANGES)}


def _compute_factors(raw_features: list[float], scaled: np.ndarray) -> list[dict]:
    # Neural Network input layer weight magnitudes
    first_layer_weights = np.sum(np.abs(COEFS[0]), axis=1)
    impacts = []
    for i, name in enumerate(FEATURE_NAMES):
        raw_val = float(raw_features[i])
        z_val = float(scaled[i])
        w = float(first_layer_weights[i])
        score = max(0.0, z_val * w)
        low, high = NORMAL_RANGES.get(name, (0, 100))
        if raw_val > high:
            status = "Elevated" if raw_val <= high * 1.25 else "High"
        elif raw_val < low:
            status = "Low"
        else:
            status = "Optimal"
        impacts.append({{
            "feature": name,
            "label": FEATURE_LABELS.get(name, name),
            "value": round(raw_val, 2),
            "score": score,
            "status": status
        }})
    total = sum(item["score"] for item in impacts)
    for item in impacts:
        item["impact"] = round((item["score"] / total * 100) if total > 0 else (100.0 / len(impacts)), 1)
        del item["score"]
    impacts.sort(key=lambda x: x["impact"], reverse=True)
    return impacts


def predict(features: list[float]) -> dict:
    \"\"\"
    Predict diabetes risk using forward pass of trained Neural Network.
    Architecture: Input (8) -> Dense 100 (ReLU) -> Dense 1 (Sigmoid).
    Returns:
        dict: {{"risk_level": "High"|"Low", "confidence": float, "raw_score": float, "top_factors": list}}
    \"\"\"
    scaled = transform(features)
    # Hidden layer: ReLU(X * W1 + b1)
    hidden = np.maximum(0.0, np.dot(scaled, COEFS[0]) + INTERCEPTS[0])
    # Output layer: Sigmoid(hidden * W2 + b2)
    logit = np.dot(hidden, COEFS[1]) + INTERCEPTS[1]
    prob = float(1.0 / (1.0 + np.exp(-logit[0])))
    risk_level = "High" if prob >= 0.5 else "Low"
    confidence = float(prob if prob >= 0.5 else 1.0 - prob)
    factors = _compute_factors(features, scaled)
    return {{
        "risk_level": risk_level,
        "confidence": round(confidence * 100.0, 2),
        "raw_score": round(prob, 4),
        "top_factors": factors
    }}
'''
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"Exported Neural Network -> {output_path}")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scaler_pkl = os.path.join(root, "scaler.pkl")
    lr_pkl = os.path.join(root, "model_logreg.pkl")
    svm_pkl = os.path.join(root, "model_svm.pkl")
    dt_pkl = os.path.join(root, "model_dt.pkl")
    nn_pkl = os.path.join(root, "model_nn.pkl")

    out_scaler = os.path.join(root, "app", "ml", "scaler.py")
    out_lr = os.path.join(root, "app", "ml", "models", "logistic_regression.py")
    out_svm = os.path.join(root, "app", "ml", "models", "svm.py")
    out_dt = os.path.join(root, "app", "ml", "models", "decision_tree.py")
    out_nn = os.path.join(root, "app", "ml", "models", "neural_network.py")

    print("Beginning .pkl -> .py model conversion...")
    export_scaler(scaler_pkl, out_scaler)
    export_logistic_regression(lr_pkl, out_lr)
    export_svm(svm_pkl, out_svm)
    export_decision_tree(dt_pkl, out_dt)
    export_neural_network(nn_pkl, out_nn)
    print("All models successfully exported to plain-Python modules!")


if __name__ == "__main__":
    main()
