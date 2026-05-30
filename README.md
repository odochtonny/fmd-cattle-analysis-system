# Professional FMD Cattle Analysis System

This upgraded starter project combines a Flutter web/mobile frontend with a FastAPI backend for professional cattle Foot and Mouth Disease surveillance.

## Main Features

- Professional Flutter dashboard with sidebar navigation
- Real-time summary cards for total analyses, FMD positives, healthy cattle and positivity rate
- District-level outbreak distribution chart
- Risk intelligence panel and recent analyses table
- Mandatory farm data capture before photo analysis
- Mandatory signs and symptoms capture before photo analysis
- Photo evidence saved to MongoDB GridFS
- Detection record saved to MongoDB `detections` collection
- Hybrid AI pipeline placeholder:
  - DenseNet cattle classifier gatekeeper
  - EfficientNetB3 FMD image classifier
  - Random Forest decision fusion using CNN probabilities + symptoms
- Backend dashboard APIs for analytics and reporting

## Project Structure

```text
fmd_cattle_analysis_system/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database/mongodb.py
│   │   ├── models/
│   │   │   ├── densenet_cattle_classifier.keras
│   │   │   ├── efficientnetb3_fmd.keras
│   │   │   ├── random_forest.pkl
│   │   │   └── scaler.pkl
│   │   └── services/
│   └── requirements.txt
├── flutter_app/
│   ├── lib/
│   │   ├── screens/
│   │   ├── services/
│   │   ├── widgets/
│   │   └── theme/
│   └── pubspec.yaml
└── backend_tools/
```

## Backend Setup

Use Python 3.10 or 3.11. Avoid Python 3.14 for TensorFlow.

```powershell
cd backend
py -3.10 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env`:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=fmd_detector
```

Run:

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Flutter Setup

```powershell
cd flutter_app
flutter pub get
flutter run -d chrome
```

For Android emulator, change `baseUrl` in:

```text
flutter_app/lib/services/api_service.dart
```

from:

```dart
http://127.0.0.1:8000
```

to:

```dart
http://10.0.2.2:8000
```

## Required Models

Place your trained models here:

```text
backend/app/models/
```

Expected names:

```text
densenet_cattle_classifier.keras
efficientnetb3_fmd.keras
random_forest.pkl
scaler.pkl
```

The system includes fallbacks so the app can run before the real models are added.

## Mandatory Capture Rules

The system requires the user to capture these before image analysis:

- Farmer name
- Farm name
- District
- Sub-county
- Village
- Duration of symptoms
- At least one clinical sign/symptom
- Cattle photo

## Professional Dashboard APIs

```text
GET /dashboard/summary
GET /dashboard/trends?days=30
GET /records/{record_id}
POST /analyze
```

## MongoDB Collections Created

```text
detections
fs.files
fs.chunks
```
