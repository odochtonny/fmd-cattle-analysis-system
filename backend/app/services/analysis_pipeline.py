from app.services.cattle_classifier import predict_cattle
from app.services.fmd_cnn import predict_fmd_cnn
from app.services.random_forest_model import predict_rf
from app.services.treatment_rules import recommend_treatment


def analyze_cattle_image(image_bytes: bytes, symptoms: dict) -> dict:
    cattle_result = predict_cattle(image_bytes)

    if not cattle_result["is_cattle"]:
        return {
            "status": "rejected",
            "message": "Uploaded image is not recognized as cattle. Please upload a clear cattle photo.",
            "cattle_result": cattle_result,
            "final_prediction": "Rejected - Not Cattle",
            "severity": "N/A",
            "final_confidence": cattle_result.get("confidence", 0),
        }

    cnn_result = predict_fmd_cnn(image_bytes)

    # Get CNN FMD probability safely
    cnn_fmd_prob = (
        cnn_result.get("fmd_probability")
        or cnn_result.get("fmd_prob")
        or cnn_result.get("probability")
        or cnn_result.get("confidence")
        or 0
    )

    rf_result = predict_rf(cnn_result, symptoms)

    final_prediction = rf_result["prediction"]
    final_confidence = rf_result["confidence"]
    severity = rf_result["severity"]

    # Safety override to reduce false negatives
    # If CNN strongly suspects FMD, do not allow RF to mark it as Healthy.
    if cnn_fmd_prob >= 0.35 and final_prediction.lower() == "healthy":
        final_prediction = "FMD Suspected"
        final_confidence = cnn_fmd_prob
        severity = "Moderate"

    treatment = recommend_treatment(
        diagnosis=final_prediction,
        severity=severity,
        confidence=final_confidence
    )

    return {
        "status": "success",
        "model_pipeline": "DenseNet cattle gate + EfficientNetB3 FMD CNN + Random Forest fusion",
        "cattle_result": cattle_result,
        "cnn_result": cnn_result,
        "rf_result": rf_result,
        "final_prediction": final_prediction,
        "severity": severity,
        "final_confidence": final_confidence,
        "confidence": final_confidence,
        "treatment_recommendation": treatment,
    }