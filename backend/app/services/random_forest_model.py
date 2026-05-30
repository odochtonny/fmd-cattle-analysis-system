from pathlib import Path
import joblib
import numpy as np

BASE = Path(__file__).resolve().parents[1] / "models"
RF_PATH = BASE / "random_forest_fmd.pkl"
SCALER_PATH = BASE / "rf_scaler.pkl"

FMD_THRESHOLD = 0.35

_rf = None
_scaler = None


def get_rf():
    global _rf
    if _rf is None and RF_PATH.exists():
        _rf = joblib.load(RF_PATH)
    return _rf


def get_scaler():
    global _scaler
    if _scaler is None and SCALER_PATH.exists():
        _scaler = joblib.load(SCALER_PATH)
    return _scaler


def normalize_prediction(prediction):
    text = str(prediction).lower().strip()

    if text in ["1", "fmd", "fmd positive", "fmd suspected", "positive"]:
        return "FMD Positive"

    if text in ["0", "healthy", "normal", "negative"]:
        return "Healthy"

    return str(prediction)


def symptom_to_float(symptoms: dict, key: str) -> float:
    value = symptoms.get(key, 0)

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, str):
        value = value.lower().strip()
        if value in ["true", "yes", "present", "1"]:
            return 1.0
        if value in ["false", "no", "absent", "0", ""]:
            return 0.0

    try:
        return float(value)
    except Exception:
        return 0.0


def calculate_symptom_probability(symptoms: dict) -> float:
    symptom_keys = [
        "fever",
        "mouth_lesions",
        "drooling",
        "lameness",
        "loss_of_appetite",
        "hoof_lesions",
        "reduced_milk",
    ]

    score = sum(symptom_to_float(symptoms, key) for key in symptom_keys)
    return min(1.0, score / len(symptom_keys))


def calculate_severity(final_score: float, symptom_prob: float, prediction: str) -> str:
    if prediction == "Healthy":
        return "None"

    if final_score >= 0.80 or symptom_prob >= 0.75:
        return "Severe"

    if final_score >= 0.55 or symptom_prob >= 0.45:
        return "Moderate"

    return "Mild"


def calibrated_fmd_confidence(cnn_fmd: float, rf_score: float, symptom_prob: float) -> float:
    base_score = (
        (cnn_fmd * 0.40) +
        (rf_score * 0.35) +
        (symptom_prob * 0.25)
    )

    # Boost severe clinical cases
    if symptom_prob >= 0.75 and cnn_fmd >= 0.35:
        base_score = max(base_score, 0.82)

    if symptom_prob >= 0.85 and cnn_fmd >= 0.40:
        base_score = max(base_score, 0.88)

    if symptom_prob >= 0.90 and cnn_fmd >= 0.50:
        base_score = max(base_score, 0.92)

    return min(0.99, base_score)


def predict_rf(cnn_result: dict, symptoms: dict) -> dict:
    rf = get_rf()
    scaler = get_scaler()

    cnn_fmd = float(cnn_result.get("fmd_probability", 0.0))
    symptom_prob = calculate_symptom_probability(symptoms)
    cnn_features = cnn_result.get("cnn_features")

    rf_score = 0.0
    rf_prediction = "Healthy"

    if cnn_features is not None:
        features = np.array([cnn_features], dtype=float)

        if features.shape[1] != 1536:
            print(f"Warning: CNN features have {features.shape[1]} values, expected 1536.")

        if scaler is not None:
            features = scaler.transform(features)

        if rf is not None:
            rf_prediction = normalize_prediction(rf.predict(features)[0])

            if hasattr(rf, "predict_proba"):
                proba = rf.predict_proba(features)[0]
                classes = list(rf.classes_)

                for cls, prob in zip(classes, proba):
                    if normalize_prediction(cls) == "FMD Positive":
                        rf_score = float(prob)
        else:
            rf_score = cnn_fmd
            rf_prediction = "FMD Positive" if cnn_fmd >= FMD_THRESHOLD else "Healthy"

    else:
        rf_score = cnn_fmd
        rf_prediction = "FMD Positive" if cnn_fmd >= FMD_THRESHOLD else "Healthy"

    combined_score = calibrated_fmd_confidence(
        cnn_fmd=cnn_fmd,
        rf_score=rf_score,
        symptom_prob=symptom_prob
    )

    if combined_score >= FMD_THRESHOLD or cnn_fmd >= FMD_THRESHOLD or symptom_prob >= 0.45:
        prediction = "FMD Positive"
        final_score = combined_score
    else:
        prediction = "Healthy"
        final_score = max(1.0 - combined_score, 0.0)

    severity = calculate_severity(final_score, symptom_prob, prediction)

    return {
        "prediction": prediction,
        "severity": severity,
        "confidence": round(float(final_score), 4),
        "cnn_fmd_probability": round(float(cnn_fmd), 4),
        "rf_probability": round(float(rf_score), 4),
        "symptom_probability": round(float(symptom_prob), 4),
        "combined_fmd_score": round(float(combined_score), 4),
        "rf_prediction": rf_prediction
    }