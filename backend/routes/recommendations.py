from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.models import Recommendation, Building, Anomaly, AuditLog, SustainabilityMetric
from backend.ai.recommendation_engine import RecommendationEngine

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")

@recommendations_bp.route("", methods=["GET"])
def list_recommendations():
    building_filter = request.args.get("building_id")
    status_filter = request.args.get("status", "ALL")

    db = SessionLocal()
    try:
        query = db.query(Recommendation)
        if building_filter and building_filter != "ALL":
            query = query.filter(Recommendation.building_id == building_filter)
        if status_filter != "ALL":
            query = query.filter(Recommendation.status == status_filter)

        recs = query.order_by(Recommendation.created_at.desc()).all()
        return jsonify({
            "success": True,
            "total": len(recs),
            "recommendations": [r.to_dict() for r in recs]
        })
    finally:
        db.close()

@recommendations_bp.route("/generate", methods=["POST"])
def generate_recommendations_endpoint():
    db = SessionLocal()
    try:
        buildings = db.query(Building).all()
        generated_count = 0

        for b in buildings:
            anomalies = [a.to_dict() for a in db.query(Anomaly).filter_by(building_id=b.id, status="ACTIVE").all()]
            new_recs = RecommendationEngine.generate_recommendations(b.id, b.name, b.building_type, anomalies)

            for nr in new_recs:
                # Check duplicate
                existing = db.query(Recommendation).filter_by(building_id=b.id, action=nr["action"], status="PENDING").first()
                if not existing:
                    rec_obj = Recommendation(
                        building_id=nr["building_id"],
                        anomaly_id=nr.get("anomaly_id"),
                        action=nr["action"],
                        reason=nr["reason"],
                        energy_saving=nr["energy_saving"],
                        water_saving=nr["water_saving"],
                        cost_saving=nr["cost_saving"],
                        co2_reduction=nr["co2_reduction"],
                        confidence=nr["confidence"],
                        status="PENDING",
                        explanation=nr.get("explanation")
                    )
                    db.add(rec_obj)
                    generated_count += 1

        db.commit()
        return jsonify({
            "success": True,
            "message": f"Generated {generated_count} new AI recommendations",
            "count": generated_count
        })
    finally:
        db.close()

@recommendations_bp.route("/<int:rec_id>/apply", methods=["POST"])
def apply_recommendation(rec_id):
    """
    Applies the recommendation in the decision-support system.
    Records the operational decision, updates sustainability metric, and logs audit.
    """
    db = SessionLocal()
    try:
        rec = db.query(Recommendation).filter_by(id=rec_id).first()
        if not rec:
            return jsonify({"success": False, "error": "Recommendation not found"}), 404

        rec.status = "APPLIED"
        
        # Log audit entry
        audit = AuditLog(
            user_email="admin@ecocampus.ai",
            action="APPLY_RECOMMENDATION",
            details=f"Applied action '{rec.action}' for building {rec.building_id}. Estimated daily energy savings: {rec.energy_saving} kWh, cost: ₹{rec.cost_saving}."
        )
        db.add(audit)

        # Boost campus sustainability optimization metric
        metric = db.query(SustainabilityMetric).first()
        if metric:
            metric.optimization_score = min(99.0, metric.optimization_score + 1.2)
            metric.overall_score = min(99.0, metric.overall_score + 0.4)

        db.commit()

        return jsonify({
            "success": True,
            "message": f"Recommendation applied successfully. Action recorded for facility operations.",
            "notice": "Decision recorded in campus log. Physical equipment actuation requires facility operations or future IoT integration.",
            "recommendation": rec.to_dict()
        })
    finally:
        db.close()

@recommendations_bp.route("/<int:rec_id>/dismiss", methods=["PUT"])
def dismiss_recommendation(rec_id):
    db = SessionLocal()
    try:
        rec = db.query(Recommendation).filter_by(id=rec_id).first()
        if not rec:
            return jsonify({"success": False, "error": "Recommendation not found"}), 404

        rec.status = "DISMISSED"
        db.commit()
        return jsonify({"success": True, "recommendation": rec.to_dict()})
    finally:
        db.close()
