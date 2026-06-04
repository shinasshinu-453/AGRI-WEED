# AgriVision — AI-Powered Precision Weed Detection and Management Platform

---

## 1. Introduction

### 1.1 Overview

AgriVision is an AI-powered precision agriculture platform designed to automate weed detection, crop identification, and intelligent herbicide management in agricultural fields. The system integrates deep learning-based object detection (YOLOv8 and Roboflow) with Explainable AI (XAI) powered by Google Gemini to provide farmers with actionable, transparent recommendations for weed control. A real-time weather pipeline further enriches decision-making by computing optimal spray windows based on live meteorological data.

The platform is architected as a full-stack web application with a **Flask (Python) backend** serving a custom-trained YOLOv8 model alongside a cloud-based Roboflow detector in a dual-model inference architecture. The **React (TypeScript) frontend**, built with Vite and TailwindCSS, provides a modern, responsive dashboard for image upload, real-time detection, batch processing, weather monitoring, and explainable AI panels. **Firebase** is used for authentication, Firestore for persistent storage, and **PostgreSQL** via an ETL pipeline for weather data ingestion.

The project is trained on the **CottonWeedDet12** dataset covering **12 weed species** commonly found in cotton and row-crop agriculture, including waterhemp, morningglory, ragweed, palmer amaranth, and others.

### 1.2 Problem Statement

Weed infestation is one of the most significant threats to global crop yield, accounting for up to 34% of annual crop losses worldwide. Traditional weed management approaches suffer from several critical shortcomings:

1. **Manual scouting is labour-intensive and impractical** at scale. Agronomists cannot physically inspect every section of large fields, leading to delayed detection and unchecked weed spread.
2. **Blanket herbicide application is unsustainable.** Uniform spraying leads to over-application of chemicals, increased input costs, environmental contamination of soil and groundwater, and the accelerated evolution of herbicide-resistant weed biotypes.
3. **Lack of decision transparency.** Existing AI-based detection tools often provide a class label and a confidence score but fail to explain *why* a particular treatment was recommended, making it difficult for farmers to trust or act on the suggestion.
4. **Weather-ignorant recommendations.** Herbicide efficacy is highly sensitive to environmental conditions — wind speed, temperature, humidity, and precipitation probability — yet most detection systems do not factor weather into their treatment plans.
5. **Single-model fragility.** Relying on a single detection model leads to missed detections or misclassifications, especially for visually similar weed–crop pairs.

AgriVision addresses these gaps through a dual-model detection architecture with cross-validation, explainable AI for transparent reasoning, and weather-aware spray scheduling.

### 1.3 Objectives

The primary objectives of this project are:

1. **Develop a custom-trained YOLOv8 object detection model** capable of identifying 12 weed species with per-class confidence thresholds tuned for precision.
2. **Implement a dual-model detection architecture** combining local YOLOv8 inference with cloud-based Roboflow detection, using IoU-based cross-model verification to reduce false positives.
3. **Build an Explainable AI (XAI) pipeline** that analyses detection features (spatial distribution, weed density, species diversity) and generates transparent herbicide recommendations, spray angle computations, and weather suitability assessments using Google Gemini.
4. **Integrate a real-time weather pipeline** using OpenMeteo API and PostgreSQL ETL to compute spray window suitability scores based on temperature, wind speed, humidity, and precipitation probability.
5. **Deliver a production-ready web application** with role-based authentication, batch image processing, real-time camera detection, interactive result overlays, and exportable detection logs.
6. **Ensure reliability through automated testing** with dedicated unit tests and integration tests covering all critical backend functions and API endpoints.

### 1.4 Scope of the Project

The scope encompasses the following functional modules:

| Module | Description |
|---|---|
| **Weed Detection Engine** | Dual-model YOLOv8 + Roboflow inference with per-class confidence thresholds and cross-model verification |
| **Crop Identification** | Automatic crop type recognition via Roboflow API |
| **Explainable AI (XAI)** | Feature extraction, spray angle computation, weather evaluation, herbicide recommendations via Gemini, and feature importance scoring |
| **Weather Pipeline** | PostgreSQL ETL ingestion, OpenMeteo API forecasting, Firestore sync, and spray window calculation |
| **Frontend Dashboard** | User and Admin dashboards, image upload with crop, camera capture, batch processing, weather widget, model performance dashboard |
| **Authentication & Data** | Firebase Authentication with role-based access (admin/user), Firestore for detection logs and activity tracking |
| **Testing Suite** | 22 unit tests + 25 integration tests using pytest |

**Out of scope:** Hardware integration (drones, IoT sensors), mobile native applications, and real-time video stream processing.

### 1.5 Social Relevance

AgriVision directly addresses several pressing societal challenges:

- **Food Security:** By enabling early and accurate weed detection, the platform helps protect crop yields that feed growing populations. Weeds compete for nutrients, water, and sunlight — reducing yields by 20–40% if unmanaged.
- **Environmental Sustainability:** Precision weed management reduces herbicide usage by targeting only infested areas rather than entire fields. This minimises chemical runoff into water bodies, preserves soil microbiome health, and slows the development of herbicide-resistant weeds.
- **Farmer Empowerment:** The explainable AI component transforms complex AI predictions into understandable, actionable advice. Farmers with no technical background can understand *why* a particular herbicide is recommended, what spray angle to use, and whether weather conditions permit safe application.
- **Economic Impact:** Precision application reduces input costs (herbicide, fuel, labour) while maximising efficacy. The weather-aware spray scheduling prevents wasted applications during unsuitable conditions.
- **Climate Adaptation:** The weather pipeline helps farmers adapt to increasingly unpredictable weather patterns by providing data-driven spray windows.

### 1.6 Organization of the Report

The remainder of this report is organised as follows:

- **Chapter 2 — Design:** Functional and non-functional requirements, system architecture, and design methodologies.
- **Chapter 3 — Implementation & Testing:** Detailed implementation of each module (dataset, backend, frontend, weather pipeline, spray window calculation), libraries used, and the complete testing strategy with test cases and execution results.
- **Chapter 4 — Results:** Sample outputs, comparison with existing methods, sustainability impact assessment, and evaluation metrics.
- **Chapter 5 — Future Scope:** Planned enhancements and extensions.

---

## 2. Design

### 2.1 Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01 | The system shall accept field images via file upload, camera capture, or batch upload | High |
| FR-02 | The system shall detect and classify weeds using a dual-model architecture (YOLOv8 + Roboflow) | High |
| FR-03 | The system shall apply per-class confidence thresholds to filter low-confidence detections | High |
| FR-04 | The system shall perform cross-model verification using IoU overlap to reclassify ambiguous detections | High |
| FR-05 | The system shall identify the crop type in the image via Roboflow API | Medium |
| FR-06 | The system shall generate weed removal techniques (manual, chemical, organic, mechanical) using Gemini AI | High |
| FR-07 | The system shall provide Explainable AI (XAI) analysis including spatial distribution, spray angle, weather suitability, herbicide recommendations, and feature importance scores | High |
| FR-08 | The system shall display real-time weather data with 7-day forecast and spray window suitability | High |
| FR-09 | The system shall support user authentication with role-based access (admin/user) via Firebase | High |
| FR-10 | The system shall persist detection history in Firestore with real-time updates | Medium |
| FR-11 | The system shall allow batch processing of multiple images with aggregated results | Medium |
| FR-12 | The system shall allow exporting detection data to CSV format | Low |
| FR-13 | The system shall render bounding box overlays on detected weeds and crops in the UI | High |
| FR-14 | The system shall compute and display model performance metrics (precision, recall, mAP) | Medium |

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-01 | **Performance:** YOLO inference shall complete within 3 seconds on CPU, 500ms on GPU | < 3s / < 500ms |
| NFR-02 | **Scalability:** The frontend shall be deployable as a static SPA on any CDN or hosting service | Vercel/Firebase Hosting |
| NFR-03 | **Availability:** The weather pipeline shall cache data for 30 minutes to reduce API calls and provide offline resilience | 30-min cache TTL |
| NFR-04 | **Security:** Firestore rules shall enforce row-level security — users can only access their own detections | Role-based rules |
| NFR-05 | **Usability:** The UI shall be responsive and support both desktop and mobile viewports | Responsive CSS |
| NFR-06 | **Reliability:** The system shall gracefully degrade when Roboflow or Gemini APIs are unavailable, falling back to YOLO-only detection | Graceful fallback |
| NFR-07 | **Maintainability:** Backend functions shall be covered by automated unit and integration tests | ≥ 47 test cases |
| NFR-08 | **Image Size Limit:** Uploaded images shall not exceed 10 MB | 10 MB max |
| NFR-09 | **Concurrency:** The Flask backend shall handle concurrent requests using threaded mode and ThreadPoolExecutor for parallel inference | Threaded + parallel |
| NFR-10 | **Remote Access:** The system shall support remote access via ngrok tunnel for field deployment | ngrok integration |

### 2.3 Design Methodologies

#### 2.3.1 System Architecture

The system follows a **three-tier architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION TIER                         │
│  React 19 + TypeScript + Vite + TailwindCSS 4               │
│  Pages: AuthPage, UserDashboard, AdminDashboard             │
│  Components: RealTimeDetector, BatchUploader, WeatherWidget │
│              ExplainableAIPanel, ResultsOverlay              │
│  Services: yoloService, weatherService, xaiService,         │
│            geminiService, firebaseService, locationService   │
│  State: Zustand                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│                    APPLICATION TIER                           │
│  Flask 3.0 + Flask-CORS                                      │
│  Endpoints: /analyze, /xai-explain, /get-treatment,          │
│             /identify-crop, /health, /status                 │
│  Models: YOLOv8 (local .pt) + Roboflow (cloud API)          │
│  AI: Google Gemini 2.0 Flash (herbicide + treatment)         │
│  Weather: OpenMeteo API (live fetch)                         │
│  Parallelism: ThreadPoolExecutor (YOLO ∥ Roboflow)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                      DATA TIER                               │
│  Firebase Firestore: detections, users, activities, weather  │
│  Firebase Storage: uploaded images                           │
│  Firebase Auth: email/password, role-based (admin/user)      │
│  PostgreSQL: ETL weather data (sync_weather.py)              │
│  OpenMeteo API: 7-day forecast, current conditions           │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Dual-Model Detection Pipeline

The detection pipeline employs a **parallel dual-model architecture** to maximise accuracy and resilience:

1. **YOLOv8 (Local):** Custom-trained on CottonWeedDet12 with 12 weed classes. Runs locally with per-class confidence thresholds (0.30–0.45) to control precision per species. Uses model fusion and warm-up for optimised inference.

2. **Roboflow (Cloud):** A separately trained model accessed via REST API. Provides crop detection capabilities that the YOLO model lacks.

3. **Cross-Model Verification:** After parallel inference, the system computes IoU (Intersection over Union) between YOLO weed detections and Roboflow crop detections. If a YOLO detection overlaps (IoU > 0.3) with a Roboflow crop detection and the YOLO confidence is below 50%, the detection is reclassified from weed to crop. This eliminates false positives where the weed-only YOLO model misidentifies crop plants.

4. **Result Merging (Frontend):** The frontend merges detections from both models, deduplicating overlapping boxes (IoU > 0.3) to produce a unified detection list.

#### 2.3.3 Explainable AI (XAI) Pipeline

The XAI system generates transparent, multi-factor recommendations through a five-stage pipeline:

1. **Feature Extraction:** From detection bounding boxes, extract weed species counts, density, weed-crop ratio, average confidence, and spatial distribution (clustered / scattered / inter-row / edge) via centroid variance analysis.
2. **Spray Angle Computation:** Compute optimal spray angle from image centre to weed cluster centroid using atan2. Map spatial patterns to nozzle types (Flat Fan, Hollow Cone, Deflector).
3. **Weather Evaluation:** Fetch live weather via OpenMeteo API and score suitability (0–100) based on temperature (10–30°C optimal), wind (< 15 km/h), humidity (40–90%), and precipitation (< 20%).
4. **Herbicide Recommendations:** Use Gemini 2.0 Flash to generate 2–3 herbicide recommendations with active ingredients, mode of action, application rates, safety assessment, and reasoning traces.
5. **Feature Importance:** Compute and rank six importance factors (Weed Count, Detection Confidence, Spatial Distribution, Weed Density, Species Diversity, Weather Risk) for explainability.

---

## 3. Implementation & Testing

### 3.1 Implementation Details

#### 3.1.1 Dataset

The project uses the **CottonWeedDet12** dataset, a large-scale weed detection dataset containing images of 12 weed species commonly found in cotton fields and row-crop agriculture:

| # | Class Name | Description |
|---|-----------|-------------|
| 0 | waterhemp | Broadleaf weed, herbicide-resistant species |
| 1 | morningglory | Vine-type broadleaf weed |
| 2 | ragweed | Allergenic broadleaf weed |
| 3 | cocklebur | Spiny-burred broadleaf weed |
| 4 | spurred_anteria | Grass-like weed |
| 5 | prickly_sida | Broadleaf weed with spiny stems |
| 6 | velvetleaf | Large-leaved broadleaf weed |
| 7 | palmer_amaranth | Aggressive broadleaf weed |
| 8 | redroot_pigweed | Common pigweed species |
| 9 | johnsongrass | Perennial grass weed |
| 10 | tall_morningglory | Tall vine-type broadleaf weed |
| 11 | sicklepod | Leguminous weed species |

**Dataset Configuration ([data.yaml](file:///c:/main%20project/Main-project-Wheat/data.yaml)):**
- **Format:** YOLO (images with corresponding label text files)
- **Split:** Train / Validation
- **Image Size:** 640 × 640 pixels (resized during inference)
- **Annotation Format:** YOLO format (class_id, x_center, y_center, width, height — normalised)

**Training Configuration:**
- **Base Model:** YOLOv8m (medium variant) pretrained on COCO, fine-tuned on CottonWeedDet12
- **Optimizer:** AdamW with learning rate 0.005, cosine annealing schedule (lr0=0.005, lrf=0.005)
- **Epochs:** 150 (with early stopping at patience=30)
- **Batch Size:** 2 (constrained by VRAM)
- **Augmentation:** Mosaic (1.0), MixUp (0.1), CopyPaste (0.1), horizontal flip (0.5), rotation (±5°), scale (0.5), HSV jitter
- **Target:** mAP@50 ≥ 0.85
- **Checkpoint:** Saved every 5 epochs; auto-resume from `last.pt`

#### 3.1.2 Backend Implementation

The backend is implemented in **Flask 3.0** ([server.py](file:///c:/main%20project/Main-project-Wheat/server.py), 1283 lines) and provides the following key capabilities:

**Model Loading and Optimisation:**
- Loads the custom-trained YOLOv8 model from [runs/detect/train6/weights/best.pt](file:///c:/main%20project/Main-project-Wheat/runs/detect/train6/weights/best.pt)
- Falls back to pretrained [yolov8n.pt](file:///c:/main%20project/Main-project-Wheat/yolov8n.pt) if custom weights are not found
- Applies `model.fuse()` for inference optimisation (layer fusion for Conv + BN)
- Configures PyTorch CPU thread count equal to available logical cores for parallelism
- Executes a warm-up pass with a blank 640×640 image to eliminate cold-start latency
- Image size for inference is 640 pixels with automatic aspect-ratio-preserving resize

**Per-Class Confidence Thresholds:**
Rather than applying a single global confidence threshold, the system uses species-specific thresholds:

| Tier | Classes | Threshold |
|------|---------|-----------|
| Common (well-trained) | waterhemp, palmer_amaranth, redroot_pigweed | 0.30 |
| Moderately common | velvetleaf, johnsongrass | 0.32 |
| Mid-range | morningglory, tall_morningglory | 0.35 |
| Less common | ragweed, cocklebur | 0.38 |
| Visually similar to crops | spurred_anteria, prickly_sida | 0.42 |
| Strictest | sicklepod | 0.45 |

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Main analysis — runs YOLO + Roboflow in parallel, cross-validates, and returns dual-model results |
| `/xai-explain` | POST | Explainable AI — extracts features, computes spray angle, evaluates weather, generates herbicide recommendations |
| `/identify-crop` | POST | Crop identification via Roboflow |
| `/get-treatment` | POST | Weed removal techniques via Gemini |
| `/health` | GET | Health check |
| `/status` | GET | Server status with device/model info |

**Cross-Model Verification Algorithm (Pseudocode):**
```
for each YOLO weed detection:
    for each Roboflow crop detection:
        iou = calculate_iou(yolo_box, roboflow_box)
        if iou > 0.3 AND yolo_confidence < 0.50:
            reclassify yolo detection as crop
            update counts
            break
```

**Gemini AI Integration:**
- Uses `google-genai` SDK with Gemini 2.0 Flash model
- Two prompt types: (1) weed removal techniques (manual/chemical/organic/mechanical), (2) herbicide recommendations with reasoning traces
- JSON response parsing with markdown code-block stripping

#### 3.1.3 Frontend Implementation

The frontend is built with **React 19**, **TypeScript**, **Vite 6**, and **TailwindCSS 4**, delivering a modern single-page application.

**Pages:**

| Page | File | Description |
|------|------|-------------|
| Authentication | [AuthPage.tsx](file:///c:/main%20project/Main-project-Wheat/src/pages/AuthPage.tsx) | Email/password login and registration with Firebase Auth |
| User Dashboard | [UserDashboard.tsx](file:///c:/main%20project/Main-project-Wheat/src/pages/UserDashboard.tsx) | Image analysis, detection results, weather widget, and XAI panel |
| Admin Dashboard | [AdminDashboard.tsx](file:///c:/main%20project/Main-project-Wheat/src/pages/AdminDashboard.tsx) | System statistics, user management, detection logs, and activity monitoring |

**Key Components:**

| Component | Description |
|-----------|-------------|
| [RealTimeDetector.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/RealTimeDetector.tsx) | Camera-based live weed detection with canvas overlay |
| [ImageUploadWithCrop.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/ImageUploadWithCrop.tsx) | Image upload with interactive cropping before analysis |
| [CameraCaptureWithCrop.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/CameraCaptureWithCrop.tsx) | Camera capture with region-of-interest cropping |
| [BatchUploader.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/BatchUploader.tsx) | Multi-image batch upload and sequential analysis |
| [BatchResultsPanel.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/BatchResultsPanel.tsx) | Aggregated results display for batch processing |
| [ExplainableAIPanel.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/ExplainableAIPanel.tsx) | Full XAI visualisation — features, spray angle, weather, herbicides, and feature importance |
| [WeatherWidget.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/WeatherWidget.tsx) | Current conditions, 7-day forecast, and spray window suitability |
| [ResultsOverlay.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/ResultsOverlay.tsx) | Bounding box overlays drawn on the analysed image |
| [RemovalTechniquesPanel.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/RemovalTechniquesPanel.tsx) | Displays Gemini-generated weed removal recommendations |
| [CropIdentificationCard.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/CropIdentificationCard.tsx) | Shows identified crop type with confidence |
| [ModelDashboard.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/ModelDashboard.tsx) | Model performance metrics and detection statistics |
| [MetricsPanel.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/MetricsPanel.tsx) | Precision, recall, and mAP metric cards |
| [Sidebar.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/Sidebar.tsx) | Navigation sidebar with role-based menu items |
| [ProtectedRoute.tsx](file:///c:/main%20project/Main-project-Wheat/src/components/ProtectedRoute.tsx) | Route guard enforcing authentication |

**State Management:** Zustand for lightweight global state.

**Services Layer:**

| Service | Function |
|---------|----------|
| [yoloService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/yoloService.ts) | Sends base64 image to `/analyze`, merges dual-model results, deduplicates via IoU |
| [weatherService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/weatherService.ts) | Fetches weather data directly from OpenMeteo API, computes spray scores, with 30-min in-memory cache |
| [xaiService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/xaiService.ts) | Calls `/xai-explain` endpoint with detections and location data |
| [geminiService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/geminiService.ts) | Direct Gemini API calls for treatment plans and structured image analysis with JSON schema |
| [firebaseService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/firebaseService.ts) | CRUD operations for detections, users, activities, statistics; real-time Firestore listeners; image upload; CSV export |
| [locationService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/locationService.ts) | Geolocation API integration for coordinate-based weather and XAI |

**Security (Firestore Rules):**
- Row-level security: users can only read/write their own detections
- Admin role can access all data
- Weather collection: read-only for authenticated users, write restricted to admins
- Activity logging: read for all authenticated users, write/delete for admins only

#### 3.1.4 Weather and ETL Pipeline

The weather subsystem operates through two complementary paths:

**Path 1 — Frontend Direct Fetch ([weatherService.ts](file:///c:/main%20project/Main-project-Wheat/src/services/weatherService.ts)):**
- Calls OpenMeteo API directly from the browser
- Fetches current conditions (temperature, humidity, wind, weather code) and 7-day daily forecast
- Computes spray suitability score (0–100) for each forecast day
- Results cached in-memory for 30 minutes per location (rounded to 2 decimal places)

**Path 2 — Backend ETL Sync ([sync_weather.py](file:///c:/main%20project/Main-project-Wheat/sync_weather.py)):**
- Reads historical weather data from a **PostgreSQL** database (ETL pipeline running via Docker)
- Fetches 7-day forecast from **OpenMeteo API**
- Compares freshness: uses PostgreSQL data if less than 1 hour old, otherwise uses OpenMeteo live data
- Builds forecast and spray window arrays
- Syncs combined data to **Firebase Firestore** (`/weather/{location_key}`)
- Designed to run as a scheduled job (every hour via cron or Windows Task Scheduler)

#### 3.1.5 Spray Window Calculation

The spray suitability score is calculated using a **penalty-based scoring system** starting at 100 and deducting points for unfavourable conditions:

| Factor | Optimal Range | Penalty |
|--------|--------------|---------|
| Temperature | 10–30°C (50–86°F) | -15 to -35 for out-of-range |
| Wind Speed | < 15 km/h | -10 to -40 depending on severity |
| Humidity | 40–90% | -10 to -20 for extreme values |
| Precipitation | < 20% probability | -15 to -50 based on probability |

**Decision thresholds:**
- **Score ≥ 80:** Excellent — all factors optimal
- **Score ≥ 60:** Acceptable — proceed with adjustments
- **Score ≥ 50:** Marginal — canSpray = true, spray with caution
- **Score < 50:** Poor — canSpray = false, DO NOT SPRAY

The XAI endpoint also evaluates weather in a more granular manner, providing per-factor reasoning strings that explain each score component (e.g., "22°C is in optimal range (10-30°C) for herbicide application").

#### 3.1.6 Libraries and Applications

**Backend (Python):**

| Library | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework and REST API |
| Flask-CORS | 4.0.0 | Cross-origin resource sharing |
| Ultralytics | ≥ 8.3.0 | YOLOv8 model training and inference |
| OpenCV (cv2) | 4.8.1 | Image processing and decoding |
| NumPy | 1.24.3 | Array operations for image data |
| Pillow | 10.1.0 | Image format handling |
| PyTorch | ≥ 2.0.1 | Deep learning inference engine |
| TorchVision | ≥ 0.15.2 | Vision model utilities |
| google-genai | ≥ 1.0.0 | Gemini AI API client |
| pyngrok | 7.0.1 | ngrok tunnel for remote access |
| python-dotenv | ≥ 1.0.0 | Environment variable management |
| Requests | ≥ 2.31.0 | HTTP client for Roboflow and OpenMeteo APIs |
| psycopg2 | — | PostgreSQL driver (weather ETL) |
| firebase-admin | — | Firebase Admin SDK (weather sync) |
| pytest | — | Test framework |

**Frontend (TypeScript/JavaScript):**

| Library | Version | Purpose |
|---------|---------|---------|
| React | 19.2.0 | UI component library |
| React DOM | 19.2.0 | DOM rendering |
| Vite | 6.2.0 | Build tool and dev server |
| TailwindCSS | 4.1.18 | Utility-first CSS framework |
| TypeScript | 5.8.2 | Type-safe JavaScript superset |
| Firebase | 12.7.0 | Authentication, Firestore, Storage |
| @google/genai | 1.30.0 | Gemini AI SDK for treatment plans |
| Zustand | 5.0.9 | Lightweight state management |
| React Router DOM | 7.11.0 | Client-side routing |
| Recharts | 3.7.0 | Data visualisation and charts |
| Lucide React | 0.554.0 | Icon library |
| react-image-crop | 11.0.10 | Image cropping component |
| react-hot-toast | 2.6.0 | Toast notifications |
| react-hook-form | 7.69.0 | Form state management |
| Zod | 4.3.4 | Schema validation |
| Radix UI | various | Accessible UI primitives (Dialog, Tabs, Avatar, Label, Separator) |
| date-fns | 4.1.0 | Date formatting utilities |
| clsx + tailwind-merge | — | Conditional className utilities |
| class-variance-authority | 0.7.1 | Component variant styling |

**External APIs:**

| API | Provider | Purpose |
|-----|----------|---------|
| OpenMeteo Forecast API | Open-Meteo | Weather data (current + 7-day forecast) |
| Roboflow Inference API | Roboflow | Cloud-based weed and crop detection |
| Gemini 2.0 Flash | Google | AI-powered herbicide recommendations and treatment plans |

**Infrastructure:**

| Service | Purpose |
|---------|---------|
| Firebase Authentication | User registration and login |
| Cloud Firestore | Detection logs, user profiles, activities, weather cache |
| Firebase Storage | Uploaded image storage |
| PostgreSQL | Weather data warehouse (ETL pipeline) |
| Docker | ETL pipeline containerisation |
| ngrok | Secure tunnel for remote backend access |

### 3.2 Testing

#### 3.2.1 Scope of Testing

Testing covers two levels:

1. **Unit Testing:** Isolated, deterministic tests for pure helper functions with no I/O dependencies. Each test runs in < 10 ms.
2. **Integration Testing:** Tests that exercise the full Flask request–response cycle using Flask's built-in test client, verifying that routing, validation, business logic, and JSON serialisation work correctly together.

The test suite is organised in the `tests/` directory with three modules:
- [test_unit_helpers.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_helpers.py) — 22 unit tests for [get_crop_type()](file:///c:/main%20project/Main-project-Wheat/server.py#152-215), [get_class_conf_threshold()](file:///c:/main%20project/Main-project-Wheat/server.py#100-103), and [resize_image_for_inference()](file:///c:/main%20project/Main-project-Wheat/server.py#217-224)
- [test_unit_xai.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_xai.py) — 25 unit tests for XAI functions: [extract_xai_features()](file:///c:/main%20project/Main-project-Wheat/server.py#750-828), [compute_spray_angle()](file:///c:/main%20project/Main-project-Wheat/server.py#830-899), [evaluate_weather_suitability()](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052), and [compute_feature_importance()](file:///c:/main%20project/Main-project-Wheat/server.py#1127-1180)
- [test_integration_api.py](file:///c:/main%20project/Main-project-Wheat/tests/test_integration_api.py) — 25 integration tests for all 6 API endpoints

#### 3.2.2 Minimum Test Case Requirement

A minimum of **47 test cases** are implemented across the three test modules, covering all critical backend functions and endpoints.

#### 3.2.3 Unit Testing — Isolated Functions

**Test Module 1: [test_unit_helpers.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_helpers.py) (22 test cases)**

| Test ID | Function | Description | Expected Result |
|---------|----------|-------------|-----------------|
| TC-U01 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Known weed "waterhemp" with crop "Wheat" | Returns "weed" |
| TC-U02 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Known weed "morningglory" | Returns "weed" |
| TC-U03 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Known weed "palmer_amaranth" | Returns "weed" |
| TC-U04 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | "ragweed" with crop "Corn" | Returns "weed" |
| TC-U05 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Label containing "weed" substring | Returns "weed" |
| TC-U06 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Label "wheat" matching crop keyword | Returns "crop" |
| TC-U07 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Label "corn" with crop "Corn" | Returns "crop" |
| TC-U08 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Roboflow "crop" class label | Returns "crop" |
| TC-U09 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Unknown label with crop context set | Returns "crop" |
| TC-U10 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Unknown label with "general crop" context | Returns "weed" |
| TC-U11 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Case-insensitive labels | Correct classification |
| TC-U12 | [get_crop_type](file:///c:/main%20project/Main-project-Wheat/server.py#152-215) | Non-plant objects ("person") | Returns "weed" |
| TC-U13 | [get_class_conf_threshold](file:///c:/main%20project/Main-project-Wheat/server.py#100-103) | "waterhemp" threshold | Returns 0.30 |
| TC-U14 | [get_class_conf_threshold](file:///c:/main%20project/Main-project-Wheat/server.py#100-103) | "sicklepod" (strictest) | Returns 0.45 |
| TC-U15 | [get_class_conf_threshold](file:///c:/main%20project/Main-project-Wheat/server.py#100-103) | "velvetleaf" | Returns 0.32 |
| TC-U16 | [get_class_conf_threshold](file:///c:/main%20project/Main-project-Wheat/server.py#100-103) | Unknown class name | Returns 0.35 (default) |
| TC-U17 | [get_class_conf_threshold](file:///c:/main%20project/Main-project-Wheat/server.py#100-103) | Case-insensitive lookup | Returns correct threshold |
| TC-U18 | [resize_image_for_inference](file:///c:/main%20project/Main-project-Wheat/server.py#217-224) | Image ≤ max_size | Returned unchanged |
| TC-U19 | [resize_image_for_inference](file:///c:/main%20project/Main-project-Wheat/server.py#217-224) | 1920×1080 → max 640 | max(h,w) ≤ 640 |
| TC-U20 | [resize_image_for_inference](file:///c:/main%20project/Main-project-Wheat/server.py#217-224) | 800×400 input | Aspect ratio preserved |
| TC-U21 | [resize_image_for_inference](file:///c:/main%20project/Main-project-Wheat/server.py#217-224) | Custom max_size=320 | max(h,w) ≤ 320 |
| TC-U22 | [resize_image_for_inference](file:///c:/main%20project/Main-project-Wheat/server.py#217-224) | Any input | Returns numpy ndarray |

**Test Module 2: [test_unit_xai.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_xai.py) (25 test cases)**

| Test ID | Function | Description | Expected Result |
|---------|----------|-------------|-----------------|
| TC-X01 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Counts weeds correctly | totalWeedCount == 3 |
| TC-X02 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Counts crops correctly | totalCropCount == 1 |
| TC-X03 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Lists weed species | All 3 species present |
| TC-X04 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Average confidence range | 0 ≤ avgConfidence ≤ 1 |
| TC-X05 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Weed density normalised | 0 ≤ weedDensity ≤ 1 |
| TC-X06 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Weed:crop ratio | 3.0 (3 weeds / 1 crop) |
| TC-X07 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Spatial distribution value | One of: clustered, scattered, inter-row, edge |
| TC-X08 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Dominant region coordinates | x, y between 0 and 1 |
| TC-X09 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | No weeds detected | density=0, ratio=0 |
| TC-X10 | [extract_xai_features](file:///c:/main%20project/Main-project-Wheat/server.py#750-828) | Empty detection list | All zeros, empty species |
| TC-S01 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | No weeds | pattern="spot", angle=0 |
| TC-S02 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Clustered weeds | pattern="directional" |
| TC-S03 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Inter-row weeds | angle=90° |
| TC-S04 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Edge weeds | pattern="directional" |
| TC-S05 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Scattered weeds | angle=360°, pattern="broadcast" |
| TC-S06 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Any scenario | nozzleType is non-empty string |
| TC-S07 | [compute_spray_angle](file:///c:/main%20project/Main-project-Wheat/server.py#830-899) | Any scenario | reasoning is non-empty string |
| TC-W01 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Ideal weather (22°C, 5 km/h) | score ≥ 80, canSpray=true |
| TC-W02 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Bad weather (40°C, 30 km/h) | score < 50, canSpray=false |
| TC-W03 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | None weather data | score=50, canSpray=true |
| TC-W04 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Temperature < 5°C | temp.suitable=false |
| TC-W05 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Wind > 25 km/h | wind.suitable=false |
| TC-W06 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Rain > 60% | precip.suitable=false |
| TC-W07 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Humidity < 30% | humidity.suitable=false |
| TC-W08 | [evaluate_weather_suitability](file:///c:/main%20project/Main-project-Wheat/server.py#943-1052) | Any response | All 7 required keys present |

#### 3.2.4 Integration Testing — API Endpoints

**Test Module 3: [test_integration_api.py](file:///c:/main%20project/Main-project-Wheat/tests/test_integration_api.py) (25 test cases)**

| Test ID | Endpoint | Description | Expected |
|---------|----------|-------------|----------|
| TC-I01 | GET `/health` | Returns health status | 200, status="ok" |
| TC-I02 | GET `/status` | Returns running status | 200, device + model info |
| TC-I03 | GET `/status` | Includes version field | version present |
| TC-I04 | POST `/analyze` | No request body | 400 or 500 |
| TC-I05 | POST `/analyze` | JSON without image field | 400, error message |
| TC-I06 | POST `/analyze` | Invalid base64 data | 400 or 500 |
| TC-I07 | POST `/analyze` | Valid image → dual model | 200, dualModel=true |
| TC-I08 | POST `/analyze` | YOLO section fields | detections, count, weedCount, cropCount, inferenceTime |
| TC-I09 | POST `/analyze` | Default crop name | cropType="Wheat" |
| TC-I10 | POST `/analyze` | Roboflow API error | 200 (YOLO-only fallback), error in roboflow object |
| TC-I11 | POST `/analyze` | Total inference time | totalInferenceTime is numeric |
| TC-I12 | POST `/analyze` | Whitespace-trimmed cropName | "  Corn  " → "Corn" |
| TC-I13 | POST `/xai-explain` | No request body | 400 or 500 |
| TC-I14 | POST `/xai-explain` | Valid detections | features, sprayingAngle, weatherSuitability, featureImportance |
| TC-I15 | POST `/xai-explain` | Empty detections | totalWeedCount=0, pattern="spot" |
| TC-I16 | POST `/xai-explain` | With location coordinates | Weather fetch triggered, score > 50 |
| TC-I17 | POST `/xai-explain` | Overall confidence range | 0 ≤ overallConfidence ≤ 1.0 |
| TC-I18 | POST `/xai-explain` | Timestamp format | generatedAt contains "T" (ISO) |
| TC-I19 | POST `/get-treatment` | No request body | 400 or 500 |
| TC-I20 | POST `/get-treatment` | Valid weed list | 200, manual + chemical fields |
| TC-I21 | POST `/get-treatment` | Gemini failure | 500, error message |
| TC-I22 | POST `/get-treatment` | Missing cropName | Defaults to "Wheat" |
| TC-I23 | POST `/identify-crop` | No image | 400 |
| TC-I24 | POST `/identify-crop` | Valid image | 200, cropName + confidence |
| TC-I25 | GET `/nonexistent-page` | Unknown route | 200 (SPA) or 404 |

#### 3.2.5 Test Execution Summary

| Test Module | Tests | Scope | Key Patterns |
|-------------|-------|-------|-------------|
| [test_unit_helpers.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_helpers.py) | 22 | Unit | Direct function calls, NumPy test images |
| [test_unit_xai.py](file:///c:/main%20project/Main-project-Wheat/tests/test_unit_xai.py) | 25 | Unit | Deterministic pure functions, fixture-based detections |
| [test_integration_api.py](file:///c:/main%20project/Main-project-Wheat/tests/test_integration_api.py) | 25 | Integration | Flask test client, `unittest.mock.patch` for API isolation |
| **Total** | **72** | — | — |

**Test infrastructure:** [conftest.py](file:///c:/main%20project/Main-project-Wheat/tests/conftest.py) provides shared pytest fixtures including `client` (Flask test client), `sample_image_640`, `sample_image_1920`, `sample_weed_detections`, `sample_no_weed_detections`, `sample_weather_good`, and `sample_weather_bad`.

---

## 4. Results

### 4.1 Sample Outputs

The system produces the following types of outputs per analysis:

**Detection Output (from `/analyze`):**
- Bounding boxes with labels, confidence scores, and weed/crop classification
- Per-model breakdown: YOLO detections vs. Roboflow detections
- Cross-validated merged results with IoU deduplication
- Total inference time and per-model latency

**XAI Output (from `/xai-explain`):**
- Spatial analysis: clustered/scattered/inter-row/edge classification
- Spray angle recommendation with nozzle type and reasoning
- Weather suitability: per-factor scores (temperature, wind, humidity, precipitation)
- Herbicide recommendations: 2–3 options with active ingredients, mode of action, application rate, and crop safety
- Feature importance: ranked list of 6 decision factors with scores and descriptions
- Overall confidence score (weighted combination of spray, detection, weather, and herbicide factors)

**Weather Output:**
- Current conditions (temperature, humidity, wind speed/direction, weather code)
- 7-day forecast with daily highs/lows, precipitation probability, and wind speed
- Spray window calendar with suitability scores and reasoning

### 4.2 Comparison with Existing Methods

| Feature | Traditional Scouting | Generic AI Detector | AgriVision |
|---------|---------------------|--------------------|----|
| Detection Method | Manual visual inspection | Single-model CNN | Dual-model (YOLOv8 + Roboflow) with cross-validation |
| Species Identification | Expert knowledge required | Generic "weed" label | 12 species-specific classes with per-class thresholds |
| Recommendation Type | Agronomist consultation | Class label + confidence | Explainable AI with herbicide reasoning, spray angle, nozzle type |
| Weather Integration | Separate weather check | None | Real-time weather scoring with per-factor suitability analysis |
| Herbicide Recommendations | Manual lookup | None | AI-generated with active ingredients, mode of action, and crop safety |
| False Positive Mitigation | None | None | Cross-model IoU verification (YOLO weed vs. Roboflow crop) |
| Transparency | Full (human expert) | Black box | Feature importance + reasoning traces |
| Scalability | Very limited | API-dependent | Local inference + cloud API with parallel execution |
| Batch Processing | Not feasible | Varies | Built-in batch upload with aggregated results |

### 4.3 Sustainability Impact Assessment

#### 4.3.1 Contribution of Project Features to SDGs

| SDG | Goal | AgriVision Contribution |
|-----|------|------------------------|
| **SDG 2** | Zero Hunger | Protects crop yields by enabling early weed detection and targeted intervention. Reduces crop loss from weed competition, contributing to food security. |
| **SDG 3** | Good Health and Well-being | Reduces human exposure to herbicides through precision application instead of blanket spraying. Weather-aware scheduling prevents spraying in high-wind conditions that cause drift. |
| **SDG 6** | Clean Water and Sanitation | Minimises herbicide runoff into water systems by recommending targeted spot-spraying over broadcast application. |
| **SDG 9** | Industry, Innovation, and Infrastructure | Demonstrates the application of Explainable AI in agriculture, combining deep learning with transparent decision-making for semi-autonomous farm operations. |
| **SDG 12** | Responsible Consumption and Production | Optimises herbicide usage through species-specific recommendations, reducing chemical waste and promoting sustainable agricultural inputs. |
| **SDG 13** | Climate Action | Weather pipeline helps farmers adapt to climate variability by providing data-driven spray windows based on real-time meteorological conditions. |
| **SDG 15** | Life on Land | Reduces soil contamination by minimising unnecessary herbicide application. Preserves biodiversity by targeting only identified weed species. |

#### 4.3.2 Evaluation Results and SDG Impact

The custom-trained YOLOv8 model achieved the following metrics on the CottonWeedDet12 validation set:

**Per-Class Performance (Top 3 Classes):**

| Class | Precision | Recall | F1 | mAP@50 | mAP@50-95 |
|-------|-----------|--------|-----|--------|-----------|
| morningglory | **0.7955** | **0.8502** | **0.8219** | **0.8447** | **0.7713** |
| waterhemp | 0.5040 | 0.8589 | 0.6353 | 0.6240 | 0.5931 |
| ragweed | 0.5251 | 0.8000 | 0.6340 | 0.6106 | 0.5385 |

**Overall Metrics:**

| Metric | Value |
|--------|-------|
| Mean Precision | 0.1520 |
| Mean Recall | 0.2091 |
| Mean F1 | 0.1743 |
| Accuracy | 0.4411 (44.11%) |
| mAP@50 | 0.1733 |
| mAP@50-95 | 0.1586 |

> **Note:** The overall mean metrics are low because 9 of 12 classes had insufficient training samples in the initial dataset split, resulting in 0.0 performance for those classes. The three classes with training data (waterhemp, morningglory, ragweed) demonstrate strong individual performance, with morningglory achieving 0.8447 mAP@50. Continued training on the full CottonWeedDet12 dataset (27 GB) is expected to significantly improve all-class metrics.

The dual-model architecture compensates for per-class weaknesses: when the local YOLO model lacks confidence, the Roboflow cloud model provides additional crop/weed detections, and cross-model verification reduces false positives.

---

## 5. Future Scope

The following enhancements are planned for future development:

1. **Complete Full-Dataset Training:** Resume training on the full 27 GB CottonWeedDet12 dataset with YOLOv11n architecture to achieve ≥ 0.85 mAP@50 across all 12 classes involving robust checkpointing and auto-resume capabilities.

2. **Drone and IoT Integration:** Extend the platform to accept real-time image streams from agricultural drones and field-mounted IoT cameras for automated, large-scale field monitoring.

3. **Mobile Application:** Develop a native mobile app (React Native or Flutter) to enable farmers to perform on-field analysis directly from their smartphones without requiring a laptop.

4. **Multi-Crop Support:** Extend the model training to cover additional crop types (wheat, rice, soybean, corn) with crop-specific weed profiles and herbicide recommendations.

5. **Prescription Map Generation:** Generate GPS-tagged prescription maps that can be loaded into variable-rate sprayer controllers for autonomous, spatially precise herbicide application.

6. **Temporal Analysis:** Track weed population trends over time using historical detection data stored in Firestore. Provide growth rate predictions and recommend preemptive interventions.

7. **Edge Deployment:** Optimise the YOLO model for edge devices (TensorRT, ONNX, OpenVINO) to enable real-time inference on embedded hardware at field stations without requiring internet connectivity.

8. **Advanced XAI Visualisations:** Implement Grad-CAM, SHAP, and LIME-based saliency maps overlaid on input images to show exactly which pixel regions triggered each detection.

9. **Community Knowledge Base:** Build a crowd-sourced weed identification database where farmers can submit and verify weed species, improving model accuracy through active learning.

10. **Regulatory Compliance Module:** Integrate local agricultural regulations and herbicide approval databases to ensure recommendations comply with regional pesticide usage laws and environmental guidelines.

---
