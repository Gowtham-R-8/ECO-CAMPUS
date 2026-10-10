from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.models import Building, EnergyConsumption, WaterConsumption, SimulationResult
from backend.ai.simulator import WhatIfSimulator
from sqlalchemy import desc

simulator_bp = Blueprint("simulator", __name__, url_prefix="/api/simulator")

@simulator_bp.route("/presets", methods=["GET"])
def get_presets():
    return jsonify({
        "success": True,
        "presets": WhatIfSimulator.ACTION_PRESETS
    })

@simulator_bp.route("/run", methods=["POST"])
def run_simulation():
    data = request.get_json() or {}
    building_id = data.get("building_id", "BLK-A")
    action = data.get("action", "reduce_ac_1h")
    duration_hours = float(data.get("duration_hours", 1.0))
    temperature = float(data.get("temperature", 32.0))
    occupancy_multiplier = float(data.get("occupancy_multiplier", 1.0))

    db = SessionLocal()
    try:
        bldg = db.query(Building).filter_by(id=building_id).first()
        if not bldg:
            return jsonify({"success": False, "error": "Building not found"}), 404

        # Calculate current baseline
        recent_e = db.query(EnergyConsumption).filter_by(building_id=building_id).order_by(desc(EnergyConsumption.timestamp)).limit(24).all()
        recent_w = db.query(WaterConsumption).filter_by(building_id=building_id).order_by(desc(WaterConsumption.timestamp)).limit(24).all()

        current_energy = sum(r.kwh for r in recent_e) if recent_e else 1200.0
        current_water = sum(r.liters for r in recent_w) if recent_w else 18000.0

        building_data = {
            "current_energy": current_energy,
            "current_water": current_water,
            "building_type": bldg.building_type
        }

        result = WhatIfSimulator.simulate_action(
            building_data, action, duration_hours=duration_hours,
            occupancy_multiplier=occupancy_multiplier, temperature=temperature
        )

        # Save record into simulation_results
        sim_rec = SimulationResult(
            building_id=building_id,
            action=result["action_name"],
            duration_hours=duration_hours,
            baseline_energy=result["baseline_energy"],
            simulated_energy=result["simulated_energy"],
            energy_saved=result["energy_saved"],
            baseline_water=result["baseline_water"],
            simulated_water=result["simulated_water"],
            water_saved=result["water_saved"],
            cost_saved=result["cost_saved_daily"],
            co2_reduction=result["co2_reduction_monthly_kg"],
            annual_saving=result["annual_saving"],
            sustainability_impact=result["sustainability_impact_points"],
            scenario_name=data.get("scenario_name", "Live What-If Simulation")
        )
        db.add(sim_rec)
        db.commit()

        result["building_name"] = bldg.name
        result["simulation_id"] = sim_rec.id

        return jsonify({"success": True, "result": result})
    finally:
        db.close()

@simulator_bp.route("/compare", methods=["POST"])
def compare_scenarios_endpoint():
    data = request.get_json() or {}
    building_id = data.get("building_id", "BLK-A")
    scenarios = data.get("scenarios", [
        {"name": "Scenario A: Reduce AC by 1 hr", "action": "reduce_ac_1h", "duration": 1.0},
        {"name": "Scenario B: Reduce AC by 2 hrs", "action": "reduce_ac_2h", "duration": 2.0},
        {"name": "Scenario C: Optimize Lighting", "action": "optimize_lighting", "duration": 8.0}
    ])

    db = SessionLocal()
    try:
        bldg = db.query(Building).filter_by(id=building_id).first()
        b_name = bldg.name if bldg else building_id

        building_data = {
            "current_energy": 1200.0,
            "current_water": 18000.0,
            "building_type": bldg.building_type if bldg else "Academic"
        }

        temperature = float(data.get("temperature", 32.0))
        comparison = WhatIfSimulator.compare_scenarios(building_data, scenarios, temperature=temperature)
        comparison["building_id"] = building_id
        comparison["building_name"] = b_name

        return jsonify({"success": True, "comparison": comparison})
    finally:
        db.close()
