# EcoCampus AI

**AI-Powered Predictive Campus Resource Optimization System**

> From detecting wastage to predicting its impact and simulating the best corrective action.

EcoCampus AI is a campus resource-management prototype designed to help institutions understand electricity and water usage, identify unusual consumption, predict future demand, explain potential causes, compare corrective actions, and estimate sustainability impact.

This README describes the planned software and hardware integration. Features marked as planned or prototype must not be represented as production-validated AI or live sensor integration until they have been implemented and tested.

## 1. Project objectives

- Collect campus resource data from uploaded files, demo data, and (when connected) IoT sensors.
- Monitor electricity and water consumption by building and time period.
- Detect readings that differ from expected usage patterns.
- Forecast future consumption from available historical data.
- Explain model outputs using transparent factors and baseline comparisons.
- Recommend potential resource-saving actions.
- Simulate “what-if” scenarios before an action is implemented.
- Report estimated cost savings, resource savings, and environmental impact.
- Scale the data model from one building to a campus and potentially multiple campuses.

## 2. Core workflow

```text
CSV / Demo Data / IoT Sensors
              |
              v
        Flask REST API
              |
              v
       Data validation
       Pandas / NumPy
              |
              v
          MySQL
              |
              v
       Python AI services
       |       |       |
       v       v       v
    Anomaly Forecast Explain
       \       |       /
        v      v      v
       Recommendations
              |
              v
       What-if simulation
              |
              v
     Sustainability metrics
              |
              v
      JavaScript dashboard
```

## 3. Technology stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | HTML5, CSS3, JavaScript | Responsive user interface |
| Charts | Chart.js or equivalent | Consumption trends and comparisons |
| Backend | Python, Flask | REST APIs and application logic |
| Data processing | Pandas, NumPy | Validation, cleaning, and feature engineering |
| Machine learning | Scikit-learn | Prototype anomaly detection and forecasting |
| Database | MySQL | Buildings, readings, results, and reports |
| IoT controller | ESP32 (planned hardware integration) | Reads supported sensors and transmits readings over Wi-Fi |
| PDF reports | ReportLab (optional) | Generate downloadable reports |

## 4. Main modules

1. **Dashboard** — resource overview, trends, recent alerts, and recommendations.
2. **Data management** — CSV upload, preview, validation, and data quality feedback.
3. **Energy monitoring** — electricity readings, time-series charts, and building comparisons.
4. **Water monitoring** — water usage trends and possible unusual-flow alerts.
5. **Building management** — building-specific resource metrics and status.
6. **Anomaly detection** — flags readings that differ from a baseline or model.
7. **Consumption prediction** — forecasts future usage when sufficient historical data exists.
8. **Explainable AI** — presents observed factors, baseline differences, and limitations.
9. **Recommendations** — proposes possible resource-saving actions.
10. **What-if simulator** — compares baseline and hypothetical resource use.
11. **Sustainability dashboard** — summarizes resource efficiency and estimated impact.
12. **Alerts and reports** — displays events and exports analysis.
13. **Hardware integration** — accepts ESP32 sensor data once the device and endpoint are configured.

## 5. Repository structure

Adapt this structure to the files that actually exist in your repository.

```text
EcoCampus-AI/
├── frontend/
│   ├── index.html
│   ├── css/
│   │   ├── style.css
│   │   └── responsive.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       ├── dashboard.js
│       ├── energy.js
│       ├── water.js
│       ├── anomalies.js
│       ├── predictions.js
│       ├── recommendations.js
│       ├── simulator.js
│       └── sustainability.js
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── database.py
│   ├── routes/
│   ├── services/
│   ├── ai/
│   │   ├── anomaly_detection.py
│   │   ├── consumption_prediction.py
│   │   ├── recommendation_engine.py
│   │   ├── decision_engine.py
│   │   ├── explainability.py
│   │   └── simulator.py
│   └── data/
│       ├── generator.py
│       └── preprocessing.py
├── database/
│   ├── schema.sql
│   └── seed.sql
├── models/
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

Do not create empty placeholder modules and claim they work. Document the actual files and features in the repository as they are implemented.

## 6. Prerequisites

Install the following:

- Python 3.10 or newer (use a version supported by the installed packages).
- pip.
- MySQL Server.
- A modern browser.
- Optional: Visual Studio Code.
- Optional for hardware integration: ESP32 development board, compatible sensors, and Arduino IDE.

Check Python and pip:

```bash
python --version
python -m pip --version
```

## 7. Backend setup (Windows)

Open Command Prompt or PowerShell in the project directory.

```powershell
cd backend
python -m venv venv
```

Activate the environment in **PowerShell**:

```powershell
.\venv\Scripts\Activate.ps1
```

Or activate it in **Command Prompt (CMD)**:

```cmd
venv\Scripts\activate.bat
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install Flask flask-cors pandas numpy scikit-learn pymysql python-dotenv
```

If the project includes SQLAlchemy models, install it too:

```bash
pip install Flask-SQLAlchemy
```

Save installed dependencies:

```bash
pip freeze > requirements.txt
```

If a maintained `requirements.txt` already exists, prefer:

```bash
pip install -r requirements.txt
```

## 8. Configure MySQL

Start MySQL Server, then create the database using MySQL Workbench or the MySQL command-line client:

```sql
CREATE DATABASE ecocampus_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Create a local `.env` file in the backend directory. Example:

```dotenv
FLASK_DEBUG=1
SECRET_KEY=replace-with-a-long-random-secret
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=ecocampus_ai
```

Use your actual local MySQL credentials. Do not commit `.env` to Git or place database passwords in frontend JavaScript. The `.env.example` file should contain placeholders only.

Create the schema using the SQL file if it exists:

```bash
mysql -u your_mysql_user -p ecocampus_ai < ../database/schema.sql
```

The tables and schema must match the actual backend models. If `schema.sql` has not yet been created, create it before running this command.

## 9. Run the Flask backend

From the `backend` directory, with the virtual environment active:

```bash
python app.py
```

If the Flask application is configured for the default port, open:

- `http://127.0.0.1:5000`
- `http://localhost:5000`

If `app.py` does not start the server itself, and it exposes a Flask instance named `app`, use:

```bash
python -m flask --app app run --debug
```

The backend must provide a health endpoint (recommended: `GET /api/health`) so that you can verify the API and database status. Only document endpoints that actually exist in the implementation.

## 10. Run the frontend

For a plain HTML/CSS/JavaScript frontend, open a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open:

`http://localhost:5500`

The frontend API base URL should be configurable in one place, for example in `frontend/js/api.js`:

```javascript
const API_BASE_URL = "http://localhost:5000";
```

Use the actual API endpoints implemented by Flask. If the frontend is served on port 5500 and Flask on port 5000, configure Flask CORS to allow the frontend origin during local development.

If the frontend is instead built with a framework such as Vite or Next.js, use that project's existing start command rather than `python -m http.server`.

## 11. Demo mode and data

Demo mode allows the prototype to be shown before physical sensors are installed. It should use clearly labelled synthetic data and should never be confused with live sensor measurements.

A useful CSV format is:

```csv
timestamp,building_id,electricity_kwh,water_liters,occupancy,temperature,humidity
2026-10-01 09:00:00,BLK-A,124.5,820,430,31.2,68
```

Recommended data checks:

- Required columns are present.
- Timestamps are parseable and consistently interpreted.
- Numeric values are valid and within plausible ranges.
- Missing values and duplicates are reported.
- Units are recorded consistently.
- Uploaded rows are associated with a valid building.

If generating demo readings, label them `DEMO` in the interface and in stored records.

## 12. AI/ML implementation notes

### Anomaly detection

A prototype can use a statistical baseline or Scikit-learn `IsolationForest`. The model should be trained or calibrated with appropriate data and tested on known normal and abnormal examples.

### Consumption forecasting

A model such as `RandomForestRegressor` can be evaluated for short-term predictions if there is enough representative historical data. Use a time-aware train/test split and report metrics such as MAE and RMSE.

### Explainability

Show the observed reading, expected baseline, deviation, and relevant contextual variables. Do not label a heuristic contribution as a validated causal explanation. A high model score is not automatically a calibrated probability.

### Recommendations

Start with transparent, rule-based recommendations connected to observed patterns. Clearly distinguish estimated savings from measured savings.

### What-if simulation

Compare a baseline with user-defined assumptions. Display the assumptions and formulas used. Simulation results are estimates, not proof that a physical intervention will achieve the same result.

### Sustainability calculations

Document the emission factors, energy prices, water prices, and score weights used. Keep these configurable and avoid presenting illustrative values as measured facts.

## 13. ESP32 and sensor integration (optional / future stage)

When hardware is available, the intended data path is:

```text
Compatible sensor(s) → ESP32 → Wi-Fi → Flask API → MySQL
                                              ↓
                                         AI services
                                              ↓
                                         Web dashboard
```

Suggested measurements:

- Electricity: a suitably rated energy meter with a supported interface.
- Water: a flow sensor compatible with the water system and ESP32 input requirements.
- Temperature/humidity: a compatible digital sensor such as DHT22.
- Occupancy: a suitable occupancy sensor, where permitted.

A hardware payload could look like this:

```json
{
  "device_id": "ESP32-BLK-A-01",
  "building_id": "BLK-A",
  "timestamp": "2026-10-10T09:00:00Z",
  "temperature_c": 31.2,
  "humidity_percent": 68,
  "water_flow_lpm": 3.4,
  "electricity_power_w": 620
}
```

This is an example payload, not a guarantee that the endpoint already exists. Implement and authenticate a dedicated ingestion endpoint before sending real readings. Validate device identity, timestamps, units, and ranges, and store sensor provenance.

**Electrical safety:** never connect mains voltage directly to an ESP32 or a breadboard. Use appropriately rated, isolated measurement equipment and have mains installation performed by a qualified person. Prototype first with low-voltage demonstration hardware. Ensure the water sensor and installation are suitable for the plumbing and electrical environment.

## 14. Testing checklist

- [ ] Flask starts successfully.
- [ ] MySQL connection succeeds.
- [ ] Frontend can reach the API.
- [ ] Invalid CSV files produce clear validation errors.
- [ ] Valid data is stored with the correct units and timestamps.
- [ ] Known normal readings are not repeatedly flagged as anomalies.
- [ ] Known abnormal readings can be detected in test data.
- [ ] Forecast performance is evaluated on held-out time periods.
- [ ] Recommendations explain their assumptions.
- [ ] Simulator results are reproducible for the same inputs.
- [ ] PDF/CSV exports open and contain the selected period.
- [ ] Demo data is clearly separated from real sensor data.
- [ ] API endpoints reject invalid or unauthorized requests.

## 15. Troubleshooting

**`python` is not recognized**

Install Python and enable “Add Python to PATH”, then reopen the terminal.

**`ModuleNotFoundError`**

Activate the project's virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

**Flask starts but the browser shows a 404**

The server may be running correctly while the requested route is not defined. Visit an implemented route or add a health endpoint.

**MySQL connection refused**

Confirm MySQL Server is running and check the host, port, username, password, and database name in `.env`.

**Frontend cannot call Flask**

Check the API base URL, Flask server status, CORS settings, and browser developer console.

**No sensor data appears**

Confirm the ESP32 is powered, connected to the correct Wi-Fi network, configured with the server address reachable from that network, and posting to a real ingestion endpoint. `localhost` on an ESP32 refers to the device itself, not the development computer.

## 16. Security and deployment

- Hash user passwords; never store plain-text passwords.
- Protect write endpoints with authentication and authorization.
- Validate and limit CSV upload size and content.
- Use parameterized SQL queries or a safe ORM.
- Keep secrets in environment variables.
- Use HTTPS and appropriate device authentication outside local development.
- Do not expose Flask debug mode in production.
- Restrict database network access and use a least-privilege database account.
- Log important operations without recording passwords or secrets.

## 17. Project status

Track implementation honestly:

- **Implemented:** list and test features available in the current repository.
- **Prototype:** features using simplified models, heuristics, or synthetic data.
- **Planned:** hardware integration, deployment, or models not yet implemented.

Do not claim real-time hardware, validated prediction accuracy, actual savings, or physical device control unless these have been demonstrated and measured.

## 18. Project vision

EcoCampus AI aims to help campuses make more informed resource decisions through monitoring, anomaly detection, forecasting, explanations, recommendations, and scenario simulation.

The long-term workflow is:

**Monitor → Detect → Predict → Explain → Recommend → Simulate → Measure Impact**

The initial prototype can operate with uploaded or simulated data and later expand to supported IoT hardware.
# ECO-CAMPUS
