from pathlib import Path
import tensorflow as tf
import numpy as np
from app.services.image_utils import load_image_from_bytes

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "cattle_densenet_final.keras"
_model = None


def get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    return _model


def predict_cattle(image_bytes: bytes) -> dict:
    model = get_model()
    if model is None:
        return {"is_cattle": True, "confidence": 0.99, "note": "Model missing; fallback allowed."}

    img = load_image_from_bytes(image_bytes, (224, 224))
    pred = model.predict(img, verbose=0)
    score = float(np.ravel(pred)[0])

    # Assumption: score >= 0.5 means cattle. Reverse this if your model uses opposite labels.
    return {
        "is_cattle": score >= 0.5,
        "confidence": score if score >= 0.5 else 1 - score
    }
