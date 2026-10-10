import os
import unittest
import json
from datetime import datetime
from backend.app import create_app
from backend.database import SessionLocal
from backend.models import Building, User
from backend.ai.anomaly_detection import AnomalyDetector
from backend.ai.explainability import AIExplainer
from backend.ai.consumption_prediction import ConsumptionPredictor
from backend.ai.recommendation_engine import RecommendationEngine
from backend.ai.simulator import WhatIfSimulator
from backend.ai.sustainability import SustainabilityCalculator

class TestEcoCampusAI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_database_connection(self):
        """Verify database connectivity and seeded buildings count"""
        db = SessionLocal()
        try:
            b_count = db.query(Building).count()
            self.assertGreaterEqual(b_count, 8, "Expected at least 8 seeded buildings")
        finally:
            db.close()

    def test_02_authentication(self):
        """Verify admin login and JWT token issuance"""
        res = self.client.post("/api/auth/login", json={
            "email": "admin@ecocampus.ai",
            "password": "Admin@123"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "admin")

    def test_03_buildings_api(self):
        """Verify building listing and detailed endpoint"""
        res = self.client.get("/api/buildings")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(len(data["buildings"]), 8)

        # Test single building detail
        detail_res = self.client.get("/api/buildings/BLK-A")
        self.assertEqual(detail_res.status_code, 200)
        detail_data = detail_res.get_json()
        self.assertEqual(detail_data["building"]["id"], "BLK-A")
        self.assertIn("kpis", detail_data)

    def test_04_energy_and_water_apis(self):
        """Verify energy and water monitoring endpoints"""
        e_res = self.client.get("/api/energy?range=24h")
        self.assertEqual(e_res.status_code, 200)
        e_data = e_res.get_json()
        self.assertTrue(e_data["success"])
        self.assertIn("kpis", e_data)
        self.assertIn("loss_intelligence", e_data)
        self.assertIn("daily_financial_loss_inr", e_data["loss_intelligence"])
        self.assertIn("categories", e_data["loss_intelligence"])
        self.assertIn("building_loss_rankings", e_data["loss_intelligence"])
        self.assertIn("loss", e_data["charts"])
        self.assertGreater(e_data["loss_intelligence"]["daily_financial_loss_inr"], 0)

        w_res = self.client.get("/api/water?range=24h")
        self.assertEqual(w_res.status_code, 200)
        w_data = w_res.get_json()
        self.assertTrue(w_data["success"])
        self.assertIn("kpis", w_data)

    def test_05_anomaly_detection_model(self):
        """
        Verify AI Anomaly Detection:
        - Normal usage returns is_anomaly = False
        - Significantly abnormal usage returns is_anomaly = True
        """
        detector = AnomalyDetector()
        
        # 1. Normal reading (Academic building at 2:00 PM with 300 occupants, ~110 kWh expected)
        normal_result = detector.detect_single(
            building_type="Academic",
            actual_value=105.0,
            occupancy=300,
            temperature=28.0,
            humidity=60.0,
            hour=14,
            day_of_week=2,
            resource="electricity"
        )
        self.assertFalse(normal_result["is_anomaly"], "Normal consumption should NOT trigger an anomaly")

        # 2. Abnormal reading (+50% spike, 210 kWh instead of 105 kWh)
        abnormal_result = detector.detect_single(
            building_type="Academic",
            actual_value=220.0,
            occupancy=300,
            temperature=28.0,
            humidity=60.0,
            hour=14,
            day_of_week=2,
            resource="electricity"
        )
        self.assertTrue(abnormal_result["is_anomaly"], "50%+ surge MUST trigger an anomaly")
        self.assertIn(abnormal_result["severity"], ["HIGH", "CRITICAL"])

    def test_06_explainable_ai(self):
        """Verify Transparent Explainable AI factor weights and explanation"""
        mock_anomaly = {
            "resource_type": "electricity",
            "deviation": 38.0,
            "actual_value": 1140.0,
            "expected_value": 820.0
        }
        mock_context = {
            "temperature": 32.0,
            "occupancy": 430,
            "hour": 14,
            "day_of_week": 2,
            "building_type": "Academic"
        }
        exp = AIExplainer.explain_anomaly(mock_anomaly, mock_context)
        self.assertIn("summary", exp)
        self.assertGreaterEqual(exp["confidence"], 85.0)
        
        # Verify factors exist and weights sum to ~100%
        factors = exp["contributing_factors"]
        self.assertGreaterEqual(len(factors), 3)
        total_weight = sum(f["weight_pct"] for f in factors)
        self.assertAlmostEqual(total_weight, 100, delta=2)

    def test_07_consumption_prediction(self):
        """Verify 24-hour ahead regression predictions"""
        predictor = ConsumptionPredictor(resource="electricity")
        forecast = predictor.predict_next_hours(
            building_id="BLK-A",
            building_type="Academic",
            current_features={"temperature": 30.0, "humidity": 65.0, "occupancy": 350},
            hours=24
        )
        self.assertEqual(len(forecast["hourly_forecast"]), 24)
        self.assertGreater(forecast["total_predicted"], 0)
        self.assertGreaterEqual(forecast["average_confidence"], 80.0)

    def test_08_what_if_simulator(self):
        """Verify What-If decision simulation, heatwave temperature penalty, and multi-scenario comparison"""
        building_data = {"current_energy": 1200.0, "current_water": 18000.0, "building_type": "Academic"}
        
        # 1. Single action simulation at standard 25°C
        sim = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=25.0)
        self.assertGreater(sim["energy_saved"], 0)
        self.assertGreater(sim["annual_saving"], 50000) # In INR
        self.assertGreater(sim["sustainability_impact_points"], 0)
        self.assertEqual(len(sim["hourly_before"]), 24)

        # 2. Temperature Increase Heatwave Loss Verification (At 38°C)
        sim_heat = WhatIfSimulator.simulate_action(building_data, "heatwave_surge", duration_hours=8.0, temperature=38.0)
        self.assertTrue(sim_heat["is_net_loss"], "High temperature heatwave must register as NET FINANCIAL LOSS")
        self.assertGreater(sim_heat["thermal_penalty"]["thermal_loss_kwh"], 0)
        self.assertGreater(sim_heat["thermal_penalty"]["thermal_loss_cost_daily"], 0)
        self.assertGreater(sim_heat["net_financial_loss_daily"], 0)

        # 3. High Temperature (45°C) with Intervention: Verifies BOTH action savings AND thermal loss are shown
        sim_45 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=45.0)
        self.assertTrue(sim_45["is_net_loss"], "45°C heat penalty exceeds 1h AC cut")
        self.assertGreater(sim_45["energy_saved"], 0, "Action savings MUST be preserved and shown")
        self.assertGreater(sim_45["cost_saved_daily"], 0, "Action cost savings MUST be preserved and shown")
        self.assertGreater(sim_45["thermal_penalty"]["thermal_loss_cost_daily"], 0, "Heat loss penalty must be shown")
        self.assertGreater(sim_45["net_financial_loss_daily"], 0, "Net loss must be calculated accurately")

        # 4. Temperature Decrease Natural Cooling Profit Verification (At 20°C - Below 25°C Baseline)
        sim_cool = WhatIfSimulator.simulate_action(building_data, "weather_fluctuation", duration_hours=8.0, temperature=20.0)
        self.assertFalse(sim_cool["is_net_loss"], "Cool temperature must register as NET PROFIT / SAVINGS")
        self.assertTrue(sim_cool["thermal_penalty"]["is_cool_bonus"], "Should have is_cool_bonus set to True")
        self.assertGreater(sim_cool["thermal_penalty"]["thermal_saving_kwh"], 0, "Must calculate positive natural cooling energy saved")
        self.assertGreater(sim_cool["thermal_penalty"]["thermal_saving_cost_daily"], 0, "Must calculate positive cooling profit in INR")
        self.assertGreater(sim_cool["energy_saved"], 0, "Total energy saved must be positive")
        self.assertGreater(sim_cool["cost_saved_daily"], 0, "Total daily cost saved must be positive")
        self.assertGreater(sim_cool["annual_saving"], 0, "Annual savings must reflect cooling profits")

        # 5. Outdoor Temperature Rise Monotonicity Verification:
        # As outdoor temperature increases (20°C -> 25°C -> 30°C -> 35°C -> 45°C),
        # net annual savings strictly reduces due to chiller thermal load surges
        sim_20 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=20.0)
        sim_25 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=25.0)
        sim_30 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=30.0)
        sim_35 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=35.0)
        sim_45 = WhatIfSimulator.simulate_action(building_data, "reduce_ac_1h", duration_hours=1.0, temperature=45.0)

        self.assertGreater(sim_20["annual_saving"], sim_25["annual_saving"], "Cooler ambient weather must yield higher savings than nominal 25°C")
        self.assertGreater(sim_25["annual_saving"], sim_30["annual_saving"], "30°C thermal load must reduce annual savings below 25°C")
        self.assertGreater(sim_30["annual_saving"], sim_35["annual_saving"], "35°C thermal load must reduce annual savings below 30°C")
        self.assertGreater(sim_35["annual_saving"], sim_45["annual_saving"], "45°C thermal load must reduce annual savings below 35°C")

        # 6. Multi-scenario comparison
        scenarios = [
            {"name": "Scenario A", "action": "reduce_ac_1h", "duration": 1.0},
            {"name": "Scenario B", "action": "reduce_ac_2h", "duration": 2.0}
        ]
        comparison = WhatIfSimulator.compare_scenarios(building_data, scenarios, temperature=30.0)
        self.assertIsNotNone(comparison["best_scenario"])
        self.assertEqual(len(comparison["scenarios"]), 2)

    def test_09_sustainability_score(self):
        """Verify GRIHA-aligned sustainability score calculation"""
        stats = {
            "energy_deviation_pct": -8.4,
            "water_deviation_pct": -5.2,
            "waste_ratio": 0.08,
            "co2_reduction_kg": 500.0,
            "recommendation_adoption_pct": 75.0
        }
        score = SustainabilityCalculator.calculate_campus_score(stats)
        self.assertGreaterEqual(score["overall_score"], 80.0)
        self.assertEqual(score["rating"], "Excellent")
        self.assertEqual(len(score["components"]), 5)

    def test_10_reports_generation(self):
        """Verify PDF report generation via ReportLab"""
        res = self.client.post("/api/reports/generate", json={
            "report_type": "AI Impact Report",
            "format": "PDF"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(os.path.exists(data["report"]["file_path"]))

    def test_11_chatbot_copilot(self):
        """Verify EcoAI Assistant chatbot query processing"""
        res = self.client.post("/api/chat", json={
            "message": "Which building wastes the most electricity?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("kWh", data["response"])

if __name__ == "__main__":
    unittest.main()
