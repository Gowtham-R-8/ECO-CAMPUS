from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="campus_manager")  # 'admin' or 'campus_manager'
    assigned_buildings = Column(Text, nullable=True)  # comma separated building IDs
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "assigned_buildings": self.assigned_buildings.split(",") if self.assigned_buildings else [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Campus(Base):
    __tablename__ = "campuses"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    location = Column(String(150))
    total_area_sqft = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    buildings = relationship("Building", back_populates="campus", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "total_area_sqft": self.total_area_sqft,
            "buildings_count": len(self.buildings) if self.buildings else 0
        }

class Building(Base):
    __tablename__ = "buildings"
    
    id = Column(String(50), primary_key=True)
    campus_id = Column(String(50), ForeignKey("campuses.id"), default="CAMPUS-1")
    name = Column(String(150), nullable=False)
    building_type = Column(String(50), default="Academic")
    area_sqft = Column(Float, default=0.0)
    capacity = Column(Integer, default=0)
    floors = Column(Integer, default=3)
    status = Column(String(20), default="normal")  # 'normal', 'warning', 'critical'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    campus = relationship("Campus", back_populates="buildings")
    energy_records = relationship("EnergyConsumption", back_populates="building", cascade="all, delete-orphan")
    water_records = relationship("WaterConsumption", back_populates="building", cascade="all, delete-orphan")
    occupancy_records = relationship("OccupancyData", back_populates="building", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="building", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="building", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="building", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "campus_id": self.campus_id,
            "name": self.name,
            "building_type": self.building_type,
            "area_sqft": self.area_sqft,
            "capacity": self.capacity,
            "floors": self.floors,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class EnergyConsumption(Base):
    __tablename__ = "energy_consumption"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    kwh = Column(Float, nullable=False)
    peak_demand_kw = Column(Float, default=0.0)
    source = Column(String(50), default="smart_meter")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    building = relationship("Building", back_populates="energy_records")

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "kwh": round(self.kwh, 2),
            "peak_demand_kw": round(self.peak_demand_kw, 2),
            "source": self.source
        }

class WaterConsumption(Base):
    __tablename__ = "water_consumption"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    liters = Column(Float, nullable=False)
    flow_rate_lpm = Column(Float, default=0.0)
    source = Column(String(50), default="flow_sensor")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    building = relationship("Building", back_populates="water_records")

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "liters": round(self.liters, 2),
            "flow_rate_lpm": round(self.flow_rate_lpm, 2),
            "source": self.source
        }

class OccupancyData(Base):
    __tablename__ = "occupancy_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    occupancy_count = Column(Integer, nullable=False)
    capacity_percentage = Column(Float, default=0.0)
    
    building = relationship("Building", back_populates="occupancy_records")

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "occupancy_count": self.occupancy_count,
            "capacity_percentage": round(self.capacity_percentage, 1)
        }

class WeatherData(Base):
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    weather_condition = Column(String(50), default="Sunny")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "temperature": round(self.temperature, 1),
            "humidity": round(self.humidity, 1),
            "weather_condition": self.weather_condition
        }

class Anomaly(Base):
    __tablename__ = "anomalies"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    resource_type = Column(String(20), nullable=False)  # 'electricity' or 'water'
    expected_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    deviation = Column(Float, nullable=False)  # e.g. +38.5
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    possible_causes = Column(Text, nullable=True)  # JSON or text list
    ai_explanation = Column(Text, nullable=True)
    contributing_factors = Column(Text, nullable=True)  # JSON: factors breakdown
    detected_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="ACTIVE")  # 'ACTIVE', 'INVESTIGATING', 'RESOLVED', 'DISMISSED'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    building = relationship("Building", back_populates="anomalies")

    def to_dict(self):
        import json
        causes = []
        factors = {}
        try:
            if self.possible_causes:
                causes = json.loads(self.possible_causes) if self.possible_causes.startswith("[") else [self.possible_causes]
        except Exception:
            causes = [self.possible_causes]
            
        try:
            if self.contributing_factors:
                factors = json.loads(self.contributing_factors)
        except Exception:
            factors = {}

        return {
            "id": self.id,
            "building_id": self.building_id,
            "building_name": self.building.name if self.building else self.building_id,
            "resource_type": self.resource_type,
            "expected_value": round(self.expected_value, 2),
            "actual_value": round(self.actual_value, 2),
            "deviation": round(self.deviation, 1),
            "anomaly_score": round(self.anomaly_score, 2),
            "severity": self.severity,
            "possible_causes": causes,
            "ai_explanation": self.ai_explanation,
            "contributing_factors": factors,
            "detected_at": self.detected_at.strftime("%Y-%m-%d %H:%M"),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    resource_type = Column(String(20), nullable=False)
    prediction_time = Column(DateTime, nullable=False)
    predicted_value = Column(Float, nullable=False)
    expected_waste = Column(Float, default=0.0)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), default="RandomForest-v1.0")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    building = relationship("Building", back_populates="predictions")

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "building_name": self.building.name if self.building else self.building_id,
            "resource_type": self.resource_type,
            "prediction_time": self.prediction_time.strftime("%Y-%m-%d %H:%M"),
            "predicted_value": round(self.predicted_value, 2),
            "expected_waste": round(self.expected_waste, 2),
            "confidence": round(self.confidence, 1),
            "model_version": self.model_version
        }

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    anomaly_id = Column(Integer, ForeignKey("anomalies.id"), nullable=True)
    action = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    energy_saving = Column(Float, default=0.0)  # kWh/day
    water_saving = Column(Float, default=0.0)   # L/day
    cost_saving = Column(Float, default=0.0)    # ₹/day
    co2_reduction = Column(Float, default=0.0)  # kg/month
    confidence = Column(Float, default=85.0)
    status = Column(String(20), default="PENDING")  # 'PENDING', 'APPLIED', 'DISMISSED'
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    building = relationship("Building", back_populates="recommendations")

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "building_name": self.building.name if self.building else self.building_id,
            "anomaly_id": self.anomaly_id,
            "action": self.action,
            "reason": self.reason,
            "energy_saving": round(self.energy_saving, 1),
            "water_saving": round(self.water_saving, 1),
            "cost_saving": round(self.cost_saving, 2),
            "co2_reduction": round(self.co2_reduction, 1),
            "confidence": round(self.confidence, 1),
            "status": self.status,
            "explanation": self.explanation,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

class SimulationResult(Base):
    __tablename__ = "simulation_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    action = Column(String(255), nullable=False)
    duration_hours = Column(Float, default=1.0)
    baseline_energy = Column(Float, nullable=False)
    simulated_energy = Column(Float, nullable=False)
    energy_saved = Column(Float, nullable=False)
    baseline_water = Column(Float, default=0.0)
    simulated_water = Column(Float, default=0.0)
    water_saved = Column(Float, default=0.0)
    cost_saved = Column(Float, nullable=False)
    co2_reduction = Column(Float, nullable=False)
    annual_saving = Column(Float, nullable=False)
    sustainability_impact = Column(Float, nullable=False)
    scenario_name = Column(String(100), default="Scenario A")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "action": self.action,
            "duration_hours": self.duration_hours,
            "baseline_energy": round(self.baseline_energy, 2),
            "simulated_energy": round(self.simulated_energy, 2),
            "energy_saved": round(self.energy_saved, 2),
            "baseline_water": round(self.baseline_water, 2),
            "simulated_water": round(self.simulated_water, 2),
            "water_saved": round(self.water_saved, 2),
            "cost_saved": round(self.cost_saved, 2),
            "co2_reduction": round(self.co2_reduction, 2),
            "annual_saving": round(self.annual_saving, 2),
            "sustainability_impact": round(self.sustainability_impact, 1),
            "scenario_name": self.scenario_name,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), ForeignKey("buildings.id"), nullable=False)
    type = Column(String(50), default="system")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "is_read": bool(self.is_read),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

class SustainabilityMetric(Base):
    __tablename__ = "sustainability_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(String(50), nullable=True)  # Null = whole campus
    energy_score = Column(Float, nullable=False)
    water_score = Column(Float, nullable=False)
    waste_score = Column(Float, nullable=False)
    co2_score = Column(Float, nullable=False)
    optimization_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "building_id": self.building_id or "All Buildings (Campus)",
            "energy_score": round(self.energy_score, 1),
            "water_score": round(self.water_score, 1),
            "waste_score": round(self.waste_score, 1),
            "co2_score": round(self.co2_score, 1),
            "optimization_score": round(self.optimization_score, 1),
            "overall_score": round(self.overall_score, 1),
            "calculated_at": self.calculated_at.strftime("%Y-%m-%d %H:%M")
        }

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(100), nullable=False)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    file_path = Column(String(255), nullable=True)
    generated_by = Column(String(100), default="Admin")
    summary_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        summary = {}
        try:
            if self.summary_data:
                summary = json.loads(self.summary_data)
        except Exception:
            summary = {}
        return {
            "id": self.id,
            "report_type": self.report_type,
            "period_start": self.period_start.strftime("%Y-%m-%d") if self.period_start else None,
            "period_end": self.period_end.strftime("%Y-%m-%d") if self.period_end else None,
            "file_path": self.file_path,
            "generated_by": self.generated_by,
            "summary_data": summary,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M")
        }

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(150))
    action = Column(String(100), nullable=False)
    details = Column(Text)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_email": self.user_email,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
