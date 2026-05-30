from datetime import datetime, timedelta
import json
from typing import Any, Dict

from bson import ObjectId
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.database.mongodb import detections_collection, fs
from app.services.analysis_pipeline import analyze_cattle_image

app = FastAPI(title="Professional FMD Cattle Analysis API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_FARM_FIELDS = ["farmer_name", "farm_name", "district", "subcounty", "village"]
REQUIRED_SYMPTOMS = [
    "fever", "mouth_lesions", "drooling", "lameness", "loss_of_appetite",
    "hoof_lesions", "duration_days"
]


def _loads_json(value: str, label: str) -> Dict[str, Any]:
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"Invalid JSON for {label}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail=f"{label} must be a JSON object")
    return data


def _validate_required(data: Dict[str, Any], required: list[str], label: str):
    missing = [field for field in required if field not in data or data[field] in ["", None]]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing {label}: {', '.join(missing)}")


@app.get("/")
def root():
    return {"message": "Professional FMD Cattle Analysis API is running", "docs": "/docs"}


@app.post("/analyze")
async def analyze_cattle(
    image: UploadFile = File(...),
    farm_info: str = Form(...),
    symptoms: str = Form(...),
):
    farm_data = _loads_json(farm_info, "farm_info")
    symptoms_data = _loads_json(symptoms, "symptoms")

    _validate_required(farm_data, REQUIRED_FARM_FIELDS, "farm information")
    _validate_required(symptoms_data, REQUIRED_SYMPTOMS, "symptoms")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    image_id = fs.put(
        image_bytes,
        filename=image.filename,
        content_type=image.content_type,
        metadata={"farm_name": farm_data.get("farm_name"), "district": farm_data.get("district")},
        upload_date=datetime.utcnow(),
    )

    result = analyze_cattle_image(image_bytes=image_bytes, symptoms=symptoms_data)

    record = {
        "farm_information": farm_data,
        "symptoms": symptoms_data,
        "image_id": str(image_id),
        "filename": image.filename,
        "content_type": image.content_type,
        "analysis_result": result,
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

    recent_cursor = detections_collection.find({}).sort("created_at", -1).limit(10)
    recent_cases = []
    for doc in recent_cursor:
        farm = doc.get("farm_information", {})
        result = doc.get("analysis_result", {})
        recent_cases.append({
            "id": str(doc.get("_id")),
            "farm_name": farm.get("farm_name", "Unknown Farm"),
            "district": farm.get("district", "Unknown"),
            "prediction": result.get("final_prediction") or result.get("prediction") or result.get("status", "Unknown"),
            "severity": result.get("severity", "N/A"),
            "date": doc.get("created_at", datetime.utcnow()).strftime("%Y-%m-%d %H:%M"),
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
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "total": {"$sum": 1},
            "fmd": {"$sum": {"$cond": [{"$regexMatch": {"input": {"$ifNull": ["$analysis_result.final_prediction", ""]}, "regex": "FMD", "options": "i"}}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    return {"days": days, "trends": list(detections_collection.aggregate(pipeline))}


@app.get("/records/{record_id}")
def get_record(record_id: str):
    try:
        oid = ObjectId(record_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid record ID")
    doc = detections_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Record not found")
    doc["_id"] = str(doc["_id"])
    return doc
