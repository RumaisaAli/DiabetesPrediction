"""
Auto-generated Scaler module from scaler.pkl.
Pure-Python / NumPy implementation without sklearn dependency at runtime.
"""
import numpy as np

MEAN = np.array([3.8192182410423454, 120.90879478827361, 69.44299674267101, 20.77687296416938, 78.66612377850163, 31.97328990228013, 0.477428338762215, 33.36644951140065], dtype=np.float64)
SCALE = np.array([3.311448216586372, 31.535381414498353, 18.387588970636795, 15.843515694762356, 107.64880281808567, 7.854959838378327, 0.33003119077476745, 11.82379790254742], dtype=np.float64)
VAR = np.array([10.965689291133062, 994.4802809578881, 338.1034281530839, 251.0169895701811, 11588.264748167088, 61.70039406253647, 0.10892058688421095, 139.80219684028478], dtype=np.float64)
FEATURE_NAMES = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

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
