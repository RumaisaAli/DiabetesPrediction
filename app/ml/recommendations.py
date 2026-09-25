"""
Clinical Recommendations Engine
Generates tailored, rule-based medical, diet, exercise, and lifestyle recommendations
based on calculated risk level and primary contributing clinical factors.
"""
from typing import List, Dict, Any


def generate_recommendations(risk_level: str, top_factors: list[dict], vitals: dict) -> list[str]:
    """
    Produces actionable clinical recommendations.
    Ensures that High-Risk profiles include diet, exercise, and doctor-visit suggestions (TC-14).
    """
    recs = []

    if risk_level == "High":
        recs.append("Consult an Endocrinologist or Primary Care Physician promptly for comprehensive HbA1c screening and clinical evaluation.")
        recs.append("Adopt a low-glycemic, Mediterranean-style diet rich in fiber, whole grains, and lean proteins; eliminate refined sugars and sweetened beverages.")
        recs.append("Engage in at least 150 minutes of moderate-intensity aerobic exercise per week (e.g. brisk walking, swimming) combined with resistance training.")
        recs.append("Monitor fasting blood glucose levels daily and maintain a detailed journal for physician review.")
    else:
        recs.append("Maintain an active lifestyle with regular cardiovascular exercise to preserve insulin sensitivity.")
        recs.append("Follow a balanced, nutrient-dense diet emphasizing vegetables, healthy fats, and controlled portion sizes.")
        recs.append("Schedule an annual routine physical exam and routine metabolic blood panel.")

    # Tailored recommendations based on specific elevated factors
    glucose_val = vitals.get("glucose", 0)
    bmi_val = vitals.get("bmi", 0)
    bp_val = vitals.get("blood_pressure", 0)
    insulin_val = vitals.get("insulin", 0)

    if glucose_val >= 126:
        recs.append(f"Your blood glucose ({glucose_val:.1f} mg/dL) is in the diabetic threshold range. Immediate medical follow-up is recommended.")
    elif glucose_val >= 100:
        recs.append(f"Fasting glucose ({glucose_val:.1f} mg/dL) indicates pre-diabetes risk. Target carbohydrate restriction and weight management.")

    if bmi_val >= 30:
        recs.append(f"BMI of {bmi_val:.1f} signifies obesity. Aiming for a 5-7% reduction in body weight can reduce diabetes incidence by up to 58%.")
    elif bmi_val >= 25:
        recs.append(f"BMI of {bmi_val:.1f} falls in the overweight range. Incorporate daily caloric moderation and portion control.")

    if bp_val >= 90:
        recs.append(f"Diastolic blood pressure ({bp_val:.0f} mm Hg) is elevated. Reduce sodium intake and discuss cardiovascular screening with your doctor.")

    if insulin_val >= 166:
        recs.append(f"Elevated serum insulin ({insulin_val:.1f} mu U/ml) indicates hyperinsulinemia and insulin resistance. Focus on intermittent fasting or low-carb meal plans.")

    # Remove duplicates while preserving order
    seen = set()
    deduped = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            deduped.append(r)

    return deduped
