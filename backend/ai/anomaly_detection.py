import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from backend.config import Config

class AnomalyDetector:
    def __init__(self, model_path=None):
        self.model_path = model_path or (Config.MODELS_FOLDER / "isolation_forest.joblib")
        self.model = None
        self._load_or_init_model()

    def _load_or_init_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                self.model = IsolationForest(
                    contamination=0.08,
                    random_state=42,
                    n_estimators=100
                )
        except Exception:
            self.model = IsolationForest(
                contamination=0.08,
                random_state=42,
                n_estimators=100
            )

    def train(self, df):
        """
        Trains Isolation Forest on historical feature matrix:
        features: [kwh, occupancy, temperature, humidity, hour, day_of_week]
        """
        features = ["kwh", "occupancy", "temperature", "humidity", "hour", "day_of_week"]
        X = df[features].fillna(0)
        self.model.fit(X)
        os.makedirs(Config.MODELS_FOLDER, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        return self

    def calculate_expected_baseline(self, building_type, hour, day_of_week, occupancy, temperature, resource="electricity"):
        """
        Computes the expected consumption baseline using contextual domain heuristics
        calibrated to university building profiles.
        """
        is_weekend = day_of_week in [5, 6]
        
        if resource == "electricity":
            # Base load according to building category
            base_kw = {
                "Academic": 65.0,
                "Administrative": 45.0,
                "Laboratory": 110.0,
                "Residential": 50.0,
                "Facility": 35.0
            }.get(building_type, 50.0)
            
            # Hourly time curve
            if 8 <= hour <= 18:
                time_mult = 1.0 if not is_weekend else 0.4
            elif 18 < hour <= 22:
                time_mult = 0.6 if not is_weekend else 0.35
            else:
                time_mult = 0.25 # Night baseline
                
            # Occupancy factor (0.12 kWh per occupant)
            occupancy_kwh = max(0, occupancy) * 0.12
            
            # Temperature / HVAC cooling factor (baseline 24C)
            temp_delta = max(0, temperature - 24.0)
            cooling_kwh = temp_delta * (base_kw * 0.08)
            
            expected = (base_kw * time_mult) + occupancy_kwh + cooling_kwh
            return max(15.0, round(float(expected), 2))
            
        else: # water
            base_lpm = {
                "Academic": 250.0,
                "Administrative": 150.0,
                "Laboratory": 400.0,
                "Residential": 850.0, # High usage in hostels morning/evening
                "Facility": 550.0      # Kitchen/cafeteria
            }.get(building_type, 300.0)
            
            if "Residential" in building_type:
                if 6 <= hour <= 9 or 18 <= hour <= 21:
                    time_mult = 1.6
                elif 10 <= hour <= 17:
                    time_mult = 0.5
                else:
                    time_mult = 0.15
            else:
                if 9 <= hour <= 17:
                    time_mult = 1.2 if not is_weekend else 0.2
                else:
                    time_mult = 0.1
                    
            occupancy_liters = max(0, occupancy) * 0.8
            expected = (base_lpm * time_mult) + occupancy_liters
            return max(50.0, round(float(expected), 2))

    def detect_single(self, building_type, actual_value, occupancy, temperature, humidity, hour, day_of_week, resource="electricity"):
        """
        Evaluates a single reading against baseline and IsolationForest score.
        """
        expected = self.calculate_expected_baseline(
            building_type, hour, day_of_week, occupancy, temperature, resource
        )
        
        diff = actual_value - expected
        pct_dev = ((actual_value - expected) / expected) * 100.0 if expected > 0 else 0.0
        
        # Scikit-learn isolation forest decision function
        features_df = pd.DataFrame([{
            "kwh": actual_value,
            "occupancy": occupancy,
            "temperature": temperature,
            "humidity": humidity,
            "hour": hour,
            "day_of_week": day_of_week
        }])
        try:
            # score_samples returns negative anomaly score (lower is more anomalous)
            raw_score = self.model.score_samples(features_df)[0]
            # normalize into 0..1 where 1 is highest anomaly probability
            iso_prob = float(np.clip(1.0 - (raw_score + 0.5), 0.0, 1.0))
        except Exception:
            iso_prob = 0.5

        # Blended anomaly metric combining ISO forest and statistical percentage deviation
        is_anomaly = False
        severity = "LOW"
        anomaly_score = round(max(iso_prob, min(1.0, abs(pct_dev) / 50.0)), 2)

        if pct_dev >= 45.0 or (pct_dev >= 35.0 and iso_prob > 0.65):
            is_anomaly = True
            severity = "CRITICAL"
        elif pct_dev >= 25.0 or (pct_dev >= 20.0 and iso_prob > 0.60):
            is_anomaly = True
            severity = "HIGH"
        elif pct_dev >= 15.0 or (pct_dev >= 12.0 and iso_prob > 0.55):
            is_anomaly = True
            severity = "MEDIUM"
        elif pct_dev >= 8.0:
            is_anomaly = False
            severity = "LOW"

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "severity": severity,
            "expected_value": expected,
            "actual_value": round(float(actual_value), 2),
            "deviation": round(pct_dev, 1),
            "excess_value": round(max(0.0, diff), 2)
        }
