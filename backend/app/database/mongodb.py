import os
from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "fmd_detector")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
fs = GridFS(db)
detections_collection = db["detections"]

# Helpful indexes for dashboard performance
detections_collection.create_index("created_at")
detections_collection.create_index("farm_information.district")
detections_collection.create_index("analysis_result.final_prediction")
