def recommend_treatment(diagnosis: str, severity: str, confidence: float) -> dict:
    if diagnosis == "Healthy":
        return {
            "summary": "No strong signs of FMD detected.",
            "actions": [
                "Continue routine observation.",
                "Maintain vaccination and farm hygiene schedules.",
                "Recheck if new symptoms appear."
            ]
        }

    actions = [
        "Isolate the affected animal from the herd.",
        "Contact a qualified veterinary officer for confirmation and management.",
        "Restrict animal movement from the farm.",
        "Disinfect feeding areas, watering points, and handling equipment.",
        "Monitor other cattle for fever, mouth lesions, drooling, and lameness."
    ]

    if severity in ["Moderate", "Severe"]:
        actions.append("Notify local veterinary authorities for outbreak surveillance.")

    return {
        "summary": f"{diagnosis} with {severity.lower()} severity suspected at confidence {confidence}.",
        "actions": actions
    }
