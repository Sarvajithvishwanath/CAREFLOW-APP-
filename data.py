from pathlib import Path
import pandas as pd

REQUIRED_FLOW_COLUMNS = [
    "Observation ID", "Patient ID", "Visit Date", "Department",
    "Arrival or Queue Entry Time", "Service Start Time", "Service End Time",
    "Waiting Time Min", "Service Time Min", "Queue Length on Arrival",
    "Service Type", "Visit Status", "Total Journey Time Min"
]

def _normalise_time(series):
    return pd.to_datetime(series.astype(str), format="%H:%M", errors="coerce")

def load_workbook(file_or_path):
    """Load the supplied HMIS workbook while preserving its separate data tables."""
    xls = pd.ExcelFile(file_or_path)
    required_sheets = ["Patient Flow Data", "Queue Summary",
                       "Directed Graph Edges", "Journey Summary"]
    missing = [s for s in required_sheets if s not in xls.sheet_names]
    if missing:
        raise ValueError("Workbook is missing required sheet(s): " + ", ".join(missing))

    flow = pd.read_excel(xls, "Patient Flow Data")
    queue = pd.read_excel(xls, "Queue Summary")
    edges = pd.read_excel(xls, "Directed Graph Edges")
    journeys = pd.read_excel(xls, "Journey Summary")

    missing_cols = [c for c in REQUIRED_FLOW_COLUMNS if c not in flow.columns]
    if missing_cols:
        raise ValueError("Patient Flow Data is missing columns: " + ", ".join(missing_cols))

    flow["Visit Date"] = pd.to_datetime(flow["Visit Date"], errors="coerce")
    for c in ["Waiting Time Min", "Service Time Min",
              "Queue Length on Arrival", "Total Journey Time Min"]:
        flow[c] = pd.to_numeric(flow[c], errors="coerce")

    journeys["Visit Date"] = pd.to_datetime(journeys["Visit Date"], errors="coerce")
    journeys["Total Journey Time Min"] = pd.to_numeric(
        journeys["Total Journey Time Min"], errors="coerce"
    )
    queue["Avg Waiting Time Min"] = pd.to_numeric(queue["Avg Waiting Time Min"], errors="coerce")
    queue["Median Waiting Time Min"] = pd.to_numeric(queue["Median Waiting Time Min"], errors="coerce")
    queue["Avg Service Time Min"] = pd.to_numeric(queue["Avg Service Time Min"], errors="coerce")
    queue["Avg Queue Length"] = pd.to_numeric(queue["Avg Queue Length"], errors="coerce")
    edges["Observed Transitions"] = pd.to_numeric(edges["Observed Transitions"], errors="coerce")
    edges["Avg Transition Gap Min"] = pd.to_numeric(edges["Avg Transition Gap Min"], errors="coerce")

    # The supplied workbook has different ID formats in Patient Flow Data and
    # Journey Summary. Keep the tables separate unless the source owner confirms a mapping.
    return {"flow": flow, "queue": queue, "edges": edges, "journeys": journeys,
            "sheets": xls.sheet_names}

def validate_data(data):
    flow = data["flow"]
    issues = []
    if flow["Observation ID"].duplicated().any():
        issues.append("Duplicate Observation IDs were found.")
    if flow["Patient ID"].isna().any():
        issues.append("Some patient identifiers are missing.")
    if flow["Visit Date"].isna().any():
        issues.append("Some visit dates could not be parsed.")
    for col in ["Waiting Time Min", "Service Time Min", "Queue Length on Arrival"]:
        if (flow[col] < 0).any():
            issues.append(f"Negative values found in {col}.")
    if flow["Patient ID"].astype(str).str.startswith("SMS-P").any():
        issues.append("Patient ID formats should be reviewed before linking datasets.")
    return issues
