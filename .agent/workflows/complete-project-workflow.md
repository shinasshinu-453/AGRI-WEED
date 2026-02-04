---
description: Complete workflow for Main-project-Wheat (AgriVision) - Setup, Development, Training, and Deployment
---

# Complete Workflow for Main-project-Wheat (AgriVision)

This comprehensive workflow covers all aspects of running, developing, and deploying the AgriVision project - a YOLO-based wheat and weed detection system with Firebase integration and weather data ETL pipeline.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Project Setup](#initial-project-setup)
3. [Running the Complete System](#running-the-complete-system)
4. [Development Workflows](#development-workflows)
5. [Model Training Workflows](#model-training-workflows)
6. [Deployment Workflows](#deployment-workflows)
7. [Testing and Verification](#testing-and-verification)
8. [Troubleshooting](#troubleshooting)
9. [Maintenance Tasks](#maintenance-tasks)

---

## 🔧 Prerequisites

### Required Software
- **Node.js** (v16 or higher)
- **Python** (3.8 or higher)
- **Docker Desktop** (for ETL pipeline)
- **Git**
- **PowerShell** (Windows)

### Required Accounts & Keys
- **Firebase Account** - For database and cloud functions
- **Gemini API Key** - For AI recommendations
- **Ngrok Account** (optional) - For public URL exposure
- **Roboflow Account** (optional) - For dataset management

### System Requirements
- **RAM**: Minimum 8GB (16GB recommended for model training)
- **Storage**: At least 10GB free space
- **GPU**: Recommended for faster model training (optional)

---

## 🚀 Initial Project Setup

### Step 1: Clone and Navigate to Project
```powershell
cd "c:\main project\Main-project-Wheat"
```

### Step 2: Install Node.js Dependencies
```powershell
npm install
```

### Step 3: Install Python Dependencies

**Main Python requirements:**
```powershell
pip install -r requirements.txt
```

**Weather sync requirements:**
```powershell
pip install -r weather_requirements.txt
```

**Expected packages:**
- Flask 3.0.0
- flask-cors 4.0.0
- ultralytics 8.1.0 (YOLO)
- opencv-python 4.8.1.78
- numpy 1.24.3
- pillow 10.1.0
- torch 2.0.1
- torchvision 0.15.2
- pyngrok 7.0.1
- psycopg2-binary (for PostgreSQL)
- firebase-admin 6.0.0

### Step 4: Configure Environment Variables

**Create `.env.local` file** in the project root with:
```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Firebase Configuration
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id

# Ngrok (Optional)
NGROK_AUTH_TOKEN=your_ngrok_token
```

**Verify `.env` file** exists with Flask backend configuration.

### Step 5: Set Up Firebase

**Follow the detailed guide:**
1. Read `FIREBASE_SETUP.md` for complete instructions
2. Create a Firebase project at [Firebase Console](https://console.firebase.google.com)
3. Enable Firestore Database
4. Enable Firebase Storage (optional)
5. Download `serviceAccountKey.json` and place in project root
6. Create Firestore collections: `detections`, `users`, `activities`, `weatherData`

**Firestore Security Rules (for development):**
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.time < timestamp.date(2026, 12, 31);
    }
  }
}
```

### Step 6: Set Up ETL Pipeline (Weather Data)

**Navigate to ETL pipeline directory:**
```powershell
cd "C:\Users\shina\ETL PIPELINE"
```

**Verify `docker-compose.yml` exists** with services:
- Airflow (webserver, scheduler, worker)
- PostgreSQL database
- Redis

**Start Docker containers:**
```powershell
docker-compose up -d
```

**Access Airflow UI:**
- URL: http://localhost:8080
- Credentials: admin/admin

**Enable weather data DAG** in Airflow UI.

### Step 7: Verify Dataset Configuration

**Check `data.yaml` configuration:**
```yaml
path: C:/dataset/wheat_yolo_dataset
train: C:/dataset/wheat_yolo_dataset/images/train
val: C:/dataset/wheat_yolo_dataset/images/val

nc: 12
names: [waterhemp, morningglory, ragweed, cocklebur, spurred_anteria, 
        prickly_sida, velvetleaf, palmer_amaranth, redroot_pigweed, 
        johnsongrass, tall_morningglory, sicklepod]
```

**Verify dataset structure:**
```
C:/dataset/wheat_yolo_dataset/
├── images/
│   ├── train/
│   └── val/
└── labels/
    ├── train/
    └── val/
```

---

## 🏃 Running the Complete System

### Option 1: Automated Startup (Recommended)

**Start all services with one command:**
```powershell
.\start-all.ps1
```

**This script will:**
1. Start ETL Pipeline (Airflow + PostgreSQL + Redis)
2. Wait 30 seconds for Airflow initialization
3. Start Flask Backend with YOLO API
4. Wait 10 seconds for Flask startup
5. Start Vite Frontend (React)

**Access points:**
- **AgriVision UI**: http://localhost:5173
- **Airflow Dashboard**: http://localhost:8080 (admin/admin)
- **Flask API**: http://localhost:5000
- **PostgreSQL**: localhost:5432 (postgres/postgres)

**Stop all services:**
```powershell
.\stop-all.ps1
```

### Option 2: Manual Startup (Step-by-Step)

**Terminal 1 - ETL Pipeline:**
```powershell
cd "C:\Users\shina\ETL PIPELINE"
docker-compose up
```

**Terminal 2 - Flask Backend:**
```powershell
cd "c:\main project\Main-project-Wheat"
python server.py
```

**Optional: Flask with Ngrok (for public URL):**
```powershell
python server.py --ngrok
```

**Terminal 3 - Vite Frontend:**
```powershell
cd "c:\main project\Main-project-Wheat"
npm run dev
```

**Terminal 4 - Weather Sync (One-time or scheduled):**
```powershell
python sync_weather.py
```

Or use the batch file:
```powershell
.\run_weather_sync.bat
```

### Option 3: Development Mode (Frontend Only)

**If you only need the frontend:**
```powershell
npm run dev
```

**Access at:** http://localhost:5173

---

## 💻 Development Workflows

### Frontend Development

**Tech Stack:**
- React 19.2.0
- TypeScript
- Vite
- TailwindCSS 4.1.18
- React Router 7.11.0
- Firebase 12.7.0
- Recharts 3.7.0

**Key directories:**
- `src/components/` - Reusable UI components
- `src/pages/` - Page components
- `src/services/` - API and Firebase services
- `src/store/` - Zustand state management
- `src/utils/` - Utilities and helpers

**Development commands:**
```powershell
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Hot reload:** Enabled automatically with Vite

### Backend Development (Flask)

**Key files:**
- `server.py` - Main Flask application
- `sync_weather.py` - Weather data synchronization
- `test_sync.py` - Test weather sync functionality

**Start Flask server:**
```powershell
python server.py
```

**With Ngrok tunnel:**
```powershell
python server.py --ngrok
```

**API Endpoints:**
- `POST /detect` - YOLO image detection
- `GET /health` - Health check
- Additional endpoints in `server.py`

**Testing Flask endpoints:**
```powershell
# Health check
curl http://localhost:5000/health

# Test detection (with image)
curl -X POST -F "image=@test_image.jpg" http://localhost:5000/detect
```

### Firebase Cloud Functions Development

**Navigate to functions directory:**
```powershell
cd functions
```

**Install dependencies:**
```powershell
npm install
```

**Key function:**
- `weather_sync.py` - Syncs weather data from PostgreSQL to Firestore

**Deploy functions:**
```powershell
firebase deploy --only functions
```

**Deploy specific function:**
```powershell
firebase deploy --only functions:weatherSync
```

**View logs:**
```powershell
firebase functions:log
```

---

## 🤖 Model Training Workflows

### Downloading Dataset from Roboflow

**Edit `download_roboflow.py`** with your Roboflow API key and workspace:
```python
rf = Roboflow(api_key="YOUR_API_KEY")
project = rf.workspace("YOUR_WORKSPACE").project("YOUR_PROJECT")
```

**Run download:**
```powershell
python download_roboflow.py
```

**Output:** Dataset saved to configured location with train/val split

### Merging Multiple Datasets

**Use case:** Combine multiple YOLO datasets into one

**Edit `merge_datasets.py`** to specify source datasets and output path:
```python
dataset_paths = [
    "path/to/dataset1",
    "path/to/dataset2"
]
output_path = "C:/dataset/wheat_yolo_dataset"
```

**Run merge:**
```powershell
python merge_datasets.py
```

**Features:**
- Merges images and labels
- Preserves class mappings
- Creates train/val splits
- Generates updated `data.yaml`

### Organizing Dataset

**Fix dataset structure and annotations:**
```powershell
python organize_dataset.py
```

**Check annotations:**
```powershell
python check_annotations.py
```

**Fix corrupted annotations:**
```powershell
python fix_annotations.py
```

### Initial Model Training

**Basic training (new model):**
```powershell
python train_yolo.py
```

**Default configuration:**
- Model: YOLOv8n (nano)
- Epochs: 50
- Image size: 640
- Batch size: 16
- Data: `data.yaml`

**Expected output:**
- Trained model: `runs/detect/train/weights/best.pt`
- Training metrics: `runs/detect/train/results.png`
- Validation results: `runs/detect/train/val_batch*_pred.jpg`

### Continuing Training (Fine-tuning)

**Use case:** Resume training from a checkpoint or fine-tune existing model

**Edit `uptrain_yolo.py`** to specify:
```python
model = YOLO('runs/detect/train/weights/best.pt')  # or 'yolov8n.pt'
results = model.train(
    data='data.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    patience=20,
    resume=True  # Resume from last checkpoint
)
```

**Run continued training:**
```powershell
python uptrain_yolo.py
```

**Benefits:**
- Transfer learning from pre-trained weights
- Lower learning rate for fine-tuning
- Better convergence on specific dataset

### Model Hyperparameter Tuning

**Recommended parameters to tune:**

**1. Learning rate:**
```python
model.train(lr0=0.01, lrf=0.001)
```

**2. Batch size:**
```python
model.train(batch=8)  # or 16, 32 (depends on GPU memory)
```

**3. Image size:**
```python
model.train(imgsz=416)  # or 640, 800
```

**4. Augmentation:**
```python
model.train(
    hsv_h=0.015,      # HSV-Hue augmentation
    hsv_s=0.7,        # HSV-Saturation
    hsv_v=0.4,        # HSV-Value
    degrees=10.0,     # Rotation
    translate=0.1,    # Translation
    scale=0.5,        # Scale
    shear=0.0,        # Shear
    flipud=0.0,       # Flip up-down
    fliplr=0.5,       # Flip left-right
    mosaic=1.0        # Mosaic augmentation
)
```

**5. Model architecture:**
```python
model = YOLO('yolov8s.pt')  # or yolov8m.pt, yolov8l.pt, yolov8x.pt
```

**Experiment tracking:**
- Results saved in `runs/detect/train#/`
- Use TensorBoard for visualization:
  ```powershell
  tensorboard --logdir runs/detect
  ```

### Model Validation

**Validate trained model:**
```powershell
yolo val model=runs/detect/train/weights/best.pt data=data.yaml
```

**Evaluate on test set:**
```python
from ultralytics import YOLO

model = YOLO('runs/detect/train/weights/best.pt')
metrics = model.val(data='data.yaml', split='test')

print(f"mAP50: {metrics.box.map50}")
print(f"mAP50-95: {metrics.box.map}")
print(f"Precision: {metrics.box.p}")
print(f"Recall: {metrics.box.r}")
```

### Deploying Trained Model

**Replace model in production:**
```powershell
# Backup current model
cp yolov8n.pt yolov8n.pt.backup

# Copy new model
cp runs/detect/train/weights/best.pt yolov8n.pt
```

**Update `server.py`** if model path changed:
```python
model = YOLO('yolov8n.pt')  # or new model path
```

**Restart Flask server** to load new model.

---

## 🚀 Deployment Workflows

### Building for Production

**Build frontend:**
```powershell
npm run build
```

**Output:** `dist/` directory with optimized production bundle

**Preview production build locally:**
```powershell
npm run preview
```

### Deploying Frontend to Firebase Hosting

**Install Firebase CLI (if not installed):**
```powershell
npm install -g firebase-tools
```

**Login to Firebase:**
```powershell
firebase login
```

**Initialize Firebase (if not done):**
```powershell
firebase init hosting
```

**Configuration in `firebase.json`:**
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{
      "source": "**",
      "destination": "/index.html"
    }]
  }
}
```

**Deploy to Firebase:**
```powershell
firebase deploy --only hosting
```

**Access deployed app:**
- URL provided in console output
- Or check Firebase Console → Hosting

### Deploying Flask Backend

**Option 1: Deploy to Cloud Run (Recommended)**

**Create `Dockerfile`:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "server.py"]
```

**Build and deploy:**
```powershell
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/agrivision-backend
gcloud run deploy agrivision-backend --image gcr.io/YOUR_PROJECT_ID/agrivision-backend --platform managed --region us-central1 --allow-unauthenticated
```

**Option 2: Deploy to Heroku**

**Create `Procfile`:**
```
web: python server.py
```

**Deploy:**
```powershell
heroku create agrivision-backend
git push heroku main
```

**Option 3: Deploy with Ngrok (for testing)**

**Use existing script:**
```powershell
python server.py --ngrok
```

**Get public URL** from console output.

### Deploying Firebase Cloud Functions

**Deploy all functions:**
```powershell
firebase deploy --only functions
```

**Deploy weather sync function:**
```powershell
firebase deploy --only functions:weatherSync
```

**Set up scheduled execution (in Firebase Console):**
1. Go to Cloud Scheduler
2. Create job to trigger weather sync function
3. Set schedule: `0 */6 * * *` (every 6 hours)

### Environment Variables for Production

**Set Firebase environment variables:**
```powershell
firebase functions:config:set postgres.host="YOUR_POSTGRES_HOST"
firebase functions:config:set postgres.db="weather_db"
firebase functions:config:set postgres.user="postgres"
firebase functions:config:set postgres.password="YOUR_PASSWORD"
```

**Verify configuration:**
```powershell
firebase functions:config:get
```

---

## 🧪 Testing and Verification

### Testing Weather Sync

**Run test script:**
```powershell
python test_sync.py
```

**This tests:**
- PostgreSQL connection
- Data retrieval from ETL pipeline
- Firestore write operations
- Error handling

**Manual sync:**
```powershell
python sync_weather.py
```

**Verify in Firestore:**
1. Open Firebase Console
2. Go to Firestore Database
3. Check `weatherData` collection
4. Verify recent entries

### Testing YOLO Detection

**Test with sample image:**
```python
from ultralytics import YOLO
from PIL import Image

model = YOLO('yolov8n.pt')
results = model('path/to/test_image.jpg')

for r in results:
    print(f"Detected {len(r.boxes)} objects")
    r.show()  # Display image with bounding boxes
```

**Test via Flask API:**
```powershell
curl -X POST -F "image=@test_image.jpg" http://localhost:5000/detect
```

### Testing Frontend Features

**Manual testing checklist:**

**User Dashboard:**
- [ ] Upload image for detection
- [ ] View detection results
- [ ] See weed/crop classification
- [ ] View AI recommendations
- [ ] Check weather data display

**Admin Dashboard:**
- [ ] View statistics (total detections, weeds, crops)
- [ ] Check interactive charts (line chart, pie chart)
- [ ] Filter detection history
- [ ] Search detections by filename
- [ ] Export CSV
- [ ] View activity feed
- [ ] Manage to-do list

**Firebase Integration:**
- [ ] Real-time data updates
- [ ] Live activity feed
- [ ] Statistics auto-refresh
- [ ] Toast notifications

**Responsive Design:**
- [ ] Mobile view (< 768px)
- [ ] Tablet view (768px - 1024px)
- [ ] Desktop view (> 1024px)

### Performance Testing

**Frontend performance:**
```powershell
npm run build
npm run preview
```

**Use Lighthouse** in Chrome DevTools:
1. Open DevTools (F12)
2. Go to Lighthouse tab
3. Run audit
4. Target scores: >90 for Performance, Accessibility, Best Practices, SEO

**Backend performance:**
```powershell
# Install locust for load testing
pip install locust

# Create locustfile.py and run
locust -f locustfile.py
```

### Integration Testing

**Test complete flow:**
1. Start all services with `.\start-all.ps1`
2. Verify Airflow DAG runs successfully
3. Check weather data syncs to Firestore
4. Upload image for detection
5. Verify detection results saved to Firestore
6. Check admin dashboard updates in real-time
7. Verify AI recommendations include weather insights

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Firebase Connection Errors

**Symptom:** "Firebase not configured" error

**Solution:**
- Verify `.env.local` exists with all Firebase variables
- Restart dev server: `npm run dev`
- Check Firebase Console for project status
- Verify `serviceAccountKey.json` is present

#### 2. ETL Pipeline Not Starting

**Symptom:** Docker containers fail to start

**Solution:**
```powershell
# Check Docker Desktop is running
docker --version

# Stop all containers
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d

# Check logs
docker-compose logs -f
```

#### 3. Port Already in Use

**Symptom:** "Port 5000 already in use" or "Port 5173 already in use"

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :5000

# Kill process
taskkill /PID <process_id> /F

# Or change port in vite.config.ts or server.py
```

#### 4. Weather Sync Fails

**Symptom:** `test_sync.py` fails

**Solution:**
- Verify ETL pipeline is running
- Check PostgreSQL connection: `psql -h localhost -U postgres -d weather_db`
- Verify Firebase credentials
- Check `sync_weather.py` for correct database connection params
- Review logs for specific error messages

#### 5. YOLO Model Not Loading

**Symptom:** "Model file not found" or "Invalid model"

**Solution:**
- Verify `yolov8n.pt` exists in project root
- Re-download model:
  ```python
  from ultralytics import YOLO
  model = YOLO('yolov8n.pt')  # Auto-downloads if missing
  ```
- Check file permissions
- Verify model path in `server.py`

#### 6. Dataset Path Issues

**Symptom:** Training fails with "Dataset not found"

**Solution:**
- Verify dataset exists at `C:/dataset/wheat_yolo_dataset/`
- Check `data.yaml` paths are correct
- Use forward slashes in paths (even on Windows)
- Ensure images and labels directories have matching files

#### 7. NPM Install Fails

**Symptom:** Dependency installation errors

**Solution:**
```powershell
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -r node_modules
rm package-lock.json

# Reinstall
npm install
```

#### 8. Ngrok Connection Issues

**Symptom:** Ngrok tunnel fails to start

**Solution:**
- Verify ngrok is installed: `ngrok version`
- Check auth token is set in `.env`
- Restart ngrok: stop Flask and run `python server.py --ngrok` again
- Check ngrok dashboard for active tunnels

#### 9. Firestore Security Rules Blocking Writes

**Symptom:** "Permission denied" in Firestore

**Solution:**
- Update security rules in Firebase Console
- For development, use permissive rules (see Setup section)
- For production, implement proper authentication
- Check Firebase Console → Rules tab for rule deployment status

#### 10. Model Training Out of Memory

**Symptom:** "CUDA out of memory" or system freeze

**Solution:**
- Reduce batch size in training script: `batch=8` or `batch=4`
- Reduce image size: `imgsz=416`
- Close other applications
- Use CPU if GPU is unavailable: `device='cpu'`
- Enable mixed precision training: `amp=True`

---

## 🔧 Maintenance Tasks

### Regular Maintenance (Weekly)

**1. Update dependencies:**
```powershell
# Frontend
npm outdated
npm update

# Python
pip list --outdated
pip install --upgrade <package_name>
```

**2. Clean up old model runs:**
```powershell
# Remove old training runs (keep last 5)
cd runs/detect
# Manually delete old train folders
```

**3. Monitor storage:**
- Check Firestore usage in Firebase Console
- Monitor dataset size
- Clean up old Docker volumes:
  ```powershell
  docker system prune -a
  ```

**4. Backup important data:**
```powershell
# Backup trained models
cp runs/detect/train/weights/best.pt backups/model_$(date +%Y%m%d).pt

# Export Firestore data (via Firebase Console)
```

### Monthly Maintenance

**1. Review and optimize Firestore indexes:**
- Check Firebase Console → Firestore → Indexes
- Add composite indexes for frequently queried fields

**2. Update security rules:**
- Review and tighten Firestore security rules
- Update authentication requirements

**3. Performance audit:**
- Run Lighthouse audit on deployed frontend
- Analyze backend API response times
- Check ETL pipeline logs for errors

**4. Dataset review:**
- Add new training images
- Remove poor quality images
- Retrain model if significant new data added

### Quarterly Maintenance

**1. Major dependency updates:**
- Update React, Vite, and other major packages
- Update Python packages
- Test thoroughly after updates

**2. Security audit:**
- Review API keys and tokens
- Rotate sensitive credentials
- Update `.gitignore` to ensure no secrets committed

**3. Cost optimization:**
- Review Firebase usage and billing
- Optimize Firestore queries
- Reduce unnecessary cloud function invocations

**4. Documentation update:**
- Update this workflow with new processes
- Document any custom modifications
- Update README.md

---

## 📞 Support and Resources

### Documentation
- **Firebase**: https://firebase.google.com/docs
- **YOLO (Ultralytics)**: https://docs.ultralytics.com
- **React**: https://react.dev
- **Vite**: https://vitejs.dev

### Project-Specific Docs
- `FIREBASE_SETUP.md` - Firebase configuration guide
- `NGROK_SETUP.md` - Ngrok setup instructions
- `README.md` - Quick start guide
- `security improvemeents.txt` - Security recommendations

### Useful Commands Quick Reference

**Start all services:**
```powershell
.\start-all.ps1
```

**Stop all services:**
```powershell
.\stop-all.ps1
```

**Frontend dev:**
```powershell
npm run dev
```

**Backend dev:**
```powershell
python server.py
```

**Train model:**
```powershell
python uptrain_yolo.py
```

**Sync weather:**
```powershell
python sync_weather.py
```

**Deploy to Firebase:**
```powershell
npm run build && firebase deploy
```

---

## 🎯 Quick Start Checklist

Use this checklist for new team members or fresh installations:

- [ ] Install Node.js, Python, Docker
- [ ] Clone repository
- [ ] Run `npm install`
- [ ] Run `pip install -r requirements.txt`
- [ ] Create `.env.local` with all required keys
- [ ] Set up Firebase project and download `serviceAccountKey.json`
- [ ] Verify dataset at `C:/dataset/wheat_yolo_dataset/`
- [ ] Start ETL pipeline: `docker-compose up -d` (in ETL directory)
- [ ] Run `.\start-all.ps1` to start all services
- [ ] Access UI at http://localhost:5173
- [ ] Test image detection
- [ ] Verify weather data in Firestore
- [ ] Run `python test_sync.py` to test integrations

---

**Last Updated:** February 2026
**Maintained By:** AgriVision Team
**Version:** 1.0.0
