# CareFlow – Hospital Operations & Patient Flow Optimisation

A Python + Streamlit academic prototype built around the supplied `DELIVERABLE 3 - HMIS DATA.xlsx`.

## Features
- HMIS Excel upload and basic data validation
- Executive KPIs and departmental performance dashboard
- Waiting-time, service-time and queue analysis
- Patient journey summary analysis
- Department hand-off / transition analysis
- FCFS versus synthetic-priority single-server queue simulation\n- Illustrative capacity sensitivity scenario
- Exploratory waiting-time regression model with holdout MAE and mean baseline
- CSV export and PDF management report

## Important data limitations
1. The `Patient Flow Data` and `Journey Summary` sheets use different patient-ID formats. This application deliberately does not join them.
2. The workbook does not provide a validated clinical priority field. Do not infer medical urgency from service type or queue length.
3. The queue-policy comparison is a simplified single-server simulation. Priority labels are randomly generated for demonstration only and are not clinical priorities. The what-if capacity control is a sensitivity illustration, not a guaranteed forecast.
4. The predictive model is exploratory. Report its holdout performance honestly; do not claim it works unless it beats the baseline and is validated on independent data.
5. This is an academic operations project, not a clinical diagnosis, treatment or triage tool.

## Setup

### 1. Create and activate a virtual environment
macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
```powershell
py -m venv .venv
.venv\Scripts\activate
```

### 2. Install packages
```bash
pip install -r requirements.txt
```

### 3. Run the application
```bash
streamlit run app.py
```

### 4. Upload the workbook
Upload `DELIVERABLE 3 - HMIS DATA.xlsx` in the sidebar.

## Suggested five-member division
1. Data loading, validation and patient-flow records (`careflow/data.py`)
2. Departmental analytics and KPI calculations (`careflow/analytics.py`)
3. Queue and what-if analysis (Queue & What-if page in `app.py`)
4. Predictive modelling (`careflow/model.py`)
5. Streamlit integration, PDF export and testing (`app.py`, `careflow/report.py`)

## Suggested project demonstration
1. Upload the supplied workbook.
2. Show the executive KPI dashboard.
3. Identify the department with the highest recorded average waiting time.
4. Explore department waiting-time distributions and hand-offs.
5. Show the journey summary separately.
6. Run the waiting-time model and compare its MAE with the baseline.
7. Demonstrate the capacity sensitivity control and explain its assumptions.
8. Export the PDF report.

## Folder structure
```text
CareFlow_Project/
├── app.py
├── requirements.txt
├── README.md
└── careflow/
    ├── __init__.py
    ├── data.py
    ├── analytics.py
    ├── model.py
    └── report.py
```
