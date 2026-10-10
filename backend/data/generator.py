import os
import json
import random
import bcrypt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from backend.database import SessionLocal, init_db
from backend.models import (
    User, Campus, Building, EnergyConsumption, WaterConsumption,
    OccupancyData, WeatherData, Anomaly, Prediction, Recommendation,
    SimulationResult, Alert, SustainabilityMetric, Report, AuditLog
)
from backend.config import Config

def seed_database():
    """
    Populates MySQL database with rich, realistic multi-week campus dataset
    including intentional anomalies for live hackathon demonstration.
    """
    init_db()
    db = SessionLocal()
    
    try:
        # Check if already seeded
        if db.query(Campus).count() > 0:
            print("Database already contains data. Checking records...")
            # If buildings exist, verify users
            if db.query(User).count() == 0:
                create_default_users(db)
            return

        print("Seeding EcoCampus AI database with realistic campus telemetry...")

        # 1. Create Default Users
        create_default_users(db)

        # 2. Create Campus
        campus = Campus(
            id="CAMPUS-1",
            name="EcoCampus Main Campus",
            location="Bangalore Tech Corridor, KA",
            total_area_sqft=450000.0
        )
        db.add(campus)
        db.commit()

        # 3. Create Buildings
        buildings_def = [
            {"id": "BLK-ADMIN", "name": "Administrative Block", "type": "Administrative", "area": 25000.0, "cap": 250, "floors": 4, "status": "normal"},
            {"id": "BLK-A", "name": "Academic Block A", "type": "Academic", "area": 45000.0, "cap": 800, "floors": 4, "status": "warning"},
            {"id": "BLK-B", "name": "Academic Block B", "type": "Academic", "area": 40000.0, "cap": 750, "floors": 4, "status": "warning"},
            {"id": "LIB-MAIN", "name": "Central Library", "type": "Academic", "area": 30000.0, "cap": 500, "floors": 3, "status": "normal"},
            {"id": "LAB-COMP", "name": "Laboratory Complex", "type": "Academic", "area": 35000.0, "cap": 400, "floors": 3, "status": "critical"},
            {"id": "HOSTEL-A", "name": "Hostel Block A", "type": "Residential", "area": 50000.0, "cap": 600, "floors": 5, "status": "normal"},
            {"id": "HOSTEL-B", "name": "Hostel Block B", "type": "Residential", "area": 48000.0, "cap": 550, "floors": 5, "status": "normal"},
            {"id": "CAFE-CTR", "name": "Central Cafeteria", "type": "Facility", "area": 18000.0, "cap": 350, "floors": 2, "status": "normal"},
        ]

        for b in buildings_def:
            b_obj = Building(
                id=b["id"],
                campus_id="CAMPUS-1",
                name=b["name"],
                building_type=b["type"],
                area_sqft=b["area"],
                capacity=b["cap"],
                floors=b["floors"],
                status=b["status"]
            )
            db.add(b_obj)
        db.commit()

        # 4. Generate 30 days of hourly telemetry
        print("Generating 30 days of hourly time-series readings...")
        end_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(days=30)
        
        current_dt = start_time
        batch_energy = []
        batch_water = []
        batch_occ = []
        batch_weather = []

        total_hours = 30 * 24
        
        while current_dt <= end_time:
            hour = current_dt.hour
            dow = current_dt.weekday()
            is_weekend = dow in [5, 6]
            
            # Weather for this hour
            diurnal_temp = 28.5 + 4.5 * np.sin((hour - 9) * np.pi / 12) + random.uniform(-0.8, 0.8)
            humidity = 68.0 - 15.0 * np.sin((hour - 9) * np.pi / 12) + random.uniform(-3.0, 3.0)
            cond = "Sunny" if (8 <= hour <= 17 and random.random() > 0.3) else ("Clear" if hour < 6 or hour > 19 else "Partly Cloudy")
            
            w_rec = WeatherData(
                timestamp=current_dt,
                temperature=round(diurnal_temp, 1),
                humidity=round(humidity, 1),
                weather_condition=cond
            )
            batch_weather.append(w_rec)

            for b in buildings_def:
                b_id = b["id"]
                b_type = b["type"]
                cap = b["cap"]

                # Realistic Occupancy
                if b_type == "Residential":
                    if 6 <= hour <= 9 or 19 <= hour <= 23:
                        occ = int(cap * random.uniform(0.70, 0.92))
                    elif 10 <= hour <= 17:
                        occ = int(cap * (0.25 if not is_weekend else 0.65))
                    else:
                        occ = int(cap * 0.85)
                elif b_type == "Facility":
                    if (12 <= hour <= 14) or (19 <= hour <= 21) or (7 <= hour <= 9):
                        occ = int(cap * random.uniform(0.65, 0.95))
                    else:
                        occ = int(cap * random.uniform(0.08, 0.25))
                else: # Academic / Administrative
                    if 8 <= hour <= 17:
                        occ = int(cap * (random.uniform(0.60, 0.88) if not is_weekend else 0.12))
                    elif 18 <= hour <= 21:
                        occ = int(cap * (random.uniform(0.15, 0.35) if not is_weekend else 0.05))
                    else:
                        occ = int(cap * 0.04)

                pct_cap = round((occ / max(1, cap)) * 100.0, 1)
                batch_occ.append(OccupancyData(
                    building_id=b_id,
                    timestamp=current_dt,
                    occupancy_count=occ,
                    capacity_percentage=pct_cap
                ))

                # Baseline Energy (kWh)
                base_kw = {"Academic": 65.0, "Administrative": 45.0, "Laboratory": 110.0, "Residential": 50.0, "Facility": 35.0}.get(b_type, 50.0)
                time_mult = (1.0 if not is_weekend else 0.4) if (8 <= hour <= 18) else (0.6 if 18 < hour <= 22 else 0.25)
                cooling = max(0, diurnal_temp - 24.0) * (base_kw * 0.08)
                kwh = (base_kw * time_mult) + (occ * 0.12) + cooling + random.uniform(-2.5, 3.5)

                # Baseline Water (Liters)
                base_lpm = {"Academic": 250.0, "Administrative": 150.0, "Laboratory": 400.0, "Residential": 850.0, "Facility": 550.0}.get(b_type, 300.0)
                w_time_mult = (1.6 if (6 <= hour <= 9 or 18 <= hour <= 21) else 0.4) if b_type == "Residential" else ((1.2 if not is_weekend else 0.2) if 9 <= hour <= 17 else 0.1)
                liters = (base_lpm * w_time_mult) + (occ * 0.8) + random.uniform(-15.0, 25.0)

                # Intentional Demo Anomalies in the most recent 24-48 hours
                if (end_time - current_dt).total_seconds() < 86400:
                    # Academic Block A - 38% electricity surge
                    if b_id == "BLK-A" and 10 <= hour <= 16:
                        kwh *= 1.38
                    # Academic Block B - 34% water leakage
                    if b_id == "BLK-B" and 9 <= hour <= 18:
                        liters *= 1.34
                    # Laboratory Complex - 52% overload
                    if b_id == "LAB-COMP" and 18 <= hour <= 23:
                        kwh *= 1.52

                kwh = max(10.0, round(float(kwh), 2))
                liters = max(30.0, round(float(liters), 2))

                batch_energy.append(EnergyConsumption(
                    building_id=b_id,
                    timestamp=current_dt,
                    kwh=kwh,
                    peak_demand_kw=round(kwh * 1.15, 2),
                    source="smart_meter"
                ))

                batch_water.append(WaterConsumption(
                    building_id=b_id,
                    timestamp=current_dt,
                    liters=liters,
                    flow_rate_lpm=round(liters / 60.0, 2),
                    source="flow_sensor"
                ))

            current_dt += timedelta(hours=1)

            # Flush periodically to optimize memory
            if len(batch_energy) >= 1000:
                db.bulk_save_objects(batch_energy)
                db.bulk_save_objects(batch_water)
                db.bulk_save_objects(batch_occ)
                db.bulk_save_objects(batch_weather)
                db.commit()
                batch_energy, batch_water, batch_occ, batch_weather = [], [], [], []

        if batch_energy:
            db.bulk_save_objects(batch_energy)
            db.bulk_save_objects(batch_water)
            db.bulk_save_objects(batch_occ)
            db.bulk_save_objects(batch_weather)
            db.commit()

        # 5. Insert Core Demo Anomalies
        print("Inserting core Explainable AI anomalies...")
        anomalies_def = [
            {
                "building_id": "BLK-A",
                "resource_type": "electricity",
                "expected_value": 820.0,
                "actual_value": 1140.0,
                "deviation": 39.0,
                "score": 0.91,
                "severity": "HIGH",
                "causes": json.dumps(["High building occupancy surge (+18%)", "Elevated outdoor ambient temperature (32°C)", "AC cooling compressor overload", "Non-scheduled classroom usage"]),
                "ai_explanation": "Electricity consumption in Academic Block A is 39% above normal. Occupancy increased by 18% during peak hours and outdoor temperature climbed 4°C above baseline, driving continuous chiller duty cycles.",
                "factors": json.dumps([
                    {"factor": "Outdoor Temperature", "expected": "28.0 °C", "actual": "32.0 °C", "impact": "HIGH", "weight_pct": 42, "detail": "High ambient heat load forced chillers to operate at maximum duty cycle."},
                    {"factor": "Occupancy Surge", "expected": "350 persons", "actual": "430 persons", "impact": "HIGH", "weight_pct": 28, "detail": "Department symposium drew concurrent crowd, surging lighting & plug loads."},
                    {"factor": "AC Chiller Continuous Duty", "expected": "Modulated 65%", "actual": "Continuous 98%", "impact": "HIGH", "weight_pct": 18, "detail": "Thermostat setpoint held at 20°C instead of standard 24°C."},
                    {"factor": "Time & Schedule Drift", "expected": "Normal timetable", "actual": "Extended lab hours", "impact": "MEDIUM", "weight_pct": 12, "detail": "Post-lecture equipment kept energized."}
                ]),
                "detected_at": end_time - timedelta(hours=3, minutes=18)
            },
            {
                "building_id": "BLK-B",
                "resource_type": "water",
                "expected_value": 3200.0,
                "actual_value": 4288.0,
                "deviation": 34.0,
                "score": 0.88,
                "severity": "HIGH",
                "causes": json.dumps(["Sustained high laminar flow rate", "Localized distribution pressure drop (-0.8 bar)", "Suspected washroom solenoid valve breach", "Continuous off-cycle discharge"]),
                "ai_explanation": "Water consumption in Academic Block B is 34% higher than historical baseline. Continuous volumetric flow sustained past class hours strongly points to a plumbing line fracture or malfunctioning cistern.",
                "factors": json.dumps([
                    {"factor": "Volumetric Flow Rate", "expected": "53 L/min", "actual": "71 L/min", "impact": "HIGH", "weight_pct": 52, "detail": "Continuous uniform discharge detected over 3+ hours."},
                    {"factor": "Line Water Pressure", "expected": "3.2 bar", "actual": "2.4 bar", "impact": "HIGH", "weight_pct": 28, "detail": "Drop in branch line pressure indicates leakage down-pipe."},
                    {"factor": "Occupancy Disparity", "expected": "310 persons", "actual": "220 persons", "impact": "MEDIUM", "weight_pct": 20, "detail": "Consumption rose despite 29% lower head count."}
                ]),
                "detected_at": end_time - timedelta(hours=5, minutes=40)
            },
            {
                "building_id": "LAB-COMP",
                "resource_type": "electricity",
                "expected_value": 950.0,
                "actual_value": 1444.0,
                "deviation": 52.0,
                "score": 0.95,
                "severity": "CRITICAL",
                "causes": json.dumps(["Heavy laboratory autoclaves & fume hoods left active", "Off-hours zero-occupancy draw", "Phase imbalance detected on Sub-panel 2"]),
                "ai_explanation": "Critical energy waste detected in Laboratory Complex: electricity usage is 52% above baseline during non-operational evening hours.",
                "factors": json.dumps([
                    {"factor": "Off-Hours Base Load", "expected": "400 kWh", "actual": "1444 kWh", "impact": "HIGH", "weight_pct": 58, "detail": "High-draw equipment running unattended with 0 occupancy."},
                    {"factor": "Fume Hood Exhausts", "expected": "Standby mode", "actual": "100% face velocity", "impact": "HIGH", "weight_pct": 26, "detail": "Exhaust dampers not closed after 6:00 PM."},
                    {"factor": "Ambient Temperature", "expected": "26.0 °C", "actual": "27.5 °C", "impact": "LOW", "weight_pct": 16, "detail": "Minor cooling penalty."}
                ]),
                "detected_at": end_time - timedelta(hours=14)
            }
        ]

        saved_anoms = []
        for ad in anomalies_def:
            anom = Anomaly(
                building_id=ad["building_id"],
                resource_type=ad["resource_type"],
                expected_value=ad["expected_value"],
                actual_value=ad["actual_value"],
                deviation=ad["deviation"],
                anomaly_score=ad["score"],
                severity=ad["severity"],
                possible_causes=ad["causes"],
                ai_explanation=ad["ai_explanation"],
                contributing_factors=ad["factors"],
                detected_at=ad["detected_at"],
                status="ACTIVE"
            )
            db.add(anom)
            db.commit()
            saved_anoms.append(anom)

        # 6. Insert AI Recommendations
        print("Inserting AI Recommendations...")
        recs_def = [
            {
                "building_id": "BLK-A",
                "anomaly_id": saved_anoms[0].id if saved_anoms else None,
                "action": "Reduce AC operation by 1 hour/day & adjust cooling setpoint to 24.5°C in Block A",
                "reason": "Block A has unusually high cooling-related consumption during moderate occupancy intervals.",
                "energy_saving": 120.0,
                "water_saving": 0.0,
                "cost_saving": 900.0,
                "co2_reduction": 80.0,
                "confidence": 89.0,
                "status": "PENDING",
                "explanation": "Resetting chiller setpoint from 20°C to 24.5°C and reducing pre-cooling run-time eliminates 120 kWh/day waste without degrading classroom occupant thermal comfort."
            },
            {
                "building_id": "BLK-B",
                "anomaly_id": saved_anoms[1].id if len(saved_anoms) > 1 else None,
                "action": "Dispatch maintenance to isolate and repair washroom plumbing leak in Academic Block B",
                "reason": "Continuous off-hours water flow indicates active pipe or cistern valve leak.",
                "energy_saving": 4.5,
                "water_saving": 1050.0,
                "cost_saving": 26.25,
                "co2_reduction": 3.7,
                "confidence": 93.4,
                "status": "PENDING",
                "explanation": "Isolating the faulty riser line will immediately preserve ~1,050 Liters of municipal water daily and save pumping energy."
            },
            {
                "building_id": "LAB-COMP",
                "anomaly_id": saved_anoms[2].id if len(saved_anoms) > 2 else None,
                "action": "Automate nighttime shutdown of heavy laboratory autoclaves and fume hood dampers",
                "reason": "Unattended equipment operation in Laboratory Complex during off-schedule hours.",
                "energy_saving": 310.0,
                "water_saving": 0.0,
                "cost_saving": 2325.0,
                "co2_reduction": 203.0,
                "confidence": 95.0,
                "status": "PENDING",
                "explanation": "Enforcing automated digital timers and setback policies saves ₹69,750 per month across research suites."
            },
            {
                "building_id": "LIB-MAIN",
                "anomaly_id": None,
                "action": "Implement smart daylight-harvesting dimmers on Library perimeter stacks",
                "reason": "Library perimeter receives abundant ambient daylight (>600 lux) from 9 AM to 4 PM.",
                "energy_saving": 45.0,
                "water_saving": 0.0,
                "cost_saving": 337.5,
                "co2_reduction": 29.5,
                "confidence": 91.0,
                "status": "PENDING",
                "explanation": "Daylight sensors step down LED troffer arrays automatically, yielding smooth energy optimization."
            }
        ]

        for r in recs_def:
            rec_obj = Recommendation(
                building_id=r["building_id"],
                anomaly_id=r["anomaly_id"],
                action=r["action"],
                reason=r["reason"],
                energy_saving=r["energy_saving"],
                water_saving=r["water_saving"],
                cost_saving=r["cost_saving"],
                co2_reduction=r["co2_reduction"],
                confidence=r["confidence"],
                status=r["status"],
                explanation=r["explanation"]
            )
            db.add(rec_obj)
        db.commit()

        # 7. Insert What-If Simulation Scenarios
        print("Inserting multi-scenario simulation presets...")
        sims_def = [
            {
                "building_id": "BLK-A",
                "action": "Reduce AC Usage by 1 hour/day",
                "duration_hours": 1.0,
                "baseline_energy": 1200.0,
                "simulated_energy": 1080.0,
                "energy_saved": 120.0,
                "cost_saved": 900.0,
                "co2_reduction": 80.0,
                "annual_saving": 328500.0,
                "sustainability_impact": 6.0,
                "scenario_name": "Scenario A: Reduce AC by 1 hr"
            },
            {
                "building_id": "BLK-A",
                "action": "Reduce AC Usage by 2 hours/day",
                "duration_hours": 2.0,
                "baseline_energy": 1200.0,
                "simulated_energy": 980.0,
                "energy_saved": 220.0,
                "cost_saved": 1650.0,
                "co2_reduction": 145.0,
                "annual_saving": 602250.0,
                "sustainability_impact": 8.5,
                "scenario_name": "Scenario B: Reduce AC by 2 hrs"
            },
            {
                "building_id": "BLK-A",
                "action": "Optimize Lighting & Smart Thermostat (+1.5°C)",
                "duration_hours": 8.0,
                "baseline_energy": 1200.0,
                "simulated_energy": 1045.0,
                "energy_saved": 155.0,
                "cost_saved": 1162.5,
                "co2_reduction": 102.0,
                "annual_saving": 424312.5,
                "sustainability_impact": 7.8,
                "scenario_name": "Scenario C: Optimize Lighting & Thermostat"
            }
        ]

        for s in sims_def:
            sim_obj = SimulationResult(
                building_id=s["building_id"],
                action=s["action"],
                duration_hours=s["duration_hours"],
                baseline_energy=s["baseline_energy"],
                simulated_energy=s["simulated_energy"],
                energy_saved=s["energy_saved"],
                baseline_water=18000.0,
                simulated_water=18000.0,
                water_saved=0.0,
                cost_saved=s["cost_saved"],
                co2_reduction=s["co2_reduction"],
                annual_saving=s["annual_saving"],
                sustainability_impact=s["sustainability_impact"],
                scenario_name=s["scenario_name"]
            )
            db.add(sim_obj)
        db.commit()

        # 8. Insert Real-Time Alerts
        print("Inserting real-time alerts...")
        alerts_def = [
            {
                "building_id": "BLK-A",
                "title": "Abnormal Electricity Spike (+39%)",
                "message": "Electricity consumption in Academic Block A is 39% above expected baseline (1,140 kWh vs 820 kWh).",
                "severity": "HIGH"
            },
            {
                "building_id": "BLK-B",
                "title": "Possible Water Leakage Detected",
                "message": "Water flow in Academic Block B is 34% higher than normal historical baseline. Suspected plumbing line leak.",
                "severity": "HIGH"
            },
            {
                "building_id": "LAB-COMP",
                "title": "Severe Off-Hours Energy Draw (+52%)",
                "message": "Laboratory Complex active load exceeds baseline by 52% with near-zero building occupancy.",
                "severity": "CRITICAL"
            },
            {
                "building_id": "LIB-MAIN",
                "title": "Predicted Energy Waste Ramp-up",
                "message": "AI prediction models indicate 142 kWh potential energy waste over the next 24 hours if thermostat setpoint remains unchanged.",
                "severity": "MEDIUM"
            }
        ]

        for a in alerts_def:
            db.add(Alert(
                building_id=a["building_id"],
                type="system",
                title=a["title"],
                message=a["message"],
                severity=a["severity"],
                is_read=False
            ))
        db.commit()

        # 9. Insert Sustainability Metrics
        print("Inserting sustainability index calculations...")
        sus_metric = SustainabilityMetric(
            building_id=None, # Campus Wide
            energy_score=88.5,
            water_score=82.0,
            waste_score=86.0,
            co2_score=84.5,
            optimization_score=81.0,
            overall_score=85.0
        )
        db.add(sus_metric)
        db.commit()

        # Generate sample CSV for test upload
        generate_sample_csv()

        print("EcoCampus AI database successfully seeded and verified!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

def create_default_users(db):
    salt = bcrypt.gensalt()
    admin_pw = bcrypt.hashpw(b"Admin@123", salt).decode('utf-8')
    mgr_pw = bcrypt.hashpw(b"Manager@123", salt).decode('utf-8')
    
    if not db.query(User).filter_by(email="admin@ecocampus.ai").first():
        admin = User(
            name="Dr. Rajesh Sharma (Director of Facilities)",
            email="admin@ecocampus.ai",
            password_hash=admin_pw,
            role="admin",
            assigned_buildings="ALL"
        )
        db.add(admin)

    if not db.query(User).filter_by(email="manager@ecocampus.ai").first():
        manager = User(
            name="Priya Nair (Campus Sustainability Officer)",
            email="manager@ecocampus.ai",
            password_hash=mgr_pw,
            role="campus_manager",
            assigned_buildings="BLK-A,BLK-B,LAB-COMP"
        )
        db.add(manager)
    db.commit()

def generate_sample_csv():
    """Creates a downloadable/testable CSV telemetry file for the Data Management module"""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    csv_path = Config.UPLOAD_FOLDER / "campus_telemetry_sample.csv"
    
    now = datetime.now()
    records = []
    buildings = ["BLK-A", "BLK-B", "BLK-ADMIN", "LIB-MAIN", "LAB-COMP"]
    
    for i in range(48): # 48 hours
        dt = now - timedelta(hours=48 - i)
        for b in buildings:
            records.append({
                "timestamp": dt.strftime("%Y-%m-%d %H:%M"),
                "building_id": b,
                "electricity_kwh": round(random.uniform(65.0, 185.0), 2),
                "water_liters": round(random.uniform(250.0, 950.0), 1),
                "occupancy": random.randint(30, 480),
                "temperature": round(27.0 + random.uniform(0.0, 6.5), 1),
                "humidity": round(55.0 + random.uniform(0.0, 20.0), 1)
            })
            
    df = pd.DataFrame(records)
    df.to_csv(csv_path, index=False)
    print(f"Sample telemetry CSV generated at: {csv_path}")

if __name__ == "__main__":
    seed_database()
