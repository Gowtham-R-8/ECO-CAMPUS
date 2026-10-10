from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from backend.database import SessionLocal
from backend.models import Building, EnergyConsumption, WaterConsumption, OccupancyData, WeatherData, Anomaly, Recommendation, Prediction, SustainabilityMetric

buildings_bp = Blueprint("buildings", __name__, url_prefix="/api/buildings")

@buildings_bp.route("", methods=["GET"])
def list_buildings():
    db = SessionLocal()
    try:
        buildings = db.query(Building).all()
        result = []
        
        # Get latest weather temperature
        latest_weather = db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()
        current_temp = latest_weather.temperature if latest_weather else 29.5

        for b in buildings:
            # Latest energy
            latest_e = db.query(EnergyConsumption).filter_by(building_id=b.id).order_by(desc(EnergyConsumption.timestamp)).first()
            # Latest water
            latest_w = db.query(WaterConsumption).filter_by(building_id=b.id).order_by(desc(WaterConsumption.timestamp)).first()
            # Latest occupancy
            latest_occ = db.query(OccupancyData).filter_by(building_id=b.id).order_by(desc(OccupancyData.timestamp)).first()
            # Active anomalies count
            active_anoms = db.query(Anomaly).filter_by(building_id=b.id, status="ACTIVE").count()

            # Dynamic sustainability score
            sus_score = 88.0
            if b.status == "critical":
                sus_score = 64.0
            elif b.status == "warning":
                sus_score = 76.5

            b_dict = b.to_dict()
            b_dict.update({
                "current_electricity_kwh": latest_e.kwh if latest_e else 0.0,
                "current_water_liters": latest_w.liters if latest_w else 0.0,
                "current_occupancy": latest_occ.occupancy_count if latest_occ else 0,
                "occupancy_percentage": latest_occ.capacity_percentage if latest_occ else 0.0,
                "temperature": current_temp,
                "active_anomalies": active_anoms,
                "sustainability_score": sus_score
            })
            result.append(b_dict)

        return jsonify({"success": True, "buildings": result})
    finally:
        db.close()

@buildings_bp.route("/<building_id>", methods=["GET"])
def get_building_detail(building_id):
    db = SessionLocal()
    try:
        bldg = db.query(Building).filter_by(id=building_id).first()
        if not bldg:
            return jsonify({"success": False, "error": "Building not found"}), 404

        # Recent 24h energy
        energy_records = (
            db.query(EnergyConsumption)
            .filter_by(building_id=building_id)
            .order_by(desc(EnergyConsumption.timestamp))
            .limit(24)
            .all()
        )
        energy_records.reverse()

        # Recent 24h water
        water_records = (
            db.query(WaterConsumption)
            .filter_by(building_id=building_id)
            .order_by(desc(WaterConsumption.timestamp))
            .limit(24)
            .all()
        )
        water_records.reverse()

        # Recent occupancy
        occ_records = (
            db.query(OccupancyData)
            .filter_by(building_id=building_id)
            .order_by(desc(OccupancyData.timestamp))
            .limit(24)
            .all()
        )
        occ_records.reverse()

        # Anomalies
        anomalies = db.query(Anomaly).filter_by(building_id=building_id).order_by(desc(Anomaly.detected_at)).all()

        # Recommendations
        recommendations = db.query(Recommendation).filter_by(building_id=building_id).all()

        # Latest Weather
        weather = db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()

        # Building KPIs
        latest_e = energy_records[-1].kwh if energy_records else 0.0
        daily_e = sum(r.kwh for r in energy_records) if energy_records else 0.0
        daily_w = sum(r.liters for r in water_records) if water_records else 0.0
        peak_e = max((r.kwh for r in energy_records), default=0.0)
        avg_e = (daily_e / len(energy_records)) if energy_records else 0.0

        return jsonify({
            "success": True,
            "building": bldg.to_dict(),
            "kpis": {
                "current_electricity_kwh": latest_e,
                "daily_electricity_kwh": round(daily_e, 1),
                "peak_load_kw": round(peak_e, 1),
                "avg_load_kw": round(avg_e, 1),
                "daily_water_liters": round(daily_w, 1),
                "occupancy": occ_records[-1].occupancy_count if occ_records else 0,
                "capacity_percentage": occ_records[-1].capacity_percentage if occ_records else 0.0,
                "temperature": weather.temperature if weather else 29.0
            },
            "energy_history": [r.to_dict() for r in energy_records],
            "water_history": [r.to_dict() for r in water_records],
            "occupancy_history": [r.to_dict() for r in occ_records],
            "anomalies": [a.to_dict() for a in anomalies],
            "recommendations": [r.to_dict() for r in recommendations]
        })
    finally:
        db.close()

@buildings_bp.route("", methods=["POST"])
def create_building():
    data = request.get_json() or {}
    b_id = data.get("id", "").strip().upper()
    name = data.get("name", "").strip()

    if not b_id or not name:
        return jsonify({"success": False, "error": "Building ID and name are required"}), 400

    db = SessionLocal()
    try:
        existing = db.query(Building).filter_by(id=b_id).first()
        if existing:
            return jsonify({"success": False, "error": f"Building {b_id} already exists"}), 400

        new_b = Building(
            id=b_id,
            campus_id=data.get("campus_id", "CAMPUS-1"),
            name=name,
            building_type=data.get("building_type", "Academic"),
            area_sqft=float(data.get("area_sqft", 25000)),
            capacity=int(data.get("capacity", 300)),
            floors=int(data.get("floors", 3)),
            status=data.get("status", "normal")
        )
        db.add(new_b)
        db.commit()
        return jsonify({"success": True, "building": new_b.to_dict()})
    finally:
        db.close()

@buildings_bp.route("/<building_id>", methods=["PUT"])
def update_building(building_id):
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        b = db.query(Building).filter_by(id=building_id).first()
        if not b:
            return jsonify({"success": False, "error": "Building not found"}), 404

        if "name" in data: b.name = data["name"]
        if "building_type" in data: b.building_type = data["building_type"]
        if "area_sqft" in data: b.area_sqft = float(data["area_sqft"])
        if "capacity" in data: b.capacity = int(data["capacity"])
        if "status" in data: b.status = data["status"]

        db.commit()
        return jsonify({"success": True, "building": b.to_dict()})
    finally:
        db.close()
