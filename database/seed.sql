-- EcoCampus AI - Seed Data Script
-- AI-Powered Predictive Campus Resource Optimization System
-- Campus: EcoCampus Main Campus (Bangalore Tech Corridor)

USE ecocampus_ai;

-- 1. Campuses
INSERT INTO campuses (id, name, location, total_area_sqft)
VALUES ('CAMPUS-1', 'EcoCampus Main Campus', 'Bangalore Tech Corridor, KA', 450000.0)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. Users (Passwords: Admin@123 and Manager@123 hashed with bcrypt)
INSERT INTO users (name, email, password_hash, role, assigned_buildings)
VALUES 
('Dr. Rajesh Sharma (Director of Facilities)', 'admin@ecocampus.ai', '$2b$12$G1uAxLjL/IhZc75jn.IMDOWuaNx9x5fMzABdl3uwh0t5Fwei7dK4S', 'admin', 'ALL'),
('Priya Nair (Campus Sustainability Officer)', 'manager@ecocampus.ai', '$2b$12$G1uAxLjL/IhZc75jn.IMDOWuaNx9x5fMzABdl3uwh0t5Fwei7dK4S', 'campus_manager', 'BLK-A,BLK-B,LAB-COMP')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. Buildings
INSERT INTO buildings (id, campus_id, name, building_type, area_sqft, capacity, floors, status)
VALUES
('BLK-ADMIN', 'CAMPUS-1', 'Administrative Block', 'Administrative', 25000.0, 250, 4, 'normal'),
('BLK-A', 'CAMPUS-1', 'Academic Block A', 'Academic', 45000.0, 800, 4, 'warning'),
('BLK-B', 'CAMPUS-1', 'Academic Block B', 'Academic', 40000.0, 750, 4, 'warning'),
('LIB-MAIN', 'CAMPUS-1', 'Central Library', 'Academic', 30000.0, 500, 3, 'normal'),
('LAB-COMP', 'CAMPUS-1', 'Laboratory Complex', 'Academic', 35000.0, 400, 3, 'critical'),
('HOSTEL-A', 'CAMPUS-1', 'Hostel Block A', 'Residential', 50000.0, 600, 5, 'normal'),
('HOSTEL-B', 'CAMPUS-1', 'Hostel Block B', 'Residential', 48000.0, 550, 5, 'normal'),
('CAFE-CTR', 'CAMPUS-1', 'Central Cafeteria', 'Facility', 18000.0, 350, 2, 'normal')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 4. Initial Core Explainable AI Anomalies
INSERT INTO anomalies (building_id, resource_type, expected_value, actual_value, deviation, anomaly_score, severity, possible_causes, ai_explanation, contributing_factors, detected_at, status)
VALUES
('BLK-A', 'electricity', 820.0, 1140.0, 39.0, 0.91, 'HIGH', 
 '["High building occupancy surge (+18%)", "Elevated outdoor ambient temperature (32°C)", "AC cooling compressor overload", "Non-scheduled classroom usage"]',
 'Electricity consumption in Academic Block A is 39% above normal. Occupancy increased by 18% during peak hours and outdoor temperature climbed 4°C above baseline, driving continuous chiller duty cycles.',
 '[{"factor": "Outdoor Temperature", "expected": "28.0 °C", "actual": "32.0 °C", "impact": "HIGH", "weight_pct": 42}, {"factor": "Occupancy Surge", "expected": "350 persons", "actual": "430 persons", "impact": "HIGH", "weight_pct": 28}, {"factor": "AC Chiller Continuous Duty", "expected": "Modulated 65%", "actual": "Continuous 98%", "impact": "HIGH", "weight_pct": 18}, {"factor": "Time & Schedule Drift", "expected": "Normal timetable", "actual": "Extended lab hours", "impact": "MEDIUM", "weight_pct": 12}]',
 NOW() - INTERVAL 3 HOUR, 'ACTIVE'),

('BLK-B', 'water', 3200.0, 4288.0, 34.0, 0.88, 'HIGH',
 '["Sustained high laminar flow rate", "Localized distribution pressure drop (-0.8 bar)", "Suspected washroom solenoid valve breach", "Continuous off-cycle discharge"]',
 'Water consumption in Academic Block B is 34% higher than historical baseline. Continuous volumetric flow sustained past class hours strongly points to a plumbing line fracture or malfunctioning cistern.',
 '[{"factor": "Volumetric Flow Rate", "expected": "53 L/min", "actual": "71 L/min", "impact": "HIGH", "weight_pct": 52}, {"factor": "Line Water Pressure", "expected": "3.2 bar", "actual": "2.4 bar", "impact": "HIGH", "weight_pct": 28}, {"factor": "Occupancy Disparity", "expected": "310 persons", "actual": "220 persons", "impact": "MEDIUM", "weight_pct": 20}]',
 NOW() - INTERVAL 5 HOUR, 'ACTIVE'),

('LAB-COMP', 'electricity', 950.0, 1444.0, 52.0, 0.95, 'CRITICAL',
 '["Heavy laboratory autoclaves & fume hoods left active", "Off-hours zero-occupancy draw", "Phase imbalance detected on Sub-panel 2"]',
 'Critical energy waste detected in Laboratory Complex: electricity usage is 52% above baseline during non-operational evening hours.',
 '[{"factor": "Off-Hours Base Load", "expected": "400 kWh", "actual": "1444 kWh", "impact": "HIGH", "weight_pct": 58}, {"factor": "Fume Hood Exhausts", "expected": "Standby mode", "actual": "100% face velocity", "impact": "HIGH", "weight_pct": 26}, {"factor": "Ambient Temperature", "expected": "26.0 °C", "actual": "27.5 °C", "impact": "LOW", "weight_pct": 16}]',
 NOW() - INTERVAL 12 HOUR, 'ACTIVE');

-- 5. AI Recommendations
INSERT INTO recommendations (building_id, action, reason, energy_saving, water_saving, cost_saving, co2_reduction, confidence, status, explanation)
VALUES
('BLK-A', 'Reduce AC operation by 1 hour/day & adjust cooling setpoint to 24.5°C in Block A', 'Block A has unusually high cooling-related consumption during moderate occupancy intervals.', 120.0, 0.0, 900.0, 80.0, 89.0, 'PENDING', 'Resetting chiller setpoint from 20°C to 24.5°C and reducing pre-cooling run-time eliminates 120 kWh/day waste without degrading classroom occupant thermal comfort.'),
('BLK-B', 'Dispatch maintenance to isolate and repair washroom plumbing leak in Academic Block B', 'Continuous off-hours water flow indicates active pipe or cistern valve leak.', 4.5, 1050.0, 26.25, 3.7, 93.4, 'PENDING', 'Isolating the faulty riser line will immediately preserve ~1,050 Liters of municipal water daily and save pumping energy.'),
('LAB-COMP', 'Automate nighttime shutdown of heavy laboratory autoclaves and fume hood dampers', 'Unattended equipment operation in Laboratory Complex during off-schedule hours.', 310.0, 0.0, 2325.0, 203.0, 95.0, 'PENDING', 'Enforcing automated digital timers and setback policies saves ₹69,750 per month across research suites.');

-- 6. Alerts
INSERT INTO alerts (building_id, type, title, message, severity, is_read)
VALUES
('BLK-A', 'anomaly', 'Abnormal Electricity Spike (+39%)', 'Electricity consumption in Academic Block A is 39% above expected baseline (1,140 kWh vs 820 kWh).', 'HIGH', 0),
('BLK-B', 'leak', 'Possible Water Leakage Detected', 'Water flow in Academic Block B is 34% higher than normal historical baseline. Suspected plumbing line leak.', 'HIGH', 0),
('LAB-COMP', 'overload', 'Severe Off-Hours Energy Draw (+52%)', 'Laboratory Complex active load exceeds baseline by 52% with near-zero building occupancy.', 'CRITICAL', 0);

-- 7. Sustainability Metrics
INSERT INTO sustainability_metrics (building_id, energy_score, water_score, waste_score, co2_score, optimization_score, overall_score)
VALUES (NULL, 88.5, 82.0, 86.0, 84.5, 81.0, 85.0);
