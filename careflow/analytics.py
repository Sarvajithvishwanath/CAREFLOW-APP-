import numpy as np
import pandas as pd

def department_metrics(flow):
    return (flow.groupby("Department", dropna=False)
            .agg(Observations=("Observation ID", "count"),
                 Avg_Wait=("Waiting Time Min", "mean"),
                 Median_Wait=("Waiting Time Min", "median"),
                 Avg_Service=("Service Time Min", "mean"),
                 Avg_Queue=("Queue Length on Arrival", "mean"))
            .reset_index()
            .sort_values("Avg_Wait", ascending=False))

def overall_metrics(flow):
    return {
        "observations": int(flow["Observation ID"].count()),
        "departments": int(flow["Department"].nunique()),
        "avg_wait": float(flow["Waiting Time Min"].mean()),
        "median_wait": float(flow["Waiting Time Min"].median()),
        "avg_service": float(flow["Service Time Min"].mean()),
        "avg_queue": float(flow["Queue Length on Arrival"].mean()),
    }

def journey_metrics(journeys):
    valid = journeys["Total Journey Time Min"].dropna()
    if valid.empty:
        return {"count": 0, "mean": np.nan, "median": np.nan, "maximum": np.nan}
    return {"count": int(valid.count()), "mean": float(valid.mean()),
            "median": float(valid.median()), "maximum": float(valid.max())}

def hourly_profile(flow):
    tmp = flow.copy()
    tmp["Arrival Hour"] = pd.to_datetime(
        tmp["Arrival or Queue Entry Time"].astype(str), format="%H:%M", errors="coerce"
    ).dt.hour
    return tmp.groupby("Arrival Hour", dropna=True).size().reset_index(name="Observations")

def transition_summary(edges):
    return edges.sort_values("Avg Transition Gap Min", ascending=False)

def queue_scenario(flow, selected_department, capacity_factor=1.0):
    """Transparent sensitivity scenario, not a validated operational forecast."""
    subset = flow[flow["Department"] == selected_department]
    if subset.empty:
        return None
    base = float(subset["Waiting Time Min"].mean())
    # A deliberately simple sensitivity assumption: waiting varies inversely
    # with a user-selected service-capacity multiplier.
    factor = max(float(capacity_factor), 0.1)
    scenario = base / factor
    return {"department": selected_department, "baseline": base,
            "scenario": scenario, "change": base - scenario,
            "capacity_factor": factor}
