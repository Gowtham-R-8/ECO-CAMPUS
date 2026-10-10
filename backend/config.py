import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ecocampus-ai-super-secret-key-2026-prod")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ecocampus-jwt-secret-key-quantum-ai")
    
    # MySQL Database credentials
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecocampus_ai")
    
    # SQLAlchemy URI (Primary MySQL, fallback SQLite)
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    SQLITE_URI = f"sqlite:///{BASE_DIR / 'ecocampus_ai.db'}"
    
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Directories
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    REPORTS_FOLDER = BASE_DIR / "backend" / "reports"
    MODELS_FOLDER = BASE_DIR / "models"
    
    # Pricing & Carbon emission factors (India campus baseline)
    ELECTRICITY_COST_PER_KWH = 7.50  # ₹7.50 per kWh
    WATER_COST_PER_1000L = 25.00     # ₹25 per 1,000 Liters
    CO2_KG_PER_KWH = 0.82            # 0.82 kg CO2 per kWh (Grid average)
    
    # Demo Mode settings
    DEMO_MODE_DEFAULT = True
