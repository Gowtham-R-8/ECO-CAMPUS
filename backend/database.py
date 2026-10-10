import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from backend.config import Config

logger = logging.getLogger("ecocampus.db")
Base = declarative_base()

def get_engine():
    try:
        # Attempt MySQL connection first
        engine = create_engine(
            Config.SQLALCHEMY_DATABASE_URI,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info("Connected to MySQL database successfully.")
        return engine
    except Exception as e:
        logger.warning(f"Failed to connect to MySQL ({e}). Falling back to SQLite database.")
        sqlite_engine = create_engine(
            Config.SQLITE_URI,
            connect_args={"check_same_thread": False}
        )
        return sqlite_engine

engine = get_engine()
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from backend.models import (
        User, Campus, Building, EnergyConsumption, WaterConsumption,
        OccupancyData, WeatherData, Anomaly, Prediction, Recommendation,
        SimulationResult, Alert, SustainabilityMetric, Report, AuditLog
    )
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
