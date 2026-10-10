import os
from pathlib import Path
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from backend.config import Config
from backend.database import init_db, SessionLocal
from backend.models import Building, User
from backend.data.generator import seed_database

# Import Blueprints
from backend.routes.auth import auth_bp
from backend.routes.buildings import buildings_bp
from backend.routes.energy import energy_bp
from backend.routes.water import water_bp
from backend.routes.anomalies import anomalies_bp
from backend.routes.predictions import predictions_bp
from backend.routes.recommendations import recommendations_bp
from backend.routes.simulator import simulator_bp
from backend.routes.sustainability import sustainability_bp
from backend.routes.alerts import alerts_bp
from backend.routes.reports import reports_bp
from backend.routes.data import data_bp
from backend.routes.chatbot import chatbot_bp
from backend.routes.demo import demo_bp

def create_app():
    frontend_folder = Path(__file__).resolve().parent.parent / "frontend"
    
    app = Flask(
        __name__,
        static_folder=str(frontend_folder),
        static_url_path=""
    )
    
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(buildings_bp)
    app.register_blueprint(energy_bp)
    app.register_blueprint(water_bp)
    app.register_blueprint(anomalies_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(sustainability_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(demo_bp)

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health_check():
        db = SessionLocal()
        db_status = "connected"
        try:
            b_count = db.query(Building).count()
        except Exception as e:
            db_status = f"error: {str(e)}"
            b_count = 0
        finally:
            db.close()

        iso_model_ok = (Config.MODELS_FOLDER / "isolation_forest.joblib").exists()
        rf_model_ok = (Config.MODELS_FOLDER / "rf_electricity_predictor.joblib").exists()

        return jsonify({
            "status": "healthy",
            "service": "EcoCampus AI — Predictive Campus Resource Optimization System",
            "version": "1.0.0-production",
            "database": db_status,
            "buildings_loaded": b_count,
            "ml_models": {
                "isolation_forest": "ready" if iso_model_ok else "missing",
                "random_forest": "ready" if rf_model_ok else "missing"
            }
        })

    # Serve Frontend UI
    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_folder, "index.html")

    @app.route("/<path:path>")
    def serve_static(path):
        target = frontend_folder / path
        if target.exists() and not target.is_dir():
            return send_from_directory(frontend_folder, path)
        return send_from_directory(frontend_folder, "index.html")

    return app

app = create_app()

if __name__ == "__main__":
    # Ensure database is initialized and seeded
    try:
        init_db()
        db = SessionLocal()
        if db.query(Building).count() == 0:
            seed_database()
        db.close()
    except Exception as e:
        print(f"Database initialization warning: {e}")

    port = int(os.environ.get("PORT", 5000))
    print(f"Starting EcoCampus AI server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
