import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from backend.config import Config

def train_and_save_models():
    """
    Generates representative training datasets and fits production models:
    1. Isolation Forest for Electricity & Water Anomaly Detection
    2. Random Forest Regressor for Electricity Prediction
    3. Random Forest Regressor for Water Prediction
    """
    os.makedirs(Config.MODELS_FOLDER, exist_ok=True)
    np.random.seed(42)
    
    # 1. Train Anomaly Detection (Isolation Forest)
    print("Training Isolation Forest Anomaly Detection model...")
    n_samples = 3500
    hours = np.random.randint(0, 24, n_samples)
    dows = np.random.randint(0, 7, n_samples)
    temps = np.random.normal(29.0, 4.0, n_samples)
    humidities = np.random.normal(65.0, 10.0, n_samples)
    occupancies = np.random.randint(20, 500, n_samples)
    
    # Normal energy equation + random anomalies
    kwh = 40.0 + (occupancies * 0.12) + np.maximum(0, temps - 25.0) * 3.5 + np.random.normal(0, 5.0, n_samples)
    # Inject intentional anomalies in 8% of training data
    anomaly_indices = np.random.choice(n_samples, int(n_samples * 0.08), replace=False)
    kwh[anomaly_indices] *= np.random.uniform(1.35, 1.8, len(anomaly_indices))
    
    X_iso = pd.DataFrame({
        "kwh": kwh,
        "occupancy": occupancies,
        "temperature": temps,
        "humidity": humidities,
        "hour": hours,
        "day_of_week": dows
    })
    
    iso_model = IsolationForest(contamination=0.08, random_state=42, n_estimators=100)
    iso_model.fit(X_iso)
    joblib.dump(iso_model, Config.MODELS_FOLDER / "isolation_forest.joblib")
    print("-> Saved isolation_forest.joblib")

    # 2. Train Electricity Predictor (Random Forest)
    print("Training Electricity Random Forest Regressor...")
    lag_1 = kwh * 0.98 + np.random.normal(0, 2, n_samples)
    lag_24 = kwh * 0.95 + np.random.normal(0, 3, n_samples)
    
    X_rf_elec = pd.DataFrame({
        "hour": hours,
        "day_of_week": dows,
        "month": np.random.randint(1, 13, n_samples),
        "occupancy": occupancies,
        "temperature": temps,
        "humidity": humidities,
        "lag_1": lag_1,
        "lag_24": lag_24
    })
    y_rf_elec = kwh
    
    rf_elec = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    rf_elec.fit(X_rf_elec, y_rf_elec)
    joblib.dump(rf_elec, Config.MODELS_FOLDER / "rf_electricity_predictor.joblib")
    print("-> Saved rf_electricity_predictor.joblib")

    # 3. Train Water Predictor (Random Forest)
    print("Training Water Random Forest Regressor...")
    liters = 200.0 + (occupancies * 0.8) + np.random.normal(0, 30.0, n_samples)
    rf_water = RandomForestRegressor(n_estimators=80, max_depth=10, random_state=42)
    rf_water.fit(X_rf_elec, liters)
    joblib.dump(rf_water, Config.MODELS_FOLDER / "rf_water_predictor.joblib")
    print("-> Saved rf_water_predictor.joblib")

    print("All ML models successfully trained and cached in", Config.MODELS_FOLDER)

if __name__ == "__main__":
    train_and_save_models()
