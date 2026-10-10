from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.models import SustainabilityMetric, Building, EnergyConsumption, WaterConsumption, Recommendation
from backend.ai.sustainability import SustainabilityCalculator
from sqlalchemy import func

sustainability_bp = Blueprint("sustainability", __name__, url_prefix="/api/sustainability")

@sustainability_bp.route("", methods=["GET"])
def get_sustainability_overview():
    db = SessionLocal()
    try:
        # Check active recommendations applied
        applied_recs = db.query(Recommendation).filter_by(status="APPLIED").count()
        total_recs = max(1, db.query(Recommendation).count())
        adoption_pct = (applied_recs / total_recs) * 100.0

        stats = {
            "energy_deviation_pct": -8.4,
            "water_deviation_pct": -5.2,
            "waste_ratio": 0.075,
            "co2_reduction_kg": 520.0 + (applied_recs * 80.0),
            "recommendation_adoption_pct": max(65.0, adoption_pct)
        }

        score_data = SustainabilityCalculator.calculate_campus_score(stats)

        # Historical trend simulation (last 6 months)
        trends = {
            "months": ["May 2026", "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026"],
            "sustainability_score": [74.2, 76.8, 78.5, 81.0, 83.4, score_data["overall_score"]],
            "co2_reduction_tons": [12.4, 14.1, 15.8, 17.5, 18.9, 21.4],
            "energy_saved_mwh": [18.2, 21.0, 23.5, 26.8, 28.5, 31.2],
            "cost_saved_lakhs": [1.36, 1.57, 1.76, 2.01, 2.13, 2.34]
        }

        # Building performance rank
        buildings = db.query(Building).all()
        building_rankings = []
        for b in buildings:
            b_score = 88.0
            if b.status == "critical":
                b_score = 64.0
            elif b.status == "warning":
                b_score = 76.5
            building_rankings.append({
                "building_id": b.id,
                "building_name": b.name,
                "building_type": b.building_type,
                "score": b_score,
                "status": b.status
            })

        building_rankings.sort(key=lambda x: x["score"], reverse=True)

        return jsonify({
            "success": True,
            "sustainability": score_data,
            "trends": trends,
            "building_rankings": building_rankings
        })
    finally:
        db.close()

@sustainability_bp.route("/<building_id>", methods=["GET"])
def get_building_sustainability(building_id):
    db = SessionLocal()
    try:
        bldg = db.query(Building).filter_by(id=building_id).first()
        if not bldg:
            return jsonify({"success": False, "error": "Building not found"}), 404

        stats = {
            "energy_deviation_pct": -4.0 if bldg.status == "normal" else 28.0,
            "water_deviation_pct": -3.0 if bldg.status != "warning" else 34.0,
            "waste_ratio": 0.05 if bldg.status == "normal" else 0.16,
            "co2_reduction_kg": 120.0,
            "recommendation_adoption_pct": 80.0
        }
        score_data = SustainabilityCalculator.calculate_campus_score(stats)

        return jsonify({
            "success": True,
            "building_id": building_id,
            "building_name": bldg.name,
            "sustainability": score_data
        })
    finally:
        db.close()
