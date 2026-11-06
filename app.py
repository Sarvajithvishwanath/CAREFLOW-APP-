import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from careflow.data import load_workbook, validate_data
from careflow.analytics import (department_metrics, overall_metrics, journey_metrics,
                                hourly_profile, transition_summary, queue_scenario)
from careflow.model import train_wait_model
from careflow.report import build_pdf_report
from careflow.queue import compare_queue_policies

st.set_page_config(page_title="CareFlow | Hospital Operations Intelligence",
                   page_icon="🏥", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
.metric-card {padding: 12px; border: 1px solid #e5e7eb; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("CareFlow")
st.subheader("Intelligent Hospital Operations & Patient Flow Optimisation Platform")
st.caption("A Python-based analytics and decision-support prototype for hospital operations.")

with st.sidebar:
    st.header("Data source")
    uploaded = st.file_uploader("Upload another HMIS Excel workbook (optional)", type=["xlsx"])
    st.info("Default data: DELIVERABLE 3 - HMIS DATA.xlsx")
    st.caption("The app analyses anonymised operational records. Do not upload identifiable patient or clinical data.")

@st.cache_data(show_spinner=False)
def load_data(file_bytes):
    from io import BytesIO
    return load_workbook(BytesIO(file_bytes))

if uploaded is not None:
    workbook_bytes = uploaded.getvalue()
else:
    workbook_path = (Path(__file__).resolve().parent / "DELIVERABLE 3 - HMIS DATA.xlsx")
    if not workbook_path.exists():
        st.error("Default HMIS workbook not found in the GitHub repository.")
        st.stop()
    workbook_bytes = workbook_path.read_bytes()

flow = data["flow"].copy()
queue = data["queue"].copy()
edges = data["edges"].copy()
journeys = data["journeys"].copy()

flow = data["flow"].copy()
queue = data["queue"].copy()
edges = data["edges"].copy()
journeys = data["journeys"].copy()

issues = validate_data(data)
with st.expander("Data validation and governance", expanded=bool(issues)):
    if issues:
        for issue in issues:
            st.warning(issue)
    else:
        st.success("Basic structural checks passed.")
    st.write(f"Workbook sheets detected: {', '.join(data['sheets'])}")
    st.caption("Patient Flow Data and Journey Summary are kept separate because their patient ID formats differ. No cross-table patient matching is attempted.")

st.sidebar.header("Filters")
departments = sorted(flow["Department"].dropna().unique().tolist())
selected_depts = st.sidebar.multiselect("Departments", departments, default=departments)
filtered = flow[flow["Department"].isin(selected_depts)].copy()
if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

min_date = filtered["Visit Date"].min()
max_date = filtered["Visit Date"].max()
if pd.notna(min_date) and pd.notna(max_date):
    date_range = st.sidebar.date_input("Visit date range", value=(min_date.date(), max_date.date()))
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        filtered = filtered[filtered["Visit Date"].between(start, end)]

page = st.sidebar.radio("Navigate", [
    "Executive Dashboard", "Department Analysis", "Patient Journey",
    "Queue & What-if Analysis", "Waiting-Time Model", "Data Explorer"
])

if filtered.empty:
    st.warning("No data available for this date and department selection.")
    st.stop()

metrics = overall_metrics(filtered)

if page == "Executive Dashboard":
    st.header("Executive Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Department observations", f"{metrics['observations']:,}")
    c2.metric("Average waiting time", f"{metrics['avg_wait']:.2f} min")
    c3.metric("Average service time", f"{metrics['avg_service']:.2f} min")
    c4.metric("Average queue length", f"{metrics['avg_queue']:.2f}")

    dept = department_metrics(filtered)
    left, right = st.columns(2)
    with left:
        st.subheader("Average waiting time by department")
        fig = px.bar(dept, x="Department", y="Avg_Wait", color="Department",
                     labels={"Avg_Wait": "Average waiting time (minutes)"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Average service time by department")
        fig = px.bar(dept, x="Department", y="Avg_Service", color="Department",
                     labels={"Avg_Service": "Average service time (minutes)"})
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Department performance summary")
    st.dataframe(dept.rename(columns={
        "Avg_Wait": "Average waiting (min)", "Median_Wait": "Median waiting (min)",
        "Avg_Service": "Average service (min)", "Avg_Queue": "Average queue length"
    }), use_container_width=True, hide_index=True)

    st.subheader("Arrival pattern")
    hourly = hourly_profile(filtered)
    if not hourly.empty:
        fig = px.bar(hourly, x="Arrival Hour", y="Observations",
                     labels={"Arrival Hour": "Arrival hour", "Observations": "Records"})
        st.plotly_chart(fig, use_container_width=True)

elif page == "Department Analysis":
    st.header("Departmental Performance Analysis")
    dept = department_metrics(filtered)
    st.dataframe(dept, use_container_width=True, hide_index=True)
    st.subheader("Waiting time distribution")
    fig = px.box(filtered, x="Department", y="Waiting Time Min", color="Department")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Queue length versus waiting time")
    fig = px.scatter(filtered, x="Queue Length on Arrival", y="Waiting Time Min",
                     color="Department", hover_data=["Observation ID", "Service Type"])
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Association in this dataset does not establish that queue length causes waiting time.")

elif page == "Patient Journey":
    st.header("Patient Journey Analysis")
    jm = journey_metrics(journeys)
    a, b, c = st.columns(3)
    a.metric("Journey records", jm["count"])
    b.metric("Average journey duration", f"{jm['mean']:.2f} min" if jm["count"] else "N/A")
    c.metric("Median journey duration", f"{jm['median']:.2f} min" if jm["count"] else "N/A")
    st.info("Journey Summary is shown independently. Its patient ID format differs from Patient Flow Data; the app does not merge these records.")
    if not journeys.empty:
        fig = px.histogram(journeys, x="Total Journey Time Min", nbins=15,
                           title="Distribution of recorded total journey duration")
        st.plotly_chart(fig, use_container_width=True)
        daily = journeys.groupby("Visit Date", dropna=True)["Total Journey Time Min"].mean().reset_index()
        fig = px.line(daily, x="Visit Date", y="Total Journey Time Min", markers=True,
                      title="Average journey duration by visit date")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(journeys, use_container_width=True, hide_index=True)

    st.subheader("Department hand-offs")
    trans = transition_summary(edges)
    st.dataframe(trans, use_container_width=True, hide_index=True)
    if not trans.empty:
        fig = px.bar(trans, x="From Department", y="Avg Transition Gap Min",
                     color="To Department", title="Average transition gap between departments",
                     labels={"Avg Transition Gap Min": "Average transition gap (minutes)"})
        st.plotly_chart(fig, use_container_width=True)

elif page == "Queue & What-if Analysis":
    st.header("Queue Management and What-if Analysis")
    st.markdown("Compare recorded department waiting times and explore a simple capacity sensitivity scenario.")
    dept_names = sorted(filtered["Department"].dropna().unique().tolist())
    chosen = st.selectbox("Select department", dept_names)
    multiplier = st.slider("Illustrative service-capacity multiplier", 1.0, 2.0, 1.25, 0.05)
    result = queue_scenario(filtered, chosen, multiplier)
    if result:
        x, y, z = st.columns(3)
        x.metric("Recorded baseline average", f"{result['baseline']:.2f} min")
        y.metric("Illustrative scenario", f"{result['scenario']:.2f} min")
        z.metric("Modelled difference", f"{result['change']:.2f} min")
    st.warning("This is a simplified sensitivity illustration, not a validated queueing simulation or a promise of real-world savings. Actual impact depends on arrival patterns, staffing, service-time distributions and downstream capacity.")
    st.subheader("FCFS vs synthetic priority scheduling demonstration")
    st.caption("The simulation uses recorded arrival and service durations with a single-server assumption. Priority labels are randomly generated for demonstration; they are not clinical priorities.")
    if st.button("Run scheduling comparison"):
        fcfs, priority = compare_queue_policies(filtered, chosen)
        if fcfs is None:
            st.error("Not enough valid arrival and service records for this department.")
        else:
            comparison = pd.DataFrame([
                {"Policy": "FCFS", "Average simulated waiting (min)": fcfs["Simulated Wait"].mean()},
                {"Policy": "Synthetic priority", "Average simulated waiting (min)": priority["Simulated Wait"].mean()}
            ])
            st.dataframe(comparison, use_container_width=True, hide_index=True)
            fig = px.bar(comparison, x="Policy", y="Average simulated waiting (min)",
                         title="Illustrative single-server policy comparison")
            st.plotly_chart(fig, use_container_width=True)
            with st.expander("View simulated job-level results"):
                st.write("FCFS results")
                st.dataframe(fcfs, use_container_width=True, hide_index=True)
                st.write("Synthetic priority results")
                st.dataframe(priority, use_container_width=True, hide_index=True)
    st.warning("This is a simplified single-server simulation. The priority labels are synthetic and must never be interpreted as medical urgency or used to order actual patients. Real hospital deployment requires approved clinical governance, validated priority rules and realistic multi-server modelling.")
    st.subheader("Recorded department queue summary")
    st.dataframe(queue, use_container_width=True, hide_index=True)

elif page == "Waiting-Time Model":
    st.header("Exploratory Waiting-Time Prediction")
    st.write("A small regression model estimates recorded waiting time from operational fields. Results are evaluated against a simple mean-prediction baseline.")
    if st.button("Train and evaluate model", type="primary"):
        with st.spinner("Training model..."):
            result, error = train_wait_model(filtered)
        if error:
            st.error(error)
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Model MAE", f"{result['model_mae']:.2f} min")
            c2.metric("Baseline MAE", f"{result['baseline_mae']:.2f} min")
            c3.metric("Test observations", result["test_rows"])
            if result["model_mae"] < result["baseline_mae"]:
                st.success("The model outperformed the mean baseline on this holdout split.")
            else:
                st.warning("The model did not outperform the mean baseline. Do not present it as a successful predictor.")
            st.caption("This is an exploratory academic model on a limited dataset. Validate with more dates and independent data before operational use.")
    else:
        st.info("Select the button to train and evaluate the model.")

elif page == "Data Explorer":
    st.header("Data Explorer")
    st.subheader("Filtered patient flow observations")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
    st.download_button("Download filtered observations (CSV)",
                       filtered.to_csv(index=False).encode("utf-8"),
                       file_name="careflow_filtered_patient_flow.csv",
                       mime="text/csv")
    st.subheader("Department transition records")
    st.dataframe(edges, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Export management report")
pdf = build_pdf_report({"flow": filtered, "journeys": journeys, "queue": queue, "edges": edges})
st.download_button("Download CareFlow PDF report", data=pdf,
                   file_name="CareFlow_Operations_Report.pdf",
                   mime="application/pdf")
st.caption("CareFlow is an academic operational analytics prototype. It is not a clinical decision-support or patient-triage system.")
