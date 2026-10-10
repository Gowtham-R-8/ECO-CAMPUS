-- EcoCampus AI Database Schema
-- AI-Powered Predictive Campus Resource Optimization System

CREATE DATABASE IF NOT EXISTS ecocampus_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ecocampus_ai;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'campus_manager') DEFAULT 'campus_manager',
    assigned_buildings TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Campuses Table
CREATE TABLE IF NOT EXISTS campuses (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    location VARCHAR(150),
    total_area_sqft DOUBLE DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Buildings Table
CREATE TABLE IF NOT EXISTS buildings (
    id VARCHAR(50) PRIMARY KEY,
    campus_id VARCHAR(50) DEFAULT 'CAMPUS-1',
    name VARCHAR(150) NOT NULL,
    building_type VARCHAR(50),
    area_sqft DOUBLE DEFAULT 0,
    capacity INT DEFAULT 0,
    floors INT DEFAULT 3,
    status ENUM('normal', 'warning', 'critical') DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (campus_id) REFERENCES campuses(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Energy Consumption Table
CREATE TABLE IF NOT EXISTS energy_consumption (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    kwh DOUBLE NOT NULL,
    peak_demand_kw DOUBLE DEFAULT 0,
    source VARCHAR(50) DEFAULT 'smart_meter',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_energy_bldg_time (building_id, timestamp),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Water Consumption Table
CREATE TABLE IF NOT EXISTS water_consumption (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    liters DOUBLE NOT NULL,
    flow_rate_lpm DOUBLE DEFAULT 0,
    source VARCHAR(50) DEFAULT 'flow_sensor',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    KEY idx_water_bldg_time (building_id, timestamp),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Occupancy Data Table
CREATE TABLE IF NOT EXISTS occupancy_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    occupancy_count INT NOT NULL,
    capacity_percentage DOUBLE DEFAULT 0,
    KEY idx_occ_bldg_time (building_id, timestamp),
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Weather Data Table
CREATE TABLE IF NOT EXISTS weather_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    temperature DOUBLE NOT NULL,
    humidity DOUBLE NOT NULL,
    weather_condition VARCHAR(50) DEFAULT 'Sunny',
    KEY idx_weather_time (timestamp)
) ENGINE=InnoDB;

-- 8. Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    resource_type ENUM('electricity', 'water') NOT NULL,
    expected_value DOUBLE NOT NULL,
    actual_value DOUBLE NOT NULL,
    deviation DOUBLE NOT NULL,
    anomaly_score DOUBLE NOT NULL,
    severity ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW') NOT NULL,
    possible_causes TEXT,
    ai_explanation TEXT,
    contributing_factors TEXT,
    detected_at DATETIME NOT NULL,
    status ENUM('ACTIVE', 'INVESTIGATING', 'RESOLVED', 'DISMISSED') DEFAULT 'ACTIVE',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 9. Predictions Table
CREATE TABLE IF NOT EXISTS predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    resource_type ENUM('electricity', 'water') NOT NULL,
    prediction_time DATETIME NOT NULL,
    predicted_value DOUBLE NOT NULL,
    expected_waste DOUBLE DEFAULT 0,
    confidence DOUBLE NOT NULL,
    model_version VARCHAR(50) DEFAULT 'RandomForest-v1.0',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 10. Recommendations Table
CREATE TABLE IF NOT EXISTS recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    anomaly_id INT NULL,
    action VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    energy_saving DOUBLE DEFAULT 0,
    water_saving DOUBLE DEFAULT 0,
    cost_saving DOUBLE DEFAULT 0,
    co2_reduction DOUBLE DEFAULT 0,
    confidence DOUBLE DEFAULT 85,
    status ENUM('PENDING', 'APPLIED', 'DISMISSED') DEFAULT 'PENDING',
    explanation TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE,
    FOREIGN KEY (anomaly_id) REFERENCES anomalies(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 11. Simulation Results Table
CREATE TABLE IF NOT EXISTS simulation_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    action VARCHAR(255) NOT NULL,
    duration_hours DOUBLE DEFAULT 1.0,
    baseline_energy DOUBLE NOT NULL,
    simulated_energy DOUBLE NOT NULL,
    energy_saved DOUBLE NOT NULL,
    baseline_water DOUBLE DEFAULT 0,
    simulated_water DOUBLE DEFAULT 0,
    water_saved DOUBLE DEFAULT 0,
    cost_saved DOUBLE NOT NULL,
    co2_reduction DOUBLE NOT NULL,
    annual_saving DOUBLE NOT NULL,
    sustainability_impact DOUBLE NOT NULL,
    scenario_name VARCHAR(100) DEFAULT 'Scenario A',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 12. Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NOT NULL,
    type VARCHAR(50) DEFAULT 'system',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW') DEFAULT 'MEDIUM',
    is_read TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (building_id) REFERENCES buildings(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 13. Sustainability Metrics Table
CREATE TABLE IF NOT EXISTS sustainability_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    building_id VARCHAR(50) NULL,
    energy_score DOUBLE NOT NULL,
    water_score DOUBLE NOT NULL,
    waste_score DOUBLE NOT NULL,
    co2_score DOUBLE NOT NULL,
    optimization_score DOUBLE NOT NULL,
    overall_score DOUBLE NOT NULL,
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 14. Reports Table
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    report_type VARCHAR(100) NOT NULL,
    period_start DATE,
    period_end DATE,
    file_path VARCHAR(255),
    generated_by VARCHAR(100) DEFAULT 'Admin',
    summary_data TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 15. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(150),
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
