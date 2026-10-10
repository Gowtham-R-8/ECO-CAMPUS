import random
from datetime import datetime
from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.models import EnergyConsumption, WaterConsumption, OccupancyData, WeatherData, Building, Anomaly, Alert
from backend.ai.anomaly_detection import AnomalyDetector
from backend.ai.explainability import AIExplainer

demo_bp = Blueprint("demo", __name__, url_prefix="/api/demo")

# Global demo state
demo_state = {
    "is_demo_mode": True,
    "tick_count": 0,
    "last_tick": datetime.now().isoformat()
}

@demo_bp.route("/status", methods=["GET"])
def get_demo_status():
    return jsonify({
        "success": True,
        "is_demo_mode": demo_state["is_demo_mode"],
        "tick_count": demo_state["tick_count"],
        "last_tick": demo_state["last_tick"]
    })

@demo_bp.route("/toggle", methods=["POST"])
def toggle_demo_mode():
    data = request.get_json() or {}
    mode = data.get("demo_mode")
    if mode is None:
        demo_state["is_demo_mode"] = not demo_state["is_demo_mode"]
    else:
        demo_state["is_demo_mode"] = bool(mode)

    return jsonify({
        "success": True,
        "is_demo_mode": demo_state["is_demo_mode"],
        "message": f"Switched to {'DEMO DATA (Simulated)' if demo_state['is_demo_mode'] else 'LIVE DATA (Hardware/IoT)'} mode"
    })

@demo_bp.route("/tick", methods=["POST"])
def trigger_tick():
    """
    Generates the next real-time reading across all buildings
    simulating live incoming IoT telemetry streams.
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        buildings = db.query(Building).all()
        detector = AnomalyDetector()

        # Slight weather fluctuation
        new_temp = round(29.0 + random.uniform(-1.5, 2.5), 1)
        new_hum = round(62.0 + random.uniform(-4.0, 4.0), 1)
        w_rec = WeatherData(
            timestamp=now,
            temperature=new_temp,
            humidity=new_hum,
            weather_condition="Sunny" if random.random() > 0.4 else "Partly Cloudy"
        )
        db.add(w_rec)

        updates = []
        for b in buildings:
            # Baseline calculation
            hour = now.hour
            dow = now.weekday()
            is_weekend = dow in [5, 6]
            cap = b.capacity or 400

            occ = int(cap * (random.uniform(0.55, 0.85) if (8 <= hour <= 18 and not is_weekend) else 0.15))
            pct_cap = round((occ / max(1, cap)) * 100.0, 1)

            db.add(OccupancyData(
                building_id=b.id,
                timestamp=now,
                occupancy_count=occ,
                capacity_percentage=pct_cap
            ))

            base_kwh = {"Academic": 70.0, "Administrative": 45.0, "Laboratory": 115.0, "Residential": 50.0, "Facility": 35.0}.get(b.building_type, 50.0)
            kwh = base_kwh * (random.uniform(0.9, 1.1)) + (occ * 0.10) + max(0, new_temp - 25.0) * 3.0
            
            # If warning/critical building, simulate sustained elevated usage
            if b.id == "BLK-A":
                kwh *= 1.35
            elif b.id == "LAB-COMP":
                kwh *= 1.45

            kwh = round(float(kwh), 2)
            liters = round(float(random.uniform(250.0, 650.0) * (1.34 if b.id == "BLK-B" else 1.0)), 1)

            e_rec = EnergyConsumption(
                building_id=b.id,
                timestamp=now,
                kwh=kwh,
                peak_demand_kw=round(kwh * 1.15, 2),
                source="demo_stream"
            )
            w_rec = WaterConsumption(
                building_id=b.id,
                timestamp=now,
                liters=liters,
                flow_rate_lpm=round(liters / 60.0, 2),
                source="demo_stream"
            )
            db.add(e_rec)
            db.add(w_rec)

            updates.append({"building_id": b.id, "kwh": kwh, "liters": liters, "occupancy": occ})

        db.commit()
        demo_state["tick_count"] += 1
        demo_state["last_tick"] = now.isoformat()

        return jsonify({
            "success": True,
            "message": "Generated new simulated telemetry tick",
            "tick_count": demo_state["tick_count"],
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "updates_count": len(updates)
        })
    finally:
        db.close()

@demo_bp.route("/inject-anomaly", methods=["POST"])
def inject_anomaly():
    """
    Intentionally injects an abnormal spike into a building so the anomaly
    detection and explainable AI card can be demonstrated live in real time.
    """
    data = request.get_json() or {}
    b_id = data.get("building_id", "BLK-A")
    resource = data.get("resource", "electricity")
    spike_pct = float(data.get("spike_pct", 45.0))

    db = SessionLocal()
    try:
        bldg = db.query(Building).filter_by(id=b_id).first()
        if not bldg:
            return jsonify({"success": False, "error": "Building not found"}), 404

        now = datetime.now()
        detector = AnomalyDetector()

        expected = 800.0 if resource == "electricity" else 2500.0
        actual = expected * (1.0 + spike_pct / 100.0)
        temp_val = 33.5
        occ_val = int(bldg.capacity * 0.90)

        # Record energy/water spike
        if resource == "electricity":
            db.add(EnergyConsumption(
                building_id=b_id,
                timestamp=now,
                kwh=actual,
                peak_demand_kw=actual * 1.2,
                source="anomaly_injection"
            ))
        else:
            db.add(WaterConsumption(
                building_id=b_id,
                timestamp=now,
                liters=actual,
                flow_rate_lpm=actual / 60.0,
                source="anomaly_injection"
            ))

        # Run explainability
        context = {
            "temperature": temp_val,
            "occupancy": occ_val,
            "hour": now.hour,
            "day_of_week": now.weekday(),
            "building_type": bldg.building_type
        }
        mock_anom = {
            "resource_type": resource,
            "deviation": spike_pct,
            "actual_value": actual,
            "expected_value": expected
        }
        exp = AIExplainer.explain_anomaly(mock_anom, context)

        import json
        new_anom = Anomaly(
            building_id=b_id,
            resource_type=resource,
            expected_value=expected,
            actual_value=actual,
            deviation=spike_pct,
            anomaly_score=0.94,
            severity="CRITICAL" if spike_pct >= 40 else "HIGH",
            possible_causes=json.dumps([f["detail"] for f in exp["contributing_factors"]]),
            ai_explanation=exp["summary"],
            contributing_factors=json.dumps(exp["contributing_factors"]),
            detected_at=now,
            status="ACTIVE"
        )
        db.add(new_anom)

        # Trigger real-time alert
        alert = Alert(
            building_id=b_id,
            type="anomaly",
            title=f"LIVE SPIKE: {bldg.name} {resource.capitalize()} (+{spike_pct}%)",
            message=f"Live telemetry spike detected: {resource.capitalize()} reached {actual:,.1f} vs expected {expected:,.1f}.",
            severity="CRITICAL" if spike_pct >= 40 else "HIGH"
        )
        db.add(alert)
        bldg.status = "critical" if spike_pct >= 40 else "warning"

        db.commit()

        return jsonify({
            "success": True,
            "message": f"Live {resource} anomaly successfully injected into {bldg.name}",
            "anomaly": new_anom.to_dict(),
            "alert": alert.to_dict()
        })
    finally:
        db.close()
