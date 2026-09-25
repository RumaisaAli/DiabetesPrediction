"""
Inference Service
Loads and executes pure-Python exported models directly.
Imports modules once at startup for sub-millisecond prediction performance.
"""
from typing import Optional
from app.ml.models import (
    decision_tree,
    logistic_regression,
    svm,
    neural_network,
)
from app.ml.recommendations import generate_recommendations

MODEL_REGISTRY = {
    "Decision Tree": decision_tree,
    "Logistic Regression": logistic_regression,
    "SVM": svm,
    "Neural Network": neural_network,
    # Module path aliases
    "app.ml.models.decision_tree": decision_tree,
    "app.ml.models.logistic_regression": logistic_regression,
    "app.ml.models.svm": svm,
    "app.ml.models.neural_network": neural_network,
}

FEATURE_KEYS = [
    "pregnancies",
    "glucose",
    "blood_pressure",
    "skin_thickness",
    "insulin",
    "bmi",
    "diabetes_pedigree_function",
    "age",
]


def predict_diabetes_risk(vitals_dict: dict, model_name: str = "Decision Tree") -> dict:
    """
    Executes inference for the given 8 vitals using the specified or active model module.
    """
    model_module = MODEL_REGISTRY.get(model_name)
    if not model_module:
        # Fallback to Decision Tree
        model_module = decision_tree
        model_name = "Decision Tree"

    feature_values = [float(vitals_dict[k]) for k in FEATURE_KEYS]
    result = model_module.predict(feature_values)

    recs = generate_recommendations(
        risk_level=result["risk_level"],
        top_factors=result["top_factors"],
        vitals=vitals_dict
    )

    result["recommendations"] = recs
    result["model_used"] = model_name
    return result
