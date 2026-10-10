import numpy as np

class SustainabilityCalculator:
    WEIGHTS = {
        "energy_efficiency": 0.25,
        "water_efficiency": 0.20,
        "waste_reduction": 0.20,
        "co2_impact": 0.20,
        "resource_optimization": 0.15
    }

    @classmethod
    def calculate_campus_score(cls, stats):
        """
        Calculates granular and overall sustainability scores.
        stats dictionary may contain:
        - energy_deviation_pct: deviation from green target (e.g. -8.4%)
        - water_deviation_pct: deviation from water target (e.g. -5.2%)
        - waste_ratio: waste vs total consumption (e.g. 0.08)
        - co2_savings_ratio: CO2 mitigated vs baseline
        - recommendation_adoption_pct: percentage of AI recommendations applied
        """
        # 1. Energy Efficiency (25% weight)
        # Base 80, bonus if under baseline, penalty if excess
        e_dev = stats.get("energy_deviation_pct", -5.0)
        energy_score = np.clip(85.0 - (e_dev * 1.2), 40.0, 98.0)

        # 2. Water Efficiency (20% weight)
        w_dev = stats.get("water_deviation_pct", -4.0)
        water_score = np.clip(84.0 - (w_dev * 1.1), 35.0, 96.0)

        # 3. Waste Reduction (20% weight)
        # Low waste ratio yields high score
        waste_ratio = stats.get("waste_ratio", 0.07)
        waste_score = np.clip(100.0 - (waste_ratio * 250.0), 45.0, 99.0)

        # 4. CO2 Impact (20% weight)
        co2_reduction_kg = stats.get("co2_reduction_kg", 450.0)
        co2_score = np.clip(78.0 + min(18.0, co2_reduction_kg * 0.02), 50.0, 98.0)

        # 5. Resource Optimization / AI Adoption (15% weight)
        adoption_pct = stats.get("recommendation_adoption_pct", 75.0)
        opt_score = np.clip(70.0 + (adoption_pct * 0.25), 40.0, 95.0)

        # Weighted composite score
        overall = (
            energy_score * cls.WEIGHTS["energy_efficiency"] +
            water_score * cls.WEIGHTS["water_efficiency"] +
            waste_score * cls.WEIGHTS["waste_reduction"] +
            co2_score * cls.WEIGHTS["co2_impact"] +
            opt_score * cls.WEIGHTS["resource_optimization"]
        )

        overall = round(float(overall), 1)

        # Rating tier
        if overall >= 81.0:
            rating = "Excellent"
            color = "#10B981" # Emerald Green
            grade = "A+"
        elif overall >= 61.0:
            rating = "Good"
            color = "#3B82F6" # Blue
            grade = "A"
        elif overall >= 41.0:
            rating = "Moderate"
            color = "#F59E0B" # Amber
            grade = "B"
        else:
            rating = "Needs Improvement"
            color = "#EF4444" # Red
            grade = "C"

        return {
            "overall_score": overall,
            "rating": rating,
            "grade": grade,
            "color": color,
            "components": {
                "energy_efficiency": {
                    "score": round(float(energy_score), 1),
                    "weight_pct": 25,
                    "benchmark": "National Green Campus Standard (GRIHA)",
                    "description": "Building specific energy index (kWh/m²/year) against regional benchmarks."
                },
                "water_efficiency": {
                    "score": round(float(water_score), 1),
                    "weight_pct": 20,
                    "benchmark": "Per-capita campus consumption index",
                    "description": "Laminar flow regulation, pressure equilibrium, and leakage minimization."
                },
                "waste_reduction": {
                    "score": round(float(waste_score), 1),
                    "weight_pct": 20,
                    "benchmark": "Parasitic off-peak load mitigation",
                    "description": "Detection and curtailment of non-operational phantom load waste."
                },
                "co2_impact": {
                    "score": round(float(co2_score), 1),
                    "weight_pct": 20,
                    "benchmark": "Scope 2 grid emissions reduction",
                    "description": "Aggregated emissions saved via smart setbacks and load shifting."
                },
                "resource_optimization": {
                    "score": round(float(opt_score), 1),
                    "weight_pct": 15,
                    "benchmark": "Corrective AI recommendation closed-loop implementation",
                    "description": "Facility response velocity to predictive recommendations."
                }
            }
        }
