import io
import pandas as pd
from datetime import datetime
from backend.models import EnergyConsumption, WaterConsumption, OccupancyData, WeatherData, Building
from backend.database import SessionLocal

REQUIRED_COLUMNS = ["timestamp", "building_id", "electricity_kwh", "water_liters", "occupancy", "temperature", "humidity"]

def validate_and_process_csv(file_stream_or_path):
    """
    Validates CSV headers, cleans rows, checks for missing values,
    and inserts records into the database.
    """
    if isinstance(file_stream_or_path, (str, bytes)):
        df = pd.read_csv(io.StringIO(file_stream_or_path) if isinstance(file_stream_or_path, str) else io.BytesIO(file_stream_or_path))
    else:
        df = pd.read_csv(file_stream_or_path)

    # 1. Header Validation
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return {
            "success": False,
            "error": f"Missing required CSV columns: {', '.join(missing_cols)}",
            "required_columns": REQUIRED_COLUMNS,
            "found_columns": list(df.columns)
        }

    # 2. Data Cleaning & Validation
    initial_rows = len(df)
    missing_val_count = df[REQUIRED_COLUMNS].isna().sum().to_dict()
    
    # Impute or drop bad rows
    df["electricity_kwh"] = pd.to_numeric(df["electricity_kwh"], errors="coerce").fillna(0.0)
    df["water_liters"] = pd.to_numeric(df["water_liters"], errors="coerce").fillna(0.0)
    df["occupancy"] = pd.to_numeric(df["occupancy"], errors="coerce").fillna(0).astype(int)
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce").fillna(28.0)
    df["humidity"] = pd.to_numeric(df["humidity"], errors="coerce").fillna(60.0)
    
    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp", "building_id"])
    
    processed_rows = len(df)
    
    # 3. Save into Database
    db = SessionLocal()
    saved_count = 0
    anomalies_detected = 0

    try:
        from backend.ai.anomaly_detection import AnomalyDetector
        detector = AnomalyDetector()

        for _, row in df.iterrows():
            ts = row["timestamp"].to_pydatetime()
            b_id = str(row["building_id"]).strip()
            
            # Check building exists or create fallback
            bldg = db.query(Building).filter_by(id=b_id).first()
            if not bldg:
                bldg = Building(
                    id=b_id,
                    name=f"Building {b_id}",
                    building_type="Academic",
                    status="normal"
                )
                db.add(bldg)
                db.commit()

            e_rec = EnergyConsumption(
                building_id=b_id,
                timestamp=ts,
                kwh=float(row["electricity_kwh"]),
                peak_demand_kw=float(row["electricity_kwh"]) * 1.12,
                source="csv_upload"
            )
            w_rec = WaterConsumption(
                building_id=b_id,
                timestamp=ts,
                liters=float(row["water_liters"]),
                flow_rate_lpm=float(row["water_liters"]) / 60.0,
                source="csv_upload"
            )
            occ_rec = OccupancyData(
                building_id=b_id,
                timestamp=ts,
                occupancy_count=int(row["occupancy"]),
                capacity_percentage=min(100.0, round((int(row["occupancy"]) / max(1, bldg.capacity or 500)) * 100.0, 1))
            )
            weath_rec = WeatherData(
                timestamp=ts,
                temperature=float(row["temperature"]),
                humidity=float(row["humidity"]),
                weather_condition="Monitored"
            )

            db.add(e_rec)
            db.add(w_rec)
            db.add(occ_rec)
            db.add(weath_rec)
            saved_count += 1

            # Quick anomaly check
            check = detector.detect_single(
                bldg.building_type, row["electricity_kwh"], row["occupancy"],
                row["temperature"], row["humidity"], ts.hour, ts.weekday()
            )
            if check["is_anomaly"]:
                anomalies_detected += 1

        db.commit()

        return {
            "success": True,
            "total_rows": initial_rows,
            "processed_rows": processed_rows,
            "records_inserted": saved_count,
            "missing_values_imputed": missing_val_count,
            "anomalies_flagged": anomalies_detected,
            "preview": df.head(5).to_dict(orient="records")
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        db.close()
