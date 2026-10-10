from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.models import Alert
from sqlalchemy import desc

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")

@alerts_bp.route("", methods=["GET"])
def list_alerts():
    db = SessionLocal()
    try:
        alerts = db.query(Alert).order_by(desc(Alert.created_at)).all()
        unread_count = db.query(Alert).filter_by(is_read=False).count()
        critical_count = db.query(Alert).filter_by(severity="CRITICAL", is_read=False).count()

        return jsonify({
            "success": True,
            "total": len(alerts),
            "unread_count": unread_count,
            "critical_count": critical_count,
            "alerts": [a.to_dict() for a in alerts]
        })
    finally:
        db.close()

@alerts_bp.route("/<int:alert_id>/read", methods=["PUT"])
def mark_alert_read(alert_id):
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter_by(id=alert_id).first()
        if not alert:
            return jsonify({"success": False, "error": "Alert not found"}), 404

        alert.is_read = True
        db.commit()
        return jsonify({"success": True, "alert": alert.to_dict()})
    finally:
        db.close()

@alerts_bp.route("/read-all", methods=["PUT"])
def mark_all_read():
    db = SessionLocal()
    try:
        db.query(Alert).filter_by(is_read=False).update({"is_read": True})
        db.commit()
        return jsonify({"success": True, "message": "All alerts marked as read"})
    finally:
        db.close()
