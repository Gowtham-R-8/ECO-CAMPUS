import os
from flask import Blueprint, request, jsonify, send_file
from backend.data.preprocessing import validate_and_process_csv, REQUIRED_COLUMNS
from backend.config import Config
from backend.database import SessionLocal
from backend.models import EnergyConsumption, WaterConsumption, OccupancyData, WeatherData, Building

data_bp = Blueprint("data", __name__, url_prefix="/api/data")

@data_bp.route("/stats", methods=["GET"])
def get_data_collection_stats():
    """Returns overview of data collection across the 6 core presentation categories"""
    db = SessionLocal()
    try:
        e_count = db.query(EnergyConsumption).count()
        w_count = db.query(WaterConsumption).count()
        b_count = db.query(Building).count()
        o_count = db.query(OccupancyData).count()
        weather_count = db.query(WeatherData).count()

        latest_time = db.query(EnergyConsumption.timestamp).order_by(EnergyConsumption.timestamp.desc()).first()

        return jsonify({
            "success": True,
            "categories": {
                "electricity": {"name": "Electricity Consumption", "records": e_count, "unit": "kWh", "status": "Active Streaming"},
                "water": {"name": "Water Consumption", "records": w_count, "unit": "Liters", "status": "Active Streaming"},
                "buildings": {"name": "Building Metadata", "records": b_count, "unit": "Facilities", "status": "Configured"},
                "occupancy": {"name": "Occupancy Telemetry", "records": o_count, "unit": "Counts", "status": "Active Streaming"},
                "weather": {"name": "Weather & Climate", "records": weather_count, "unit": "Readings", "status": "Active Sync"},
                "time": {"name": "Temporal Indices", "records": e_count, "unit": "Timestamps", "status": "Synchronized"}
            },
            "latest_sync": latest_time[0].strftime("%Y-%m-%d %H:%M") if latest_time else "N/A"
        })
    finally:
        db.close()

@data_bp.route("/upload", methods=["POST"])
def upload_data():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not file.filename.endswith(".csv"):
        return jsonify({"success": False, "error": "Only CSV files are supported"}), 400

    try:
        content = file.read()
        result = validate_and_process_csv(content)
        if not result["success"]:
            return jsonify(result), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@data_bp.route("/sample", methods=["GET"])
def download_sample_csv():
    sample_path = Config.UPLOAD_FOLDER / "campus_telemetry_sample.csv"
    if not os.path.exists(sample_path):
        from backend.data.generator import generate_sample_csv
        generate_sample_csv()

    return send_file(
        sample_path,
        as_attachment=True,
        download_name="campus_telemetry_template.csv",
        mimetype="text/csv"
    )
