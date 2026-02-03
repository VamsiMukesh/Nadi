"""
HealthSync — ML Model Module
============================
Handles:
  - Synthetic health dataset generation
  - Feature engineering (BMI, BP ratio, recovery index, etc.)
  - Model training: Health Risk Classifier + Health Score Regressor
  - Prediction pipeline: accepts raw vitals → returns risk + score + recommendations
  - Model persistence (joblib)

Models:
  1. Risk Classifier  → predicts risk category: Low / Moderate / High / Critical
  2. Score Regressor  → predicts overall health score 0–100

Requirements:
    pip install scikit-learn pandas numpy joblib

Usage:
    python ml_model.py            # Train and save models
    from ml_model import predict  # Import prediction function
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, mean_squared_error
import joblib
import os
import warnings

warnings.filterwarnings("ignore")

# ─── CONFIG ───────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
RISK_MODEL_PATH = os.path.join(MODEL_DIR, "risk_classifier.pkl")
SCORE_MODEL_PATH = os.path.join(MODEL_DIR, "score_regressor.pkl")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

N_SAMPLES = 5000  # Synthetic dataset size
RANDOM_STATE = 42

np.random.seed(RANDOM_STATE)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SYNTHETIC DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════════
def generate_synthetic_data(n=N_SAMPLES) -> pd.DataFrame:
    """
    Generate a realistic synthetic health dataset simulating IoT sensor readings.
    Includes physiological correlations (e.g., high stress → elevated HR).
    """
    # Base distributions (age-stratified)
    ages = np.random.randint(18, 80, n)

    # Heart rate (influenced by age and stress)
    base_hr = 72 - ages * 0.05 + np.random.normal(0, 8, n)
    stress = np.clip(np.random.normal(45, 18, n), 0, 100)
    heart_rate = np.clip(base_hr + stress * 0.3 + np.random.normal(0, 5, n), 35, 160).astype(int)

    # SpO2 (mostly high, occasionally dips)
    spo2 = np.clip(np.random.normal(97.5, 1.8, n), 85, 100).round(1)

    # Temperature
    temperature = np.clip(np.random.normal(36.6, 0.4, n), 35.0, 39.5).round(1)

    # Blood pressure (age-correlated)
    systolic = np.clip(110 + ages * 0.3 + np.random.normal(0, 12, n), 70, 200).astype(int)
    diastolic = np.clip(systolic * 0.65 + np.random.normal(0, 6, n), 40, 130).astype(int)

    # Steps (influenced by age)
    steps = np.clip(np.random.normal(7000 - ages * 30, 2500, n), 0, 25000).astype(int)

    # Sleep hours
    sleep_hours = np.clip(np.random.normal(7.0, 1.2, n), 3, 12).round(1)

    # HRV (inversely related to stress)
    hrv = np.clip(65 - stress * 0.3 + np.random.normal(0, 8, n), 15, 100).astype(int)

    # Calories
    calories = np.clip(steps * 0.18 + np.random.normal(500, 200, n), 800, 4000).astype(int)

    # Hydration
    hydration = np.clip(np.random.normal(6, 2, n), 0, 15).round(1)

    # Weight & height
    height_cm = np.clip(np.random.normal(170, 10, n), 140, 210).astype(int)
    weight_kg = np.clip(np.random.normal(70, 15, n), 40, 150).round(1)

    # Gender
    gender = np.random.choice(["male", "female"], n)

    df = pd.DataFrame({
        "age": ages,
        "gender": gender,
        "weight_kg": weight_kg,
        "height_cm": height_cm,
        "heart_rate": heart_rate,
        "spo2": spo2,
        "temperature": temperature,
        "systolic_bp": systolic,
        "diastolic_bp": diastolic,
        "steps": steps,
        "sleep_hours": sleep_hours,
        "hrv": hrv,
        "stress_level": stress.round(1),
        "calories": calories,
        "hydration_glasses": hydration,
    })
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features for better model performance.
    """
    df = df.copy()

    # BMI
    df["bmi"] = (df["weight_kg"] / ((df["height_cm"] / 100) ** 2)).round(1)

    # Pulse Pressure (systolic - diastolic)
    df["pulse_pressure"] = df["systolic_bp"] - df["diastolic_bp"]

    # Mean Arterial Pressure
    df["map"] = ((df["systolic_bp"] + 2 * df["diastolic_bp"]) / 3).round(1)

    # Resting Heart Rate category score
    df["hr_deviation"] = abs(df["heart_rate"] - 72)

    # Sleep efficiency indicator
    df["sleep_score"] = np.clip(df["sleep_hours"] / 8 * 100, 0, 100).round(1)

    # Activity intensity
    df["activity_intensity"] = (df["steps"] / 10000 * 100).clip(0, 100).round(1)

    # Recovery index (HRV / stress ratio)
    df["recovery_index"] = (df["hrv"] / (df["stress_level"] + 1) * 10).round(2)

    # Hydration adequacy
    df["hydration_score"] = np.clip(df["hydration_glasses"] / 8 * 100, 0, 100)

    # Encode gender
    df["gender_encoded"] = (df["gender"] == "male").astype(int)

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# 3. LABEL GENERATION (Simulated Ground Truth)
# ═══════════════════════════════════════════════════════════════════════════════
def generate_labels(df: pd.DataFrame):
    """
    Create target labels based on physiological rules.
    These simulate what a physician would flag.
    """
    risk_scores = np.zeros(len(df))

    # Heart rate risk
    risk_scores += np.where(df["heart_rate"] > 100, 25, 0)
    risk_scores += np.where(df["heart_rate"] < 50, 20, 0)
    risk_scores += np.where((df["heart_rate"] >= 50) & (df["heart_rate"] <= 100), 2, 0)

    # SpO2
    risk_scores += np.where(df["spo2"] < 92, 30, 0)
    risk_scores += np.where((df["spo2"] >= 92) & (df["spo2"] < 95), 15, 0)

    # Blood pressure
    risk_scores += np.where(df["systolic_bp"] > 140, 20, 0)
    risk_scores += np.where(df["systolic_bp"] > 130, 10, 0)

    # Temperature
    risk_scores += np.where(df["temperature"] > 38.0, 18, 0)

    # Sleep
    risk_scores += np.where(df["sleep_hours"] < 5, 12, 0)

    # Stress
    risk_scores += np.where(df["stress_level"] > 70, 15, 0)

    # BMI
    risk_scores += np.where(df["bmi"] > 30, 12, 0)
    risk_scores += np.where(df["bmi"] < 18.5, 8, 0)

    # Add noise to simulate real-world variability
    risk_scores += np.random.normal(0, 3, len(df))
    risk_scores = np.clip(risk_scores, 0, 100)

    # Risk categories
    risk_labels = np.where(risk_scores < 20, "Low",
                  np.where(risk_scores < 45, "Moderate",
                  np.where(risk_scores < 70, "High", "Critical")))

    # Health score (inverse of risk, 0–100)
    health_scores = np.clip(100 - risk_scores * 1.2 + np.random.normal(0, 4, len(df)), 0, 100).round(1)

    return risk_labels, health_scores


# ═══════════════════════════════════════════════════════════════════════════════
# 4. MODEL TRAINING
# ═══════════════════════════════════════════════════════════════════════════════
FEATURE_COLUMNS = [
    "age", "gender_encoded", "weight_kg", "height_cm",
    "heart_rate", "spo2", "temperature",
    "systolic_bp", "diastolic_bp",
    "steps", "sleep_hours", "hrv", "stress_level",
    "calories", "hydration_glasses",
    "bmi", "pulse_pressure", "map", "hr_deviation",
    "sleep_score", "activity_intensity", "recovery_index", "hydration_score",
]


def train_models():
    """Full pipeline: generate data → engineer features → train → evaluate → save."""
    print("=" * 60)
    print("  HealthSync ML Training Pipeline")
    print("=" * 60)

    # 1. Generate data
    print("\n[1/5] Generating synthetic health dataset...")
    df = generate_synthetic_data(N_SAMPLES)
    print(f"      Dataset shape: {df.shape}")

    # 2. Feature engineering
    print("[2/5] Engineering features...")
    df = engineer_features(df)

    # 3. Generate labels
    print("[3/5] Generating target labels...")
    risk_labels, health_scores = generate_labels(df)
    df["risk_label"] = risk_labels
    df["health_score"] = health_scores

    print(f"      Risk distribution:\n{pd.Series(risk_labels).value_counts().to_string()}")

    # 4. Prepare features
    X = df[FEATURE_COLUMNS].values
    y_risk = df["risk_label"].values
    y_score = df["health_score"].values

    X_train, X_test, y_risk_train, y_risk_test = train_test_split(X, y_risk, test_size=0.2, random_state=RANDOM_STATE, stratify=y_risk)
    _, _, y_score_train, y_score_test = train_test_split(X, y_score, test_size=0.2, random_state=RANDOM_STATE)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Train Risk Classifier
    print("[4/5] Training Risk Classifier (RandomForest)...")
    risk_clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    risk_clf.fit(X_train_scaled, y_risk_train)

    y_risk_pred = risk_clf.predict(X_test_scaled)
    print("\n      Risk Classifier — Classification Report:")
    print(classification_report(y_risk_test, y_risk_pred, target_names=["Critical", "High", "Low", "Moderate"]))
    print(f"      Accuracy: {(y_risk_pred == y_risk_test).mean():.3f}")

    # 6. Train Score Regressor
    print("[5/5] Training Health Score Regressor (GradientBoosting)...")
    score_reg = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        random_state=RANDOM_STATE,
    )
    score_reg.fit(X_train_scaled, y_score_train)

    y_score_pred = score_reg.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_score_test, y_score_pred))
    print(f"      Score Regressor RMSE: {rmse:.2f}")
    print(f"      Score Regressor R²:   {score_reg.score(X_test_scaled, y_score_test):.3f}")

    # Save models
    print("\n      Saving models...")
    joblib.dump(risk_clf, RISK_MODEL_PATH)
    joblib.dump(score_reg, SCORE_MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    # Feature importance
    print("\n      Top 10 Features (Risk Classifier):")
    importances = risk_clf.feature_importances_
    indices = np.argsort(importances)[::-1][:10]
    for i in indices:
        print(f"        {FEATURE_COLUMNS[i]:25s} → {importances[i]:.4f}")

    print("\n" + "=" * 60)
    print("  Training complete! Models saved.")
    print("=" * 60)
    return risk_clf, score_reg, scaler


# ═══════════════════════════════════════════════════════════════════════════════
# 5. PREDICTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════
def load_models():
    """Load saved models. If not found, train first."""
    if not all(os.path.exists(p) for p in [RISK_MODEL_PATH, SCORE_MODEL_PATH, SCALER_PATH]):
        print("Models not found. Training...")
        return train_models()
    return (
        joblib.load(RISK_MODEL_PATH),
        joblib.load(SCORE_MODEL_PATH),
        joblib.load(SCALER_PATH),
    )


def predict(vitals: dict) -> dict:
    """
    Main prediction function.
    Input: dict with keys matching raw vitals + user demographics.
    Output: dict with risk_label, health_score, breakdown, recommendations.

    Example input:
        {
            "age": 35, "gender": "male", "weight_kg": 75, "height_cm": 178,
            "heart_rate": 88, "spo2": 96.5, "temperature": 36.8,
            "systolic_bp": 135, "diastolic_bp": 85,
            "steps": 4500, "sleep_hours": 5.5, "hrv": 42,
            "stress_level": 68, "calories": 1900, "hydration_glasses": 4
        }
    """
    risk_clf, score_reg, scaler = load_models()

    # Convert to DataFrame for feature engineering
    df = pd.DataFrame([vitals])
    df = engineer_features(df)

    # Extract feature columns
    X = df[FEATURE_COLUMNS].values
    X_scaled = scaler.transform(X)

    # Predictions
    risk_label = risk_clf.predict(X_scaled)[0]
    risk_proba = risk_clf.predict_proba(X_scaled)[0]
    health_score = round(float(score_reg.predict(X_scaled)[0]), 1)

    # Risk class probabilities
    risk_classes = risk_clf.classes_
    risk_distribution = {cls: round(float(prob), 3) for cls, prob in zip(risk_classes, risk_proba)}

    # Generate recommendations based on vitals
    recommendations = generate_recommendations(vitals, risk_label, health_score)

    return {
        "risk_label": risk_label,
        "risk_distribution": risk_distribution,
        "health_score": min(max(health_score, 0), 100),
        "recommendations": recommendations,
        "input_vitals": vitals,
    }


def generate_recommendations(vitals: dict, risk_label: str, health_score: float) -> list:
    """Generate actionable health recommendations based on prediction results."""
    recs = []

    hr = vitals.get("heart_rate", 72)
    if hr > 90:
        recs.append("Your heart rate is elevated. Try deep breathing exercises or progressive muscle relaxation.")
    elif hr < 55:
        recs.append("Your resting heart rate is low. Ensure adequate hydration and nutrition throughout the day.")

    spo2 = vitals.get("spo2", 98)
    if spo2 < 95:
        recs.append("Your blood oxygen is below optimal. Practice diaphragmatic breathing and consider consulting a doctor.")

    sleep = vitals.get("sleep_hours", 7)
    if sleep < 6:
        recs.append("Sleep deprivation detected. Aim for 7–9 hours. Establish a consistent bedtime routine.")
    elif sleep >= 8:
        recs.append("Excellent sleep! Maintain your current sleep schedule for optimal health.")

    steps = vitals.get("steps", 5000)
    if steps < 5000:
        recs.append("Increase physical activity. A 20-minute brisk walk twice daily can improve cardiovascular health.")
    elif steps >= 10000:
        recs.append("Outstanding activity level! Keep maintaining this habit for long-term health benefits.")

    stress = vitals.get("stress_level", 40)
    if stress > 65:
        recs.append("High stress detected. Consider mindfulness meditation, yoga, or journaling to manage stress.")

    hydration = vitals.get("hydration_glasses", 6)
    if hydration < 6:
        recs.append("Increase water intake. Aim for 8 glasses per day. Set hourly reminders to stay hydrated.")

    bmi = vitals.get("weight_kg", 70) / ((vitals.get("height_cm", 170) / 100) ** 2)
    if bmi > 30:
        recs.append("Consider consulting a nutritionist for a personalized diet plan to achieve a healthy BMI.")
    elif bmi < 18.5:
        recs.append("You may be underweight. Focus on nutrient-dense foods and consult a healthcare professional.")

    if risk_label in ["High", "Critical"]:
        recs.append("⚠️ Your health risk is elevated. Please consult a healthcare professional at your earliest convenience.")

    if not recs:
        recs.append("You're doing great! Continue your healthy lifestyle habits for sustained well-being.")

    return recs[:5]  # Return top 5 recommendations


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN — Train models when run directly
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Train and save models
    train_models()

    # Demo prediction
    print("\n── Demo Prediction ──")
    sample_vitals = {
        "age": 42,
        "gender": "female",
        "weight_kg": 68,
        "height_cm": 165,
        "heart_rate": 95,
        "spo2": 94.5,
        "temperature": 37.2,
        "systolic_bp": 138,
        "diastolic_bp": 88,
        "steps": 3200,
        "sleep_hours": 5.0,
        "hrv": 38,
        "stress_level": 72,
        "calories": 1600,
        "hydration_glasses": 3,
    }
    result = predict(sample_vitals)
    print(f"\n  Input Vitals:      {sample_vitals}")
    print(f"  Predicted Risk:    {result['risk_label']}")
    print(f"  Risk Distribution: {result['risk_distribution']}")
    print(f"  Health Score:      {result['health_score']}")
    print(f"  Recommendations:")
    for i, rec in enumerate(result["recommendations"], 1):
        print(f"    {i}. {rec}")
