from datetime import datetime, timedelta
from typing import Any, Dict

from bson import ObjectId
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database.mongodb import detections_collection

app = FastAPI(
    title="Professional FMD Cattle Analysis API",
    version="3.0.0",
    description="Lightweight backend for mobile TFLite + Random Forest FMD analysis",
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


def _validate_required(data: Dict[str, Any], required: list[str], label: str):
    missing = [
        field for field in required
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

    if "updated_at" in doc and isinstance(doc["updated_at"], datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()

    return doc


@app.get("/")
def root():
    return {
        "message": "Professional FMD Cattle Analysis API is running",
        "version": "3.0.0",
        "docs": "/docs",
        "mode": "Lightweight backend: mobile TFLite + Random Forest inference",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "fmd-cattle-analysis-api",
        "mode": "mobile_tflite_backend",
        "time": datetime.utcnow().isoformat(),
    }


@app.post("/save-result")
async def save_result(payload: Dict[str, Any] = Body(...)):
    farm_data = payload.get("farm_info") or payload.get("farm_information") or {}
    symptoms_data = payload.get("symptoms") or {}

    if not isinstance(farm_data, dict):
        raise HTTPException(status_code=400, detail="farm_info must be a JSON object")

    if not isinstance(symptoms_data, dict):
        raise HTTPException(status_code=400, detail="symptoms must be a JSON object")

    _validate_required(farm_data, REQUIRED_FARM_FIELDS, "farm information")

    result = {
        "status": payload.get("status", "success"),
        "model_pipeline": payload.get(
            "model_pipeline",
            "On-device DenseNet cattle gate + EfficientNetB3 features + Random Forest fusion",
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
        "confidence": payload.get("confidence", payload.get("final_confidence", 0)),
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
        "updated_at": datetime.utcnow(),
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
    rejected = detections_collection.count_documents({"analysis_result.status": "rejected"})

    fmd_positive = detections_collection.count_documents({
        "$or": [
            {"analysis_result.final_prediction": {"$regex": "FMD", "$options": "i"}},
            {"analysis_result.prediction": {"$regex": "FMD", "$options": "i"}},
        ]
    })

    healthy = detections_collection.count_documents({
        "$or": [
            {"analysis_result.final_prediction": {"$regex": "Healthy", "$options": "i"}},
            {"analysis_result.prediction": {"$regex": "Healthy", "$options": "i"}},
        ]
    })

    valid = max(fmd_positive + healthy, 1)
    positivity_rate = (fmd_positive / valid) * 100

    district_pipeline = [
        {"$match": {"analysis_result.final_prediction": {"$regex": "FMD", "$options": "i"}}},
        {"$group": {"_id": "$farm_information.district", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ]

    district_counts = [
        {"district": item.get("_id") or "Unknown", "count": item.get("count", 0)}
        for item in detections_collection.aggregate(district_pipeline)
    ]

    recent_cases = []
    recent_cursor = detections_collection.find({}).sort("created_at", -1).limit(10)

    for doc in recent_cursor:
        farm = doc.get("farm_information", {})
        result = doc.get("analysis_result", {})
        created_at = doc.get("created_at", datetime.utcnow())

        date_value = (
            created_at.strftime("%Y-%m-%d %H:%M")
            if isinstance(created_at, datetime)
            else str(created_at)
        )

        recent_cases.append({
            "id": str(doc.get("_id")),
            "farm_name": farm.get("farm_name", "Unknown Farm"),
            "district": farm.get("district", "Unknown"),
            "prediction": (
                result.get("final_prediction")
                or result.get("prediction")
                or result.get("status", "Unknown")
            ),
            "severity": result.get("severity", "N/A"),
            "confidence": result.get("final_confidence", result.get("confidence", 0)),
            "source": doc.get("analysis_source", "unknown"),
            "date": date_value,
        })

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
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "total": {"$sum": 1},
                "fmd": {
                    "$sum": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": {"$ifNull": ["$analysis_result.final_prediction", ""]},
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
                                    "input": {"$ifNull": ["$analysis_result.final_prediction", ""]},
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
        raise HTTPException(status_code=400, detail="Invalid record ID")

    doc = detections_collection.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")

    return _serialize_doc(doc)