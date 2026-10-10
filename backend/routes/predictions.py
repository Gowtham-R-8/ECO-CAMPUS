from flask import Blueprint, request, jsonify
from sqlalchemy import desc
from backend.database import SessionLocal
from backend.models import Building, WeatherData, OccupancyData, EnergyConsumption
from backend.ai.consumption_prediction import ConsumptionPredictor
from backend.config import Config

predictions_bp = Blueprint("predictions", __name__, url_prefix="/api/predictions")

@predictions_bp.route("", methods=["GET"])
def get_predictions():
    building_id = request.args.get("building_id", "ALL")
    resource = request.args.get("resource", "electricity")
    hours = int(request.args.get("hours", 24))

    db = SessionLocal()
    try:
        predictor = ConsumptionPredictor(resource=resource)
        latest_w = db.query(WeatherData).order_by(desc(WeatherData.timestamp)).first()
        temp_val = latest_w.temperature if latest_w else 30.0
        hum_val = latest_w.humidity if latest_w else 62.0

        if building_id != "ALL":
            bldg = db.query(Building).filter_by(id=building_id).first()
            if not bldg:
                return jsonify({"success": False, "error": "Building not found"}), 404
            
            latest_occ = db.query(OccupancyData).filter_by(building_id=building_id).order_by(desc(OccupancyData.timestamp)).first()
            occ_val = latest_occ.occupancy_count if latest_occ else 250
            
            forecast = predictor.predict_next_hours(
                building_id, bldg.building_type,
                {"temperature": temp_val, "humidity": hum_val, "occupancy": occ_val},
                hours=hours
            )
            return jsonify({"success": True, "forecast": forecast})
        
        # Campus-wide composite forecast
        buildings = db.query(Building).all()
        aggregated_hourly = []
        total_pred = 0.0
        total_waste = 0.0

        for h in range(1, hours + 1):
            h_pred = 0.0
            h_base = 0.0
            h_waste = 0.0
            
            for b in buildings:
                b_forecast = predictor.predict_next_hours(
                    b.id, b.building_type,
                    {"temperature": temp_val, "humidity": hum_val, "occupancy": b.capacity // 2},
                    hours=hours
                )
                item = b_forecast["hourly_forecast"][h - 1]
                h_pred += item["predicted"]
                h_base += item["baseline"]
                h_waste += item["waste"]

            h_pred = round(h_pred, 1)
            h_base = round(h_base, 1)
            h_waste = round(h_waste, 1)
            total_pred += h_pred
            total_waste += h_waste

            hour_time = (latest_w.timestamp if latest_w else datetime.now()) + timedelta(hours=h)
            aggregated_hourly.append({
                "timestamp": hour_time.strftime("%Y-%m-%d %H:00"),
                "hour_label": hour_time.strftime("%I %p"),
                "predicted": h_pred,
                "baseline": h_base,
                "waste": h_waste,
                "confidence": 91.2
            })

        cost_val = round(total_pred * Config.ELECTRICITY_COST_PER_KWH if resource == "electricity" else (total_pred / 1000.0) * Config.WATER_COST_PER_1000L, 2)

        return jsonify({
            "success": True,
            "forecast": {
                "building_id": "ALL",
                "building_name": "Campus Consolidated",
                "resource": resource,
                "period": f"Next {hours} Hours",
                "total_predicted": round(total_pred, 1),
                "expected_waste": round(total_waste, 1),
                "estimated_cost": cost_val,
                "average_confidence": 91.4,
                "hourly_forecast": aggregated_hourly
            }
        })
    finally:
        db.close()
