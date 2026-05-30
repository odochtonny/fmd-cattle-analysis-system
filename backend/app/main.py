from datetime import datetime, timedelta
import json
from typing import Any, Dict

from bson import ObjectId
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware

from app.database.mongodb import detections_collection, fs
from app.services.analysis_pipeline import analyze_cattle_image

app = FastAPI(
    title="Professional FMD Cattle Analysis API",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_FARM_FIELDS = [
    "farmer_name",
    "farm_name",
    "district",
    "subcounty",
    "village",
]

REQUIRED_SYMPTOMS = [
    "fever",
    "mouth_lesions",
    "drooling",
    "lameness",
    "loss_of_appetite",
    "hoof_lesions",
    "duration_days",
]


def _loads_json(value: str, label: str) -> Dict[str, Any]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON for {label}",
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be a JSON object",
        )

    return data


def _validate_required(
    data: Dict[str, Any],
    required: list[str],
    label: str,
):
    missing = [
        field
        for field in required
        if field not in data or data[field] in ["", None]
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing {label}: {', '.join(missing)}",
        )


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc["_id"] = str(doc["_id"])

    if "created_at" in doc and isinstance(doc["created_at"], datetime):
        doc["created_at"] = doc["created_at"].isoformat()

    if "image_id" in doc and isinstance(doc["image_id"], ObjectId):
        doc["image_id"] = str(doc["image_id"])

    return doc


@app.get("/")
def root():
    return {
        "message": "Professional FMD Cattle Analysis API is running",
        "version": "2.1.0",
        "docs": "/docs",
        "mode": "Mobile TFLite + Random Forest supported",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fmd-cattle-analysis-api",
        "time": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------
# OLD SERVER-SIDE ANALYSIS ENDPOINT
# Kept for compatibility, but mobile app should now use TFLite locally.
# ---------------------------------------------------------------------
@app.post("/analyze")
async def analyze_cattle(
    image: UploadFile = File(...),
    farm_info: str = Form(...),
    symptoms: str = Form(...),
):
    farm_data = _loads_json(farm_info, "farm_info")
    symptoms_data = _loads_json(symptoms, "symptoms")

    _validate_required(
        farm_data,
        REQUIRED_FARM_FIELDS,
        "farm information",
    )

    _validate_required(
        symptoms_data,
        REQUIRED_SYMPTOMS,
        "symptoms",
    )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty",
        )

    image_id = fs.put(
        image_bytes,
        filename=image.filename,
        content_type=image.content_type,
        metadata={
            "farm_name": farm_data.get("farm_name"),
            "district": farm_data.get("district"),
        },
        upload_date=datetime.utcnow(),
    )

    result = analyze_cattle_image(
        image_bytes=image_bytes,
        symptoms=symptoms_data,
    )

    record = {
        "farm_information": farm_data,
        "symptoms": symptoms_data,
        "image_id": str(image_id),
        "filename": image.filename,
        "content_type": image.content_type,
        "analysis_result": result,
        "analysis_source": "server_tensorflow_pipeline",
        "created_at": datetime.utcnow(),
        "surveillance_status": "active",
    }

    inserted = detections_collection.insert_one(record)

    return {
        "message": "Analysis completed and evidence saved to MongoDB",
        "record_id": str(inserted.inserted_id),
        "image_id": str(image_id),
        "result": result,
    }


# ---------------------------------------------------------------------
# NEW MOBILE TFLITE RESULT SAVE ENDPOINT
# Flutter runs AI locally, then sends final result here for storage.
# ---------------------------------------------------------------------
@app.post("/save-result")
async def save_result(payload: Dict[str, Any] = Body(...)):
    farm_data = (
        payload.get("farm_info")
        or payload.get("farm_information")
        or {}
    )

    symptoms_data = payload.get("symptoms") or {}

    if not isinstance(farm_data, dict):
        raise HTTPException(
            status_code=400,
            detail="farm_info must be a JSON object",
        )

    if not isinstance(symptoms_data, dict):
        raise HTTPException(
            status_code=400,
            detail="symptoms must be a JSON object",
        )

    _validate_required(
        farm_data,
        REQUIRED_FARM_FIELDS,
        "farm information",
    )

    result = {
        "status": payload.get("status", "success"),
        "model_pipeline": payload.get(
            "model_pipeline",
            "On-device TFLite cattle gate + EfficientNetB3 features + Random Forest fusion",
        ),
        "cattle_result": payload.get("cattle_result"),
        "cnn_result": payload.get("cnn_result"),
        "rf_result": payload.get("rf_result"),
        "final_prediction": payload.get(
            "final_prediction",
            payload.get("prediction", "Unknown"),
        ),
        "severity": payload.get("severity", "N/A"),
        "final_confidence": payload.get(
            "final_confidence",
            payload.get("confidence", 0),
        ),
        "confidence": payload.get(
            "confidence",
            payload.get("final_confidence", 0),
        ),
        "analysis_source": payload.get(
            "analysis_source",
            "mobile_tflite_random_forest",
        ),
    }

    record = {
        "farm_information": farm_data,
        "symptoms": symptoms_data,
        "image_name": payload.get("image_name"),
        "analysis_result": result,
        "analysis_source": result["analysis_source"],
        "created_at": datetime.utcnow(),
        "surveillance_status": "active",
    }

    inserted = detections_collection.insert_one(record)

    return {
        "message": "Mobile TFLite analysis result saved successfully",
        "status": "saved",
        "record_id": str(inserted.inserted_id),
        "result": result,
    }


@app.get("/dashboard/summary")
def dashboard_summary():
    total = detections_collection.count_documents({})

    rejected = detections_collection.count_documents(
        {"analysis_result.status": "rejected"}
    )

    fmd_positive = detections_collection.count_documents(
        {
            "$or": [
                {
                    "analysis_result.final_prediction": {
                        "$regex": "FMD",
                        "$options": "i",
                    }
                },
                {
                    "analysis_result.prediction": {
                        "$regex": "FMD",
                        "$options": "i",
                    }
                },
            ]
        }
    )

    healthy = detections_collection.count_documents(
        {
            "$or": [
                {
                    "analysis_result.final_prediction": {
                        "$regex": "Healthy",
                        "$options": "i",
                    }
                },
                {
                    "analysis_result.prediction": {
                        "$regex": "Healthy",
                        "$options": "i",
                    }
                },
            ]
        }
    )

    valid = max(fmd_positive + healthy, 1)
    positivity_rate = (fmd_positive / valid) * 100

    district_pipeline = [
        {
            "$match": {
                "analysis_result.final_prediction": {
                    "$regex": "FMD",
                    "$options": "i",
                }
            }
        },
        {
            "$group": {
                "_id": "$farm_information.district",
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]

    district_counts = [
        {
            "district": item.get("_id") or "Unknown",
            "count": item.get("count", 0),
        }
        for item in detections_collection.aggregate(district_pipeline)
    ]

    recent_cursor = (
        detections_collection.find({})
        .sort("created_at", -1)
        .limit(10)
    )

    recent_cases = []

    for doc in recent_cursor:
        farm = doc.get("farm_information", {})
        result = doc.get("analysis_result", {})

        recent_cases.append(
            {
                "id": str(doc.get("_id")),
                "farm_name": farm.get("farm_name", "Unknown Farm"),
                "district": farm.get("district", "Unknown"),
                "prediction": (
                    result.get("final_prediction")
                    or result.get("prediction")
                    or result.get("status", "Unknown")
                ),
                "severity": result.get("severity", "N/A"),
                "confidence": result.get(
                    "final_confidence",
                    result.get("confidence", 0),
                ),
                "source": doc.get("analysis_source", "unknown"),
                "date": doc.get(
                    "created_at",
                    datetime.utcnow(),
                ).strftime("%Y-%m-%d %H:%M"),
            }
        )

    return {
        "total_analyses": total,
        "fmd_positive": fmd_positive,
        "healthy": healthy,
        "rejected": rejected,
        "positivity_rate": round(positivity_rate, 2),
        "district_counts": district_counts,
        "recent_cases": recent_cases,
    }


@app.get("/dashboard/trends")
def dashboard_trends(days: int = 30):
    start = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {"created_at": {"$gte": start}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$created_at",
                    }
                },
                "total": {"$sum": 1},
                "fmd": {
                    "$sum": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": {
                                        "$ifNull": [
                                            "$analysis_result.final_prediction",
                                            "",
                                        ]
                                    },
                                    "regex": "FMD",
                                    "options": "i",
                                }
                            },
                            1,
                            0,
                        ]
                    }
                },
                "healthy": {
                    "$sum": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": {
                                        "$ifNull": [
                                            "$analysis_result.final_prediction",
                                            "",
                                        ]
                                    },
                                    "regex": "Healthy",
                                    "options": "i",
                                }
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]

    return {
        "days": days,
        "trends": list(detections_collection.aggregate(pipeline)),
    }


@app.get("/records/{record_id}")
def get_record(record_id: str):
    try:
        oid = ObjectId(record_id)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid record ID",
        )

    doc = detections_collection.find_one({"_id": oid})

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Record not found",
        )

    return _serialize_doc(doc)