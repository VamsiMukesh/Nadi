# HealthSync — Healthcare IoT Ecosystem

> A full-stack, AI-powered Healthcare IoT platform that connects wearable devices, collects real-time vitals, and delivers intelligent health insights via machine learning.

---

## 🏗️ Project Architecture

```
healthsync/
├── frontend/                  # React Dashboard (UI)
│   ├── src/
│   │   └── App.jsx            # Main application — all tabs & components
│   └── package.json
├── backend/                   # Flask REST API
│   └── app.py                 # All API endpoints, auth, alerts, AI routes
├── ml_model/                  # Machine Learning module
│   └── ml_model.py            # Data generation, training, prediction pipeline
├── iot_simulator/             # IoT Device Simulator
│   └── iot_simulator.py       # 5 simulated devices with realistic data
├── docs/                      # Project documentation
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

---

## 🔬 System Components

### 1. IoT Devices (Simulated)
| Device               | Metrics                        | Interval |
|----------------------|--------------------------------|----------|
| Smart Watch Pro      | HR, HRV, Steps, Calories, Stress | 5s       |
| Blood Pressure Cuff  | Systolic BP, Diastolic BP      | 30s      |
| Pulse Oximeter       | SpO2, Heart Rate               | 3s       |
| Smart Thermometer    | Temperature                    | 60s      |
| Sleep Tracker Band   | Sleep Hours, HRV               | 300s     |

### 2. Backend API (Flask)
- **Auth**: Login / Register with JWT tokens
- **Vitals**: Ingest, query latest, history, summary stats
- **Goals**: CRUD for daily health goals
- **Devices**: Register, status updates, removal
- **Notifications**: Real-time alerts and reminders
- **AI Endpoints**: Health score, insights, risk prediction, trend analysis
- **Export**: CSV and JSON data export

### 3. ML Models
| Model                | Algorithm                 | Task                                |
|----------------------|---------------------------|-------------------------------------|
| Risk Classifier      | Random Forest             | Predict risk: Low/Moderate/High/Critical |
| Score Regressor      | Gradient Boosting         | Predict health score 0–100          |

**Features engineered**: BMI, pulse pressure, MAP, HRV/stress ratio, activity intensity, sleep score, recovery index

### 4. Frontend Dashboard
- **Dashboard**: Live vitals cards, sparklines, bar charts, BP trend chart
- **AI Analysis**: Health score breakdown, trend analysis, AI recommendations
- **Goals**: Daily goal tracking with progress bars
- **Devices**: Connected devices status, battery, architecture diagram
- **History**: 14-day vitals log with export options

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm / npx

### 1. Clone & Setup
```bash
git clone <repo-url>
cd healthsync
cp .env.example .env          # Edit .env with your values
```

### 2. Install Dependencies
```bash
# Python
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Train ML Models
```bash
cd ml_model
python ml_model.py            # Trains and saves models
```

### 4. Start Backend
```bash
cd backend
python app.py                 # Starts on http://localhost:5000
```

### 5. Start Frontend
```bash
cd frontend
npm start                     # Starts on http://localhost:3000
```

### 6. Start IoT Simulator (optional)
```bash
cd iot_simulator
python iot_simulator.py       # Simulates 5 IoT devices pushing data
```

---

## 📡 API Reference

### Health Check
```
GET  /api/health
```

### Auth
```
POST /api/auth/login          → { email, password }
POST /api/auth/register       → { name, email, password, age, gender, weight_kg, height_cm }
```

### Vitals
```
POST /api/vitals              → Ingest a reading (from IoT)
GET  /api/vitals/latest       → Most recent reading
GET  /api/vitals/history      → ?days=30&page=1&per_page=50
GET  /api/vitals/summary      → Aggregated stats for period
```

### Goals
```
GET  /api/goals               → All user goals
POST /api/goals               → Create goal
PUT  /api/goals/:id           → Update goal (current progress)
DEL  /api/goals/:id           → Delete goal
```

### Devices
```
GET  /api/devices             → All user devices
POST /api/devices             → Register new device
PUT  /api/devices/:id/status  → Update status/battery
DEL  /api/devices/:id         → Remove device
```

### AI / ML
```
GET  /api/ai/health-score     → Weighted health score + breakdown
GET  /api/ai/insights         → AI-generated health insights
POST /api/ai/predict-risk     → Risk prediction from vitals payload
GET  /api/ai/trend-analysis   → 7-day vs 14-day trend comparison
```

### Notifications & Alerts
```
GET  /api/notifications       → All notifications
PUT  /api/notifications/:id/read
PUT  /api/notifications/read-all
GET  /api/alerts              → ?resolved=false
PUT  /api/alerts/:id/resolve
```

### Export
```
GET  /api/export/csv          → ?days=30
GET  /api/export/json         → ?days=30
```

---

## 🛡️ Security & Compliance Considerations

| Requirement | Implementation |
|-------------|----------------|
| HIPAA       | Encrypt data at rest & in transit (TLS 1.3). Audit logging. Access controls. |
| GDPR        | User consent flow. Data deletion endpoint. Anonymization option. |
| FDA         | Software documentation (this README). Version control. Validation testing. |
| Auth        | JWT tokens. Password hashing (bcrypt). Role-based access. |
| Network     | HTTPS only. IP whitelisting for IoT device endpoints. |

---

## 📊 Deployment (Production)

### Backend
```bash
# Use Gunicorn for production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend
```bash
cd frontend
npm run build                 # Creates /build directory
# Serve with nginx or deploy to Vercel/Netlify
```

### Database
Replace in-memory DB with MongoDB or PostgreSQL (see `.env.example`).

### IoT Devices
In production, replace the simulator with actual MQTT or COAP clients on embedded devices (ESP32, Arduino with WiFi).

---

## 📝 Dependencies

| Layer          | Libraries                                      |
|----------------|-------------------------------------------------|
| Frontend       | React 18, React DOM                             |
| Backend        | Flask, Flask-CORS                               |
| ML             | scikit-learn, pandas, numpy, joblib             |
| IoT Simulator  | requests, colorama                              |
| DB (prod)      | pymongo / psycopg2 / sqlalchemy                 |

---

## 👥 Team Roles (Suggested)

| Role                    | Responsibility                                   |
|-------------------------|--------------------------------------------------|
| Frontend Developer      | React dashboard, charts, UI/UX                   |
| Backend Developer       | Flask API, database, auth, alerts                |
| ML Engineer             | Model training, feature engineering, deployment  |
| IoT Engineer            | Device simulation, edge computing, MQTT          |
| DevOps / QA             | CI/CD, testing, deployment, documentation        |

---

## 📌 Future Enhancements

- MQTT protocol for real IoT device communication
- WebSocket for true real-time dashboard updates
- Mobile companion app (React Native)
- Cloud deployment (AWS / GCP) with auto-scaling
- Deep learning models (LSTM for time-series prediction)
- Telemedicine integration
- Electronic Health Records (EHR) integration

---

*Built for Final Year Project — Engineering Department*
*HealthSync IoT Ecosystem — AI-Powered Health Monitoring*
