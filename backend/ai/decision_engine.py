from backend.ai.anomaly_detection import AnomalyDetector
from backend.ai.consumption_prediction import ConsumptionPredictor
from backend.ai.explainability import AIExplainer
from backend.ai.recommendation_engine import RecommendationEngine
from backend.ai.simulator import WhatIfSimulator
from backend.ai.sustainability import SustainabilityCalculator

class DecisionEngine:
    """
    Central AI Decision Engine coordinating the entire autonomous workflow:
    MONITOR → DETECT → PREDICT → EXPLAIN → RECOMMEND → SIMULATE → OPTIMIZE → MEASURE IMPACT
    """
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.elec_predictor = ConsumptionPredictor(resource="electricity")
        self.water_predictor = ConsumptionPredictor(resource="water")

    def analyze_building(self, building_info, telemetry):
        """
        Processes real-time building telemetry through the entire AI decision pipeline.
        
        telemetry: {
            "electricity_kwh": float,
            "water_liters": float,
            "occupancy": int,
            "temperature": float,
            "humidity": float,
            "hour": int,
            "day_of_week": int
        }
        """
        b_id = building_info.get("id")
        b_name = building_info.get("name")
        b_type = building_info.get("building_type", "Academic")
        
        elec_kwh = telemetry.get("electricity_kwh", 150.0)
        water_liters = telemetry.get("water_liters", 800.0)
        occ = telemetry.get("occupancy", 250)
        temp = telemetry.get("temperature", 31.0)
        hum = telemetry.get("humidity", 65.0)
        hour = telemetry.get("hour", 14)
        dow = telemetry.get("day_of_week", 2)

        # 1. Anomaly Detection (Electricity & Water)
        elec_anom = self.anomaly_detector.detect_single(
            b_type, elec_kwh, occ, temp, hum, hour, dow, resource="electricity"
        )
        elec_anom["resource_type"] = "electricity"
        elec_anom["building_id"] = b_id

        water_anom = self.anomaly_detector.detect_single(
            b_type, water_liters, occ, temp, hum, hour, dow, resource="water"
        )
        water_anom["resource_type"] = "water"
        water_anom["building_id"] = b_id

        detected_anomalies = []
        if elec_anom["is_anomaly"]:
            detected_anomalies.append(elec_anom)
        if water_anom["is_anomaly"]:
            detected_anomalies.append(water_anom)

        # 2. Consumption Prediction (Next 24 Hours)
        elec_forecast = self.elec_predictor.predict_next_hours(
            b_id, b_type, {"temperature": temp, "humidity": hum, "occupancy": occ}, hours=24
        )
        water_forecast = self.water_predictor.predict_next_hours(
            b_id, b_type, {"temperature": temp, "humidity": hum, "occupancy": occ}, hours=24
        )

        # 3. Explainable AI Analysis
        context = {
            "temperature": temp,
            "humidity": hum,
            "occupancy": occ,
            "hour": hour,
            "day_of_week": dow,
            "building_type": b_type
        }
        
        explanations = {}
        if elec_anom["is_anomaly"]:
            explanations["electricity"] = AIExplainer.explain_anomaly(elec_anom, context)
        if water_anom["is_anomaly"]:
            explanations["water"] = AIExplainer.explain_anomaly(water_anom, context)

        # 4. Corrective Recommendations Generation
        recommendations = RecommendationEngine.generate_recommendations(
            b_id, b_name, b_type, detected_anomalies, elec_forecast
        )

        # 5. Pre-computed What-If Simulations for Top Recommendation
        top_rec = recommendations[0] if recommendations else None
        simulation_preview = None
        if top_rec:
            action_key = "reduce_ac_1h" if "AC" in top_rec["action"] else ("fix_water_leak" if "valve" in top_rec["action"] or "water" in top_rec["action"].lower() else "optimize_lighting")
            simulation_preview = WhatIfSimulator.simulate_action(
                {"current_energy": elec_kwh * 24.0, "current_water": water_liters * 24.0},
                action_key,
                duration_hours=1.0,
                temperature=temp
            )

        # 6. Overall Decision Package
        return {
            "building_id": b_id,
            "building_name": b_name,
            "telemetry": telemetry,
            "anomalies": detected_anomalies,
            "predictions": {
                "electricity": elec_forecast,
                "water": water_forecast
            },
            "explanations": explanations,
            "recommendations": recommendations,
            "simulation_preview": simulation_preview,
            "confidence": 91.5
        }
