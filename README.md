# EcoCampus AI
### AI-Powered Predictive Campus Resource Optimization System

> **Tagline:** *“From detecting wastage to predicting its impact and simulating the best corrective action.”*

---

## 🌿 Project Overview

**EcoCampus AI** is an explainable AI decision-support platform designed for colleges, universities, and large academic institutions. It continuously ingests multi-factor campus telemetry (electricity, water, occupancy, timetable schedules, and meteorological data), detects abnormal consumption patterns, forecasts future resource demands, explains the underlying thermodynamic and human drivers, generates actionable recommendations, simulates "what-if" corrective scenarios before implementation, and measures sustainability impact aligned with green building standards (GRIHA).

---

## 🏛️ System Architecture

```
                    ┌─────────────────────────┐
                    │       Campus Data       │
                    │ Electricity  │  Water   │
                    │ Occupancy    │  Weather │
                    │ Timetable    │  Sensors │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ MySQL Database (InnoDB) │
                    │   (SQLite Auto-fallback)│
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Data Processing Engine  │
                    │     Pandas & NumPy      │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
  │  Anomaly     │        │ Consumption  │        │ Contextual   │
  │  Detection   │        │ Prediction   │        │ Analysis     │
  │IsolationForest        │ RandomForest │        │ Weather/Occ  │
  └──────┬───────┘        └──────┬───────┘        └──────┬───────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │   AI Decision Engine    │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   Recommendations       What-If Simulator       Explainable AI
  Actionable advice      Multi-scenario ROI      Factor Weights
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────────┐
                    │  Sustainability Portal  │
                    │     Score: 85 / 100     │
                    └─────────────────────────┘
```

---

## 🔄 The 8-Stage Closed-Loop AI Workflow

1. **DATA INGESTION**: Collects sub-metered electricity (kWh), water flow (L), occupancy headcounts, and ambient temperatures across 8 campus facilities.
2. **ANOMALY DETECTION**: Scikit-learn `IsolationForest` combined with dynamic university baselines identifies abnormal surges and leaks.
3. **CONSUMPTION PREDICTION**: Scikit-learn `RandomForestRegressor` forecasts next 24-hour and 7-day demand loads and avoidable waste.
4. **EXPLAINABLE AI (XAI)**: Deconstructs detections into transparent factor contributions (e.g., Temperature 42%, Occupancy 28%, AC Chiller load 18%).
5. **AI RECOMMENDATION**: Synthesizes anomalies into prioritized corrective interventions with estimated kWh, ₹, and CO₂ savings.
6. **WHAT-IF SIMULATION**: Allows administrators to adjust variables (AC hours, setback temperatures, lighting schedules) and test the exact consequences before implementation.
7. **MULTI-SCENARIO OPTIMIZATION**: Evaluates Scenario A vs B vs C and highlights the **BEST SCENARIO** yielding maximum annual ROI.
8. **SUSTAINABILITY IMPACT**: Quantifies avoided carbon emissions and updates the 5-component Campus Sustainability Index (85/100, Tier A+).

---

## 💻 Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript ES6+, Chart.js, Lucide Icons, Glassmorphism UI |
| **Backend** | Python 3.14+, Flask REST API, Flask-CORS, python-dotenv |
| **AI / ML** | Scikit-learn (`IsolationForest`, `RandomForestRegressor`), Pandas, NumPy |
| **Database** | MySQL 8.0 / MariaDB (InnoDB) with seamless SQLite fallback |
| **Security** | Bcrypt password hashing, PyJWT tokens, Role-Based Access Control |
| **Reporting**| ReportLab (Automated PDF Generation), CSV Data Exporter |

---

## 🏢 Campus Buildings Included

| Code | Building Name | Category | Area (sq ft) | Capacity | Baseline Status |
|---|---|---|---|---|---|
| `BLK-ADMIN` | Administrative Block | Administrative | 25,000 | 250 | Normal 🟢 |
| `BLK-A` | Academic Block A | Academic | 45,000 | 800 | Warning 🟡 (+39% Surge) |
| `BLK-B` | Academic Block B | Academic | 40,000 | 750 | Warning 🟡 (+34% Water Leak) |
| `LIB-MAIN` | Central Library | Academic | 30,000 | 500 | Normal 🟢 |
| `LAB-COMP` | Laboratory Complex | Academic | 35,000 | 400 | Critical 🔴 (+52% Off-hours) |
| `HOSTEL-A` | Hostel Block A | Residential | 50,000 | 600 | Normal 🟢 |
| `HOSTEL-B` | Hostel Block B | Residential | 48,000 | 550 | Normal 🟢 |
| `CAFE-CTR` | Central Cafeteria | Facility | 18,000 | 350 | Normal 🟢 |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed
- MySQL / MariaDB (e.g. XAMPP) or run directly with built-in SQLite fallback

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python -m backend.data.generator
```

### 4. Train Scikit-learn ML Models
```bash
python -m backend.ai.train_models
```

### 5. Launch Application
Double-click `run.bat` or run:
```bash
python -m backend.app
```
Then open your browser at **[http://localhost:5000](http://localhost:5000)**.

---

## 🔑 Sample Authentication Credentials

| Role | Email | Password | Access Level |
|---|---|---|---|
| **Facility Director (Admin)** | `admin@ecocampus.ai` | `Admin@123` | Full campus administration, simulations, CSV ingestion, report generation |
| **Sustainability Officer** | `manager@ecocampus.ai` | `Manager@123` | Assigned buildings monitoring (`BLK-A`, `BLK-B`, `LAB-COMP`), recommendations, simulator |

---

## 🧪 Automated Testing

EcoCampus AI includes an automated test suite verifying database connectivity, authentication, API routes, machine learning anomaly detection, regression forecasting, Explainable AI factor weights, What-If simulation math, and ReportLab PDF compilation:

```bash
python -m unittest tests/test_ecocampus.py
```

---

## 🎯 10-Step Hackathon Demo Scenario

Follow this live demonstration sequence during evaluations or presentations:

1. **Step 1 - Landing Page**: Showcase the hero section, closed-loop AI flowchart, and click **[Explore Live Dashboard]**.
2. **Step 2 - Live Dashboard**: View the 6 animated KPI cards (Electricity: 1,248 kWh/day, Active Anomalies: 3, Sustainability Score: 85/100).
3. **Step 3 - Interactive Campus Map**: Click on **Academic Block A** or **Laboratory Complex** on the SVG map to open real-time sub-meter telemetry.
4. **Step 4 - AI Anomaly Detection**: Navigate to **Anomalies & XAI**. Point out the +39% electricity anomaly detected in Block A at 10:42 AM.
5. **Step 5 - Explainable AI**: Click **[WHY DID AI DETECT THIS? (Explain Prediction)]**. Demonstrate the transparent factor breakdown (Temperature 42%, Occupancy Surge 28%, AC Chiller load 18%).
6. **Step 6 - AI Recommendations**: Navigate to **AI Recommendations**. Review the generated advice: *“Adjust AC chiller setpoint to 24.5°C and reduce compressor run-time by 1.0 hr/day in Academic Block A”*.
7. **Step 7 - What-If Decision Simulator**: Click **[Simulate Action]**. Move the duration slider to 1.5 hours. Click **[RUN SIMULATION]** and observe the BEFORE vs AFTER 24-hour demand curve.
8. **Step 8 - Multi-Scenario Optimization**: View the Scenario Comparison matrix. Point out how the AI automatically evaluates Scenario A, B, and C and highlights the **BEST SCENARIO** yielding ₹4.2 Lakhs in annual cost avoidance.
9. **Step 9 - EcoAI Assistant Chatbot**: Open the floating assistant at the bottom right. Ask: *“Which building wastes the most electricity?”* and *“How much can we save by reducing AC usage?”* to demonstrate live database lookups.
10. **Step 10 - Reports & Audit**: Navigate to **Reports & Audit**, click **[Generate PDF Report]**, and download the certified ReportLab PDF audit document.

---

## 🔒 Security & Architecture Integrity

- **Decision-Support Guardrails**: EcoCampus AI clearly records operational decisions without claiming unverified physical hardware actuation unless an authenticated IoT gateway integration is active.
- **Data Protection**: Sensitive credentials and JWT secrets are stored in `.env`.
- **SQL Injection Prevention**: All queries utilize SQLAlchemy ORM parameterized queries.
- **Production Resilience**: Multi-tiered database fallback (MySQL → SQLite) ensures zero downtime during presentations.
