"""
HealthSync - Healthcare IoT Backend Server
==========================================
Flask-based REST API handling:
  - Real-time vitals ingestion from IoT devices
  - User health data CRUD operations
  - AI/ML prediction endpoints
  - Goal tracking and progress
  - Device management
  - Notification system
  - Data export (CSV, JSON)

Requirements:
    pip install flask flask-cors pymongo scikit-learn pandas numpy python-dotenv

Run:
    python app.py
"""

import os
import json
import uuid
import random
import math
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from functools import wraps
import hashlib
import hmac

# ─── APP INITIALIZATION ─────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "healthsync-dev-key-change-in-prod")
    DATABASE_URI = os.environ.get("DATABASE_URI", "sqlite:///healthsync.db")
    AI_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "ml_model", "trained_model.pkl")
    MAX_HISTORY_DAYS = 90
    ALERT_THRESHOLDS = {
        "heart_rate": {"min": 40, "max": 120},
        "spo2": {"min": 90, "max": 100},
        "temperature": {"min": 35.5, "max": 38.5},
        "systolic_bp": {"min": 80, "max": 160},
        "diastolic_bp": {"min": 50, "max": 110},
    }

config = Config()

# ─── IN-MEMORY DATABASE (Replace with MongoDB/PostgreSQL in production) ───────
db = {
    "users": {
        "user_001": {
            "id": "user_001",
            "name": "John Doe",
            "email": "john@example.com",
            "age": 35,
            "gender": "male",
            "weight_kg": 75,
            "height_cm": 178,
            "created_at": datetime.now().isoformat(),
        }
    },
    "vitals": [],          # List of vital readings
    "goals": [],           # User health goals
    "devices": [],         # Registered IoT devices
    "notifications": [],   # User notifications
    "alerts": [],          # System alerts
}

# ─── SEED DATA ────────────────────────────────────────────────────────────────
def seed_data():
    """Generate realistic sample data for the last 30 days."""
    now = datetime.now()

    # Seed devices
    db["devices"] = [
        {"id": "dev_001", "user_id": "user_001", "name": "Smart Watch Pro", "type": "smartwatch", "mac": "AA:BB:CC:DD:01", "status": "connected", "battery": 82, "firmware": "2.4.1", "last_sync": now.isoformat(), "registered_at": (now - timedelta(days=30)).isoformat()},
        {"id": "dev_002", "user_id": "user_001", "name": "BP Cuff", "type": "blood_pressure", "mac": "AA:BB:CC:DD:02", "status": "connected", "battery": 67, "firmware": "1.2.0", "last_sync": (now - timedelta(minutes=5)).isoformat(), "registered_at": (now - timedelta(days=25)).isoformat()},
        {"id": "dev_003", "user_id": "user_001", "name": "Pulse Oximeter", "type": "pulse_ox", "mac": "AA:BB:CC:DD:03", "status": "connected", "battery": 91, "firmware": "3.0.2", "last_sync": now.isoformat(), "registered_at": (now - timedelta(days=20)).isoformat()},
        {"id": "dev_004", "user_id": "user_001", "name": "Smart Thermometer", "type": "thermometer", "mac": "AA:BB:CC:DD:04", "status": "idle", "battery": 45, "firmware": "1.0.5", "last_sync": (now - timedelta(hours=2)).isoformat(), "registered_at": (now - timedelta(days=15)).isoformat()},
        {"id": "dev_005", "user_id": "user_001", "name": "Sleep Tracker", "type": "sleep_band", "mac": "AA:BB:CC:DD:05", "status": "connected", "battery": 73, "firmware": "2.1.3", "last_sync": (now - timedelta(hours=8)).isoformat(), "registered_at": (now - timedelta(days=10)).isoformat()},
    ]

    # Seed goals
    db["goals"] = [
        {"id": "goal_001", "user_id": "user_001", "label": "Daily Steps", "target": 10000, "unit": "steps", "current": 7842, "icon": "🚶", "color": "#4ade80", "created_at": (now - timedelta(days=7)).isoformat()},
        {"id": "goal_002", "user_id": "user_001", "label": "Water Intake", "target": 8, "unit": "glasses", "current": 6, "icon": "💧", "color": "#60a5fa", "created_at": (now - timedelta(days=7)).isoformat()},
        {"id": "goal_003", "user_id": "user_001", "label": "Sleep Duration", "target": 8, "unit": "hrs", "current": 7.2, "icon": "🌙", "color": "#a78bfa", "created_at": (now - timedelta(days=7)).isoformat()},
        {"id": "goal_004", "user_id": "user_001", "label": "Calories Burned", "target": 2500, "unit": "kcal", "current": 2150, "icon": "🔥", "color": "#fb923c", "created_at": (now - timedelta(days=7)).isoformat()},
    ]

    # Seed 30 days of vitals
    for day_offset in range(30):
        ts = (now - timedelta(days=day_offset)).replace(hour=random.randint(6, 22), minute=random.randint(0, 59))
        db["vitals"].append({
            "id": str(uuid.uuid4()),
            "user_id": "user_001",
            "device_id": "dev_001",
            "timestamp": ts.isoformat(),
            "heart_rate": random.randint(58, 95),
            "spo2": round(96.5 + random.random() * 3, 1),
            "temperature": round(36.2 + random.random() * 1.0, 1),
            "systolic_bp": random.randint(108, 138),
            "diastolic_bp": random.randint(68, 90),
            "steps": random.randint(3000, 13000),
            "sleep_hours": round(5.5 + random.random() * 3.0, 1),
            "hrv": random.randint(35, 75),
            "stress_level": random.randint(15, 75),
            "calories": random.randint(1600, 2800),
            "hydration_glasses": random.randint(3, 10),
        })

    # Seed notifications
    db["notifications"] = [
        {"id": "notif_001", "user_id": "user_001", "type": "reminder", "message": "Time to drink water!", "read": False, "created_at": (now - timedelta(minutes=2)).isoformat()},
        {"id": "notif_002", "user_id": "user_001", "type": "achievement", "message": "Great job hitting 7k steps!", "read": False, "created_at": (now - timedelta(hours=1)).isoformat()},
        {"id": "notif_003", "user_id": "user_001", "type": "report", "message": "Sleep score report is ready", "read": True, "created_at": (now - timedelta(hours=3)).isoformat()},
    ]

seed_data()


# ─── MIDDLEWARE / HELPERS ─────────────────────────────────────────────────────
def get_user_id():
    """Extract user_id from token or default (for demo)."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        # In production: decode JWT here
        return "user_001"
    return "user_001"  # Demo default


def success_response(data, status=200, message="Success"):
    return jsonify({"status": "success", "message": message, "data": data}), status


def error_response(message, status=400):
    return jsonify({"status": "error", "message": message, "data": None}), status


def check_alerts(vitals_entry):
    """Check vital values against alert thresholds and create alerts if needed."""
    alerts = []
    thresholds = config.ALERT_THRESHOLDS

    if vitals_entry.get("heart_rate"):
        hr = vitals_entry["heart_rate"]
        if hr < thresholds["heart_rate"]["min"]:
            alerts.append({"type": "critical", "metric": "heart_rate", "value": hr, "message": f"Heart rate critically low: {hr} bpm"})
        elif hr > thresholds["heart_rate"]["max"]:
            alerts.append({"type": "critical", "metric": "heart_rate", "value": hr, "message": f"Heart rate critically high: {hr} bpm"})

    if vitals_entry.get("spo2"):
        spo2 = vitals_entry["spo2"]
        if spo2 < thresholds["spo2"]["min"]:
            alerts.append({"type": "critical", "metric": "spo2", "value": spo2, "message": f"SpO2 dangerously low: {spo2}%"})

    if vitals_entry.get("temperature"):
        temp = vitals_entry["temperature"]
        if temp > thresholds["temperature"]["max"]:
            alerts.append({"type": "warning", "metric": "temperature", "value": temp, "message": f"Elevated temperature: {temp}°C"})

    return alerts


# ─── ROUTES: AUTH & HEALTH CHECK ─────────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health_check():
    return success_response({"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").lower()
    password = data.get("password", "")

    # Demo: accept any credentials matching seeded user
    if email == "john@example.com" and password == "demo123":
        token = "demo_jwt_token_" + str(uuid.uuid4())
        return success_response({"token": token, "user_id": "user_001", "name": "John Doe", "email": email})
    return error_response("Invalid credentials", 401)


@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    required = ["name", "email", "password", "age", "gender", "weight_kg", "height_cm"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error_response(f"Missing fields: {', '.join(missing)}")

    user_id = "user_" + str(uuid.uuid4())[:6]
    db["users"][user_id] = {
        "id": user_id,
        "name": data["name"],
        "email": data["email"].lower(),
        "age": data["age"],
        "gender": data["gender"],
        "weight_kg": data["weight_kg"],
        "height_cm": data["height_cm"],
        "created_at": datetime.now().isoformat(),
    }
    token = "jwt_token_" + str(uuid.uuid4())
    return success_response({"token": token, "user_id": user_id, "name": data["name"]}, 201, "Registration successful")


# ─── ROUTES: VITALS ──────────────────────────────────────────────────────────
@app.route("/api/vitals", methods=["POST"])
def ingest_vitals():
    """
    Ingest a single vitals reading from an IoT device.
    Called by the IoT simulator or edge gateway.
    """
    data = request.get_json()
    user_id = get_user_id()

    entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "device_id": data.get("device_id", "unknown"),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "heart_rate": data.get("heart_rate"),
        "spo2": data.get("spo2"),
        "temperature": data.get("temperature"),
        "systolic_bp": data.get("systolic_bp"),
        "diastolic_bp": data.get("diastolic_bp"),
        "steps": data.get("steps"),
        "sleep_hours": data.get("sleep_hours"),
        "hrv": data.get("hrv"),
        "stress_level": data.get("stress_level"),
        "calories": data.get("calories"),
        "hydration_glasses": data.get("hydration_glasses"),
    }
    db["vitals"].append(entry)

    # Check for alerts
    new_alerts = check_alerts(entry)
    for alert in new_alerts:
        alert["id"] = str(uuid.uuid4())
        alert["user_id"] = user_id
        alert["timestamp"] = datetime.now().isoformat()
        alert["resolved"] = False
        db["alerts"].append(alert)
        # Also create a notification
        db["notifications"].append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "alert",
            "message": alert["message"],
            "read": False,
            "created_at": datetime.now().isoformat(),
        })

    return success_response({"vitals_id": entry["id"], "alerts_generated": len(new_alerts)}, 201)


@app.route("/api/vitals/latest", methods=["GET"])
def get_latest_vitals():
    """Get the most recent vitals reading for the authenticated user."""
    user_id = get_user_id()
    user_vitals = [v for v in db["vitals"] if v["user_id"] == user_id]
    if not user_vitals:
        return error_response("No vitals data found", 404)
    latest = sorted(user_vitals, key=lambda x: x["timestamp"], reverse=True)[0]
    return success_response(latest)


@app.route("/api/vitals/history", methods=["GET"])
def get_vitals_history():
    """Get vitals history with optional date range and pagination."""
    user_id = get_user_id()
    days = int(request.args.get("days", 30))
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))

    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    user_vitals = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= cutoff]
    user_vitals.sort(key=lambda x: x["timestamp"], reverse=True)

    total = len(user_vitals)
    start = (page - 1) * per_page
    paginated = user_vitals[start:start + per_page]

    return success_response({
        "vitals": paginated,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page),
    })


@app.route("/api/vitals/summary", methods=["GET"])
def get_vitals_summary():
    """Compute daily/weekly summary statistics."""
    user_id = get_user_id()
    days = int(request.args.get("days", 7))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    user_vitals = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= cutoff]

    if not user_vitals:
        return success_response({"message": "No data in range"})

    def avg(key):
        vals = [v[key] for v in user_vitals if v.get(key) is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    def max_val(key):
        vals = [v[key] for v in user_vitals if v.get(key) is not None]
        return max(vals) if vals else None

    def min_val(key):
        vals = [v[key] for v in user_vitals if v.get(key) is not None]
        return min(vals) if vals else None

    summary = {
        "period_days": days,
        "readings_count": len(user_vitals),
        "heart_rate": {"avg": avg("heart_rate"), "min": min_val("heart_rate"), "max": max_val("heart_rate")},
        "spo2": {"avg": avg("spo2"), "min": min_val("spo2"), "max": max_val("spo2")},
        "temperature": {"avg": avg("temperature"), "min": min_val("temperature"), "max": max_val("temperature")},
        "blood_pressure": {"avg_systolic": avg("systolic_bp"), "avg_diastolic": avg("diastolic_bp")},
        "steps": {"avg": avg("steps"), "total": sum(v.get("steps", 0) for v in user_vitals)},
        "sleep": {"avg_hours": avg("sleep_hours")},
        "hrv": {"avg": avg("hrv")},
        "stress": {"avg": avg("stress_level")},
        "hydration": {"avg_glasses": avg("hydration_glasses")},
    }
    return success_response(summary)


# ─── ROUTES: GOALS ───────────────────────────────────────────────────────────
@app.route("/api/goals", methods=["GET"])
def get_goals():
    user_id = get_user_id()
    goals = [g for g in db["goals"] if g["user_id"] == user_id]
    return success_response(goals)


@app.route("/api/goals", methods=["POST"])
def create_goal():
    user_id = get_user_id()
    data = request.get_json()
    goal = {
        "id": "goal_" + str(uuid.uuid4())[:6],
        "user_id": user_id,
        "label": data.get("label"),
        "target": data.get("target"),
        "unit": data.get("unit"),
        "current": data.get("current", 0),
        "icon": data.get("icon", "⭐"),
        "color": data.get("color", "#4ade80"),
        "created_at": datetime.now().isoformat(),
    }
    db["goals"].append(goal)
    return success_response(goal, 201, "Goal created")


@app.route("/api/goals/<goal_id>", methods=["PUT"])
def update_goal(goal_id):
    data = request.get_json()
    for g in db["goals"]:
        if g["id"] == goal_id:
            g.update({k: v for k, v in data.items() if k in ["label", "target", "current", "unit", "icon", "color"]})
            return success_response(g, 200, "Goal updated")
    return error_response("Goal not found", 404)


@app.route("/api/goals/<goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    db["goals"] = [g for g in db["goals"] if g["id"] != goal_id]
    return success_response({"deleted": goal_id}, 200, "Goal deleted")


# ─── ROUTES: DEVICES ─────────────────────────────────────────────────────────
@app.route("/api/devices", methods=["GET"])
def get_devices():
    user_id = get_user_id()
    devices = [d for d in db["devices"] if d["user_id"] == user_id]
    return success_response(devices)


@app.route("/api/devices", methods=["POST"])
def register_device():
    user_id = get_user_id()
    data = request.get_json()
    device = {
        "id": "dev_" + str(uuid.uuid4())[:6],
        "user_id": user_id,
        "name": data.get("name"),
        "type": data.get("type"),
        "mac": data.get("mac"),
        "status": "connected",
        "battery": 100,
        "firmware": data.get("firmware", "1.0.0"),
        "last_sync": datetime.now().isoformat(),
        "registered_at": datetime.now().isoformat(),
    }
    db["devices"].append(device)
    return success_response(device, 201, "Device registered")


@app.route("/api/devices/<device_id>/status", methods=["PUT"])
def update_device_status(device_id):
    data = request.get_json()
    for d in db["devices"]:
        if d["id"] == device_id:
            d["status"] = data.get("status", d["status"])
            d["battery"] = data.get("battery", d["battery"])
            d["last_sync"] = datetime.now().isoformat()
            return success_response(d)
    return error_response("Device not found", 404)


@app.route("/api/devices/<device_id>", methods=["DELETE"])
def remove_device(device_id):
    db["devices"] = [d for d in db["devices"] if d["id"] != device_id]
    return success_response({"removed": device_id})


# ─── ROUTES: NOTIFICATIONS ───────────────────────────────────────────────────
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    user_id = get_user_id()
    notifs = [n for n in db["notifications"] if n["user_id"] == user_id]
    notifs.sort(key=lambda x: x["created_at"], reverse=True)
    return success_response(notifs)


@app.route("/api/notifications/<notif_id>/read", methods=["PUT"])
def mark_notification_read(notif_id):
    for n in db["notifications"]:
        if n["id"] == notif_id:
            n["read"] = True
            return success_response(n)
    return error_response("Notification not found", 404)


@app.route("/api/notifications/read-all", methods=["PUT"])
def mark_all_read():
    user_id = get_user_id()
    for n in db["notifications"]:
        if n["user_id"] == user_id:
            n["read"] = True
    return success_response({"message": "All notifications marked as read"})


# ─── ROUTES: ALERTS ──────────────────────────────────────────────────────────
@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    user_id = get_user_id()
    resolved = request.args.get("resolved", "false").lower() == "true"
    alerts = [a for a in db["alerts"] if a["user_id"] == user_id and a.get("resolved") == resolved]
    alerts.sort(key=lambda x: x["timestamp"], reverse=True)
    return success_response(alerts)


@app.route("/api/alerts/<alert_id>/resolve", methods=["PUT"])
def resolve_alert(alert_id):
    for a in db["alerts"]:
        if a["id"] == alert_id:
            a["resolved"] = True
            a["resolved_at"] = datetime.now().isoformat()
            return success_response(a)
    return error_response("Alert not found", 404)


# ─── ROUTES: AI / ML ANALYSIS ─────────────────────────────────────────────────
@app.route("/api/ai/health-score", methods=["GET"])
def get_health_score():
    """
    Compute an AI-driven health score (0–100) based on recent vitals.
    Uses a weighted scoring model across multiple health dimensions.
    """
    user_id = get_user_id()
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    recent = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= cutoff]

    if not recent:
        return success_response({"score": 0, "message": "Insufficient data"})

    # Scoring functions (returns 0–100)
    def score_hr(vals):
        avg_hr = sum(v for v in vals) / len(vals)
        return max(0, 100 - abs(avg_hr - 72) * 2)

    def score_spo2(vals):
        avg = sum(v for v in vals) / len(vals)
        return min(100, max(0, (avg - 90) * 10))

    def score_sleep(vals):
        avg = sum(v for v in vals) / len(vals)
        return min(100, max(0, avg * 12.5))

    def score_hrv(vals):
        avg = sum(v for v in vals) / len(vals)
        return min(100, avg * 1.5)

    hr_vals = [v["heart_rate"] for v in recent if v.get("heart_rate")]
    spo2_vals = [v["spo2"] for v in recent if v.get("spo2")]
    sleep_vals = [v["sleep_hours"] for v in recent if v.get("sleep_hours")]
    hrv_vals = [v["hrv"] for v in recent if v.get("hrv")]

    cardiovascular = round(score_hr(hr_vals), 1) if hr_vals else 50
    oxygen = round(score_spo2(spo2_vals), 1) if spo2_vals else 50
    sleep_score = round(score_sleep(sleep_vals), 1) if sleep_vals else 50
    recovery = round(score_hrv(hrv_vals), 1) if hrv_vals else 50

    # Weighted overall score
    overall = round(
        cardiovascular * 0.30 +
        oxygen * 0.25 +
        sleep_score * 0.25 +
        recovery * 0.20,
        1
    )

    return success_response({
        "overall_score": overall,
        "breakdown": {
            "cardiovascular": cardiovascular,
            "oxygen_levels": oxygen,
            "sleep_health": sleep_score,
            "recovery_hrv": recovery,
        },
        "risk_level": "Low" if overall >= 70 else ("Moderate" if overall >= 50 else "High"),
        "computed_at": datetime.now().isoformat(),
    })


@app.route("/api/ai/insights", methods=["GET"])
def get_ai_insights():
    """Generate AI-powered health insights based on latest vitals."""
    user_id = get_user_id()
    user_vitals = [v for v in db["vitals"] if v["user_id"] == user_id]
    if not user_vitals:
        return success_response({"insights": []})

    latest = sorted(user_vitals, key=lambda x: x["timestamp"], reverse=True)[0]
    insights = []

    # Heart rate insight
    hr = latest.get("heart_rate", 72)
    if hr > 90:
        insights.append({"type": "warning", "icon": "⚡", "title": "Elevated Heart Rate", "message": f"HR is {hr} bpm — above normal. Try relaxation exercises."})
    elif hr < 55:
        insights.append({"type": "warning", "icon": "💤", "title": "Low Heart Rate", "message": f"HR is {hr} bpm — ensure hydration and nutrition."})
    else:
        insights.append({"type": "good", "icon": "💚", "title": "Heart Rate Normal", "message": f"HR at {hr} bpm is within healthy range."})

    # SpO2
    spo2 = latest.get("spo2", 98)
    if spo2 < 95:
        insights.append({"type": "alert", "icon": "🚨", "title": "Low SpO2", "message": f"Blood oxygen at {spo2}% — consult a professional if persistent."})
    else:
        insights.append({"type": "good", "icon": "🫁", "title": "Oxygen Healthy", "message": f"SpO2 at {spo2}% — optimal range."})

    # Sleep
    sleep = latest.get("sleep_hours", 7)
    if sleep < 6:
        insights.append({"type": "warning", "icon": "🌙", "title": "Sleep Deficit", "message": f"Only {sleep}h sleep. Aim for 7–9 hours."})
    elif sleep >= 7.5:
        insights.append({"type": "good", "icon": "✨", "title": "Excellent Sleep", "message": f"{sleep}h of quality sleep supports recovery."})

    # Steps
    steps = latest.get("steps", 5000)
    if steps < 5000:
        insights.append({"type": "warning", "icon": "🚶", "title": "Low Activity", "message": f"Only {steps} steps today. A 20-min walk helps."})
    elif steps >= 10000:
        insights.append({"type": "good", "icon": "🏆", "title": "Activity Goal!", "message": f"{steps} steps — amazing work!"})

    return success_response({"insights": insights[:4]})


@app.route("/api/ai/predict-risk", methods=["POST"])
def predict_health_risk():
    """
    Rule-based health risk prediction.
    In production, replace with a trained ML model (sklearn, TensorFlow).
    """
    data = request.get_json()

    risk_score = 0
    factors = []

    hr = data.get("heart_rate", 72)
    if hr > 100: risk_score += 25; factors.append("Tachycardia")
    elif hr < 50: risk_score += 20; factors.append("Bradycardia")

    spo2 = data.get("spo2", 98)
    if spo2 < 92: risk_score += 30; factors.append("Hypoxemia")
    elif spo2 < 95: risk_score += 15; factors.append("Borderline SpO2")

    temp = data.get("temperature", 36.6)
    if temp > 38.0: risk_score += 20; factors.append("Fever")
    elif temp < 35.5: risk_score += 15; factors.append("Hypothermia risk")

    sys_bp = data.get("systolic_bp", 120)
    if sys_bp > 140: risk_score += 20; factors.append("Hypertension Stage 2")
    elif sys_bp > 130: risk_score += 10; factors.append("Hypertension Stage 1")

    sleep = data.get("sleep_hours", 7)
    if sleep < 5: risk_score += 10; factors.append("Severe sleep deprivation")

    stress = data.get("stress_level", 40)
    if stress > 70: risk_score += 15; factors.append("High stress")

    risk_level = "Low" if risk_score < 20 else ("Moderate" if risk_score < 50 else ("High" if risk_score < 75 else "Critical"))

    return success_response({
        "risk_score": min(risk_score, 100),
        "risk_level": risk_level,
        "risk_factors": factors,
        "recommendation": (
            "Maintain current healthy habits." if risk_level == "Low" else
            "Monitor closely and consult your doctor." if risk_level == "Moderate" else
            "Seek medical attention soon." if risk_level == "High" else
            "Contact emergency services immediately."
        ),
    })


@app.route("/api/ai/trend-analysis", methods=["GET"])
def get_trend_analysis():
    """Compare last 7 days vs previous 7 days for trend detection."""
    user_id = get_user_id()
    now = datetime.now()
    week1_start = (now - timedelta(days=7)).isoformat()
    week2_start = (now - timedelta(days=14)).isoformat()

    week1 = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= week1_start]
    week2 = [v for v in db["vitals"] if v["user_id"] == user_id and week2_start <= v["timestamp"] < week1_start]

    def compute_avg(data, key):
        vals = [v[key] for v in data if v.get(key)]
        return sum(vals) / len(vals) if vals else 0

    metrics = ["heart_rate", "spo2", "steps", "sleep_hours", "hrv", "stress_level"]
    trends = []

    for metric in metrics:
        avg1 = compute_avg(week1, metric)
        avg2 = compute_avg(week2, metric)
        change_pct = round(((avg1 - avg2) / avg2 * 100), 1) if avg2 != 0 else 0

        # Determine if improvement or decline (context dependent)
        positive_metrics = ["spo2", "steps", "sleep_hours", "hrv"]
        negative_metrics = ["stress_level"]
        if metric in positive_metrics:
            is_good = change_pct >= 0
        elif metric in negative_metrics:
            is_good = change_pct <= 0
        else:
            is_good = abs(change_pct) < 5  # Heart rate: stable is good

        trends.append({
            "metric": metric.replace("_", " ").title(),
            "current_avg": round(avg1, 1),
            "previous_avg": round(avg2, 1),
            "change_percent": change_pct,
            "trend": "Improving" if is_good and change_pct != 0 else ("Stable" if change_pct == 0 else "Declining"),
            "is_positive": is_good,
        })

    return success_response({"trends": trends, "period": "7 days"})


# ─── ROUTES: DATA EXPORT ─────────────────────────────────────────────────────
@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Export vitals data as CSV."""
    import io, csv
    user_id = get_user_id()
    days = int(request.args.get("days", 30))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    data = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= cutoff]

    output = io.StringIO()
    if data:
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

    from flask import Response
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=health_data.csv"})


@app.route("/api/export/json", methods=["GET"])
def export_json():
    user_id = get_user_id()
    days = int(request.args.get("days", 30))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    data = [v for v in db["vitals"] if v["user_id"] == user_id and v["timestamp"] >= cutoff]
    return success_response({"export": data, "count": len(data), "period_days": days})


# ─── ROUTES: USER PROFILE ────────────────────────────────────────────────────
@app.route("/api/user/profile", methods=["GET"])
def get_profile():
    user_id = get_user_id()
    user = db["users"].get(user_id)
    if not user:
        return error_response("User not found", 404)
    # Compute BMI
    h = user["height_cm"] / 100
    bmi = round(user["weight_kg"] / (h * h), 1)
    user["bmi"] = bmi
    user["bmi_category"] = "Underweight" if bmi < 18.5 else ("Normal" if bmi < 25 else ("Overweight" if bmi < 30 else "Obese"))
    return success_response(user)


@app.route("/api/user/profile", methods=["PUT"])
def update_profile():
    user_id = get_user_id()
    data = request.get_json()
    user = db["users"].get(user_id)
    if not user:
        return error_response("User not found", 404)
    for key in ["name", "age", "gender", "weight_kg", "height_cm"]:
        if key in data:
            user[key] = data[key]
    return success_response(user, 200, "Profile updated")


# ─── MAIN ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  HealthSync Backend Server")
    print("  Healthcare IoT Ecosystem API")
    print("=" * 60)
    print(f"  Starting on http://0.0.0.0:5000")
    print(f"  Seeded {len(db['vitals'])} vitals, {len(db['devices'])} devices, {len(db['goals'])} goals")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
