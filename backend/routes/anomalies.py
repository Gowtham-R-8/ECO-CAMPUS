import json
from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from datetime import datetime
from backend.database import SessionLocal
from backend.models import Anomaly, Building, WeatherData, OccupancyData, EnergyConsumption
from backend.ai.anomaly_detection import AnomalyDetector
from backend.ai.explainability import AIExplainer

anomalies_bp = Blueprint("anomalies", __name__, url_prefix="/api/anomalies")

@anomalies_bp.route("", methods=["GET"])
def list_anomalies():
    severity_filter = request.args.get("severity")
    building_filter = request.args.get("building_id")
    status_filter = request.args.get("status")

    db = SessionLocal()
    try:
        query = db.query(Anomaly).order_by(desc(Anomaly.detected_at))
        if severity_filter and severity_filter != "ALL":
            query = query.filter(Anomaly.severity == severity_filter)
        if building_filter and building_filter != "ALL":
            query = query.filter(Anomaly.building_id == building_filter)
        if status_filter and status_filter != "ALL":
            query = query.filter(Anomaly.status == status_filter)

        anomalies = query.all()
        return jsonify({
            "success": True,
            "total": len(anomalies),
            "anomalies": [a.to_dict() for a in anomalies]
        })
    finally:
        db.close()

@anomalies_bp.route("/<int:anomaly_id>", methods=["GET"])
def get_anomaly_detail(anomaly_id):
    db = SessionLocal()
    try:
        anom = db.query(Anomaly).filter_by(id=anomaly_id).first()
        if not anom:
            return jsonify({"success": False, "error": "Anomaly not found"}), 404

        data = anom.to_dict()
        
        # If no explanation saved, generate on the fly
        if not data.get("contributing_factors"):
            weather = db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()
            occ = db.query(OccupancyData).filter_by(building_id=anom.building_id).order_by(desc(OccupancyData.timestamp)).first()
            context = {
                "temperature": weather.temperature if weather else 31.0,
                "humidity": weather.humidity if weather else 65.0,
                "occupancy": occ.occupancy_count if occ else 300,
                "hour": anom.detected_at.hour,
                "day_of_week": anom.detected_at.weekday(),
                "building_type": anom.building.building_type if anom.building else "Academic"
            }
            exp = AIExplainer.explain_anomaly(data, context)
            data["ai_explanation"] = exp["summary"]
            data["contributing_factors"] = exp["contributing_factors"]
            data["confidence"] = exp["confidence"]

        return jsonify({"success": True, "anomaly": data})
    finally:
        db.close()

@anomalies_bp.route("/analyze", methods=["POST"])
def run_anomaly_analysis():
    """Triggers real-time AI scan across all buildings"""
    db = SessionLocal()
    try:
        detector = AnomalyDetector()
        buildings = db.query(Building).all()
        latest_w = db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()
        now = datetime.now()

        detected_count = 0
        new_anomalies = []

        for b in buildings:
            latest_e = db.query(EnergyConsumption).filter_by(building_id=b.id).order_by(desc(EnergyConsumption.timestamp)).first()
            latest_occ = db.query(OccupancyData).filter_by(building_id=b.id).order_by(desc(OccupancyData.timestamp)).first()
            
            if not latest_e:
                continue

            occ_val = latest_occ.occupancy_count if latest_occ else int(b.capacity * 0.5)
            temp_val = latest_w.temperature if latest_w else 29.0
            hum_val = latest_w.humidity if latest_w else 60.0

            result = detector.detect_single(
                b.building_type, latest_e.kwh, occ_val, temp_val, hum_val, now.hour, now.weekday(), resource="electricity"
            )

            if result["is_anomaly"] and result["deviation"] > 25.0:
                # Check if recent anomaly already flagged
                existing = db.query(Anomaly).filter_by(building_id=b.id, resource_type="electricity", status="ACTIVE").first()
                if not existing:
                    context = {
                        "temperature": temp_val,
                        "humidity": hum_val,
                        "occupancy": occ_val,
                        "hour": now.hour,
                        "day_of_week": now.weekday(),
                        "building_type": b.building_type
                    }
                    exp = AIExplainer.explain_anomaly(result, context)
                    
                    new_a = Anomaly(
                        building_id=b.id,
                        resource_type="electricity",
                        expected_value=result["expected_value"],
                        actual_value=result["actual_value"],
                        deviation=result["deviation"],
                        anomaly_score=result["anomaly_score"],
                        severity=result["severity"],
                        possible_causes=json.dumps([f["detail"] for f in exp["contributing_factors"]]),
                        ai_explanation=exp["summary"],
                        contributing_factors=json.dumps(exp["contributing_factors"]),
                        detected_at=now,
                        status="ACTIVE"
                    )
                    db.add(new_a)
                    detected_count += 1
                    new_anomalies.append(b.name)

        db.commit()
        return jsonify({
            "success": True,
            "message": f"AI scan completed. Detected {detected_count} new anomalies.",
            "affected_buildings": new_anomalies
        })
    finally:
        db.close()

@anomalies_bp.route("/<int:anomaly_id>/status", methods=["PUT"])
def update_anomaly_status(anomaly_id):
    data = request.get_json() or {}
    new_status = data.get("status", "INVESTIGATING").upper()

    db = SessionLocal()
    try:
        anom = db.query(Anomaly).filter_by(id=anomaly_id).first()
        if not anom:
            return jsonify({"success": False, "error": "Anomaly not found"}), 404

        anom.status = new_status
        db.commit()
        return jsonify({"success": True, "anomaly": anom.to_dict()})
    finally:
        db.close()
