from pathlib import Path
import tensorflow as tf
import numpy as np
from app.services.image_utils import load_image_from_bytes

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "efficientnetb3_fmd.keras"

CLASS_NAMES = ["FMD", "Healthy"]
FMD_THRESHOLD = 0.35

_model = None
_feature_extractor = None


def get_model():
    global _model
    if _model is None and MODEL_PATH.exists():
        _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
    return _model


def get_feature_extractor():
    global _feature_extractor

    model = get_model()
    if model is None:
        return None

    if _feature_extractor is not None:
        return _feature_extractor

    # Automatically find a layer with 1536 output features
    for layer in reversed(model.layers):
        try:
            shape = layer.output_shape
            if isinstance(shape, tuple) and len(shape) == 2 and shape[-1] == 1536:
                _feature_extractor = tf.keras.Model(
                    inputs=model.input,
                    outputs=layer.output
                )
                print(f"Using CNN feature layer: {layer.name}")
                return _feature_extractor
        except Exception:
            pass

    # Fallback: use second-last layer
    _feature_extractor = tf.keras.Model(
        inputs=model.input,
        outputs=model.layers[-2].output
    )
    print(f"Using fallback CNN feature layer: {model.layers[-2].name}")
    return _feature_extractor


def predict_fmd_cnn(image_bytes: bytes) -> dict:
    model = get_model()

    if model is None:
        return {
            "prediction": "FMD Suspected",
            "healthy_probability": 0.25,
            "fmd_probability": 0.75,
            "confidence": 0.75,
            "cnn_features": None,
            "note": "Model missing; fallback prediction used."
        }

    img = load_image_from_bytes(image_bytes, (300, 300))

    pred = model.predict(img, verbose=0)
    values = np.ravel(pred)

    if len(values) == 1:
        raw_score = float(values[0])

        # Use this if binary model was trained as Healthy=0, FMD=1
        fmd_prob = raw_score
        healthy_prob = 1.0 - raw_score

        # If results are still reversed, swap to this:
        # healthy_prob = raw_score
        # fmd_prob = 1.0 - raw_score

    else:
        class_probs = {
            CLASS_NAMES[i]: float(values[i])
            for i in range(min(len(CLASS_NAMES), len(values)))
        }

        fmd_prob = class_probs.get("FMD", 0.0)
        healthy_prob = class_probs.get("Healthy", 0.0)

    feature_extractor = get_feature_extractor()
    cnn_features = None

    if feature_extractor is not None:
        features = feature_extractor.predict(img, verbose=0)
        cnn_features = np.ravel(features).astype(float).tolist()

    prediction = "FMD Suspected" if fmd_prob >= FMD_THRESHOLD else "Healthy"

    return {
        "prediction": prediction,
        "healthy_probability": round(healthy_prob, 4),
        "fmd_probability": round(fmd_prob, 4),
        "confidence": round(fmd_prob if prediction != "Healthy" else healthy_prob, 4),
        "raw_output": values.tolist(),
        "cnn_features": cnn_features,
        "cnn_feature_count": len(cnn_features) if cnn_features is not None else 0
    }