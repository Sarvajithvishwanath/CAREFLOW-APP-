import numpy as np
import pandas as pd

def simulate_single_server(arrival_minutes, service_minutes, priorities=None):
    """
    Non-preemptive single-server queue simulation.
    Lower numeric priority means higher priority.
    If priorities is None, jobs are served FCFS.
    Returns per-job simulated waiting and completion times.
    """
    arrivals = np.asarray(arrival_minutes, dtype=float)
    services = np.asarray(service_minutes, dtype=float)
    if len(arrivals) != len(services):
        raise ValueError("Arrival and service arrays must have equal length.")
    if np.any(~np.isfinite(arrivals)) or np.any(~np.isfinite(services)):
        raise ValueError("Arrival and service values must be finite.")
    if np.any(services < 0):
        raise ValueError("Service times cannot be negative.")

    n = len(arrivals)
    if priorities is None:
        priorities = np.ones(n, dtype=int)
        use_priority = False
    else:
        priorities = np.asarray(priorities, dtype=int)
        if len(priorities) != n:
            raise ValueError("Priority array must match the number of jobs.")
        use_priority = True

    # Stable sort by arrival; ties preserve original row order.
    arrival_order = sorted(range(n), key=lambda i: (arrivals[i], i))
    pending = []
    cursor = 0
    clock = 0.0
    results = {}

    while cursor < n or pending:
        if not pending and cursor < n:
            clock = max(clock, arrivals[arrival_order[cursor]])
        while cursor < n and arrivals[arrival_order[cursor]] <= clock:
            idx = arrival_order[cursor]
            pending.append(idx)
            cursor += 1

        if not pending:
            continue

        if use_priority:
            # Priority first; then earlier arrival; then original row order.
            chosen = min(pending, key=lambda i: (priorities[i], arrivals[i], i))
        else:
            chosen = min(pending, key=lambda i: (arrivals[i], i))
        pending.remove(chosen)

        start = max(clock, arrivals[chosen])
        wait = start - arrivals[chosen]
        finish = start + services[chosen]
        results[chosen] = (wait, finish)
        clock = finish

    ordered = pd.DataFrame({
        "Job": np.arange(1, n + 1),
        "Arrival": arrivals,
        "Service": services,
        "Priority (synthetic)": priorities,
        "Simulated Wait": [results[i][0] for i in range(n)],
        "Completion": [results[i][1] for i in range(n)]
    })
    return ordered


def compare_queue_policies(flow, department, seed=42):
    """
    Compare FCFS with a synthetic priority policy using observed arrival/service
    durations. Each visit date is simulated independently. Priority values are
    randomly assigned for demonstration only; they are not clinical priorities.
    """
    df = flow[flow["Department"] == department].copy()
    df["Visit Date"] = pd.to_datetime(df["Visit Date"], errors="coerce").dt.date
    df["Arrival Clock"] = pd.to_datetime(
        df["Arrival or Queue Entry Time"].astype(str), format="%H:%M", errors="coerce"
    )
    df["Service Numeric"] = pd.to_numeric(df["Service Time Min"], errors="coerce")
    df = df.dropna(subset=["Visit Date", "Arrival Clock", "Service Numeric"])
    if len(df) < 2:
        return None, None

    rng = np.random.default_rng(seed)
    fcfs_parts, priority_parts = [], []
    for _, day_df in df.groupby("Visit Date", sort=True):
        day_df = day_df.sort_values("Arrival Clock", kind="stable")
        arrivals = (
            day_df["Arrival Clock"].dt.hour.to_numpy() * 60
            + day_df["Arrival Clock"].dt.minute.to_numpy()
        ).astype(float)
        services = day_df["Service Numeric"].to_numpy(dtype=float)
        synthetic_priorities = rng.integers(1, 4, size=len(day_df))

        fcfs_day = simulate_single_server(arrivals, services)
        priority_day = simulate_single_server(arrivals, services, synthetic_priorities)
        fcfs_day["Visit Date"] = str(day_df["Visit Date"].iloc[0])
        priority_day["Visit Date"] = str(day_df["Visit Date"].iloc[0])
        fcfs_parts.append(fcfs_day)
        priority_parts.append(priority_day)

    return pd.concat(fcfs_parts, ignore_index=True), pd.concat(priority_parts, ignore_index=True)
