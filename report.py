from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from careflow.analytics import department_metrics, overall_metrics, journey_metrics

def build_pdf_report(data):
    flow, journeys = data["flow"], data["journeys"]
    overall = overall_metrics(flow)
    jm = journey_metrics(journeys)
    dept = department_metrics(flow)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm,
                            leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("CareFlow", styles["Title"]),
        Paragraph("Hospital Operations & Patient Flow Analytics Report", styles["Heading2"]),
        Spacer(1, 8),
        Paragraph("Executive Summary", styles["Heading1"]),
        Paragraph(
            f"The analysis covers {overall['observations']} department-level observations "
            f"across {overall['departments']} departments. The overall mean recorded waiting "
            f"time is {overall['avg_wait']:.2f} minutes. Journey-summary records are reported "
            f"separately because their patient identifier format differs from the station-log data.",
            styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("Key Performance Indicators", styles["Heading1"]),
    ]
    kpi_data = [
        ["Metric", "Value"],
        ["Department observations", str(overall["observations"])],
        ["Average waiting time", f"{overall['avg_wait']:.2f} min"],
        ["Median waiting time", f"{overall['median_wait']:.2f} min"],
        ["Average service time", f"{overall['avg_service']:.2f} min"],
        ["Average queue length", f"{overall['avg_queue']:.2f}"],
        ["Journey records (separate table)", str(jm["count"])],
        ["Average journey duration", f"{jm['mean']:.2f} min" if jm["count"] else "N/A"],
    ]
    t = Table(kpi_data, colWidths=[90*mm, 70*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#183153")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story += [t, Spacer(1, 10), Paragraph("Department Performance", styles["Heading1"])]
    table_data = [["Department", "Records", "Avg wait (min)", "Avg service (min)", "Avg queue"]]
    for _, row in dept.iterrows():
        table_data.append([
            str(row["Department"]), str(int(row["Observations"])),
            f"{row['Avg_Wait']:.2f}", f"{row['Avg_Service']:.2f}", f"{row['Avg_Queue']:.2f}"
        ])
    t2 = Table(table_data, repeatRows=1, colWidths=[42*mm, 22*mm, 32*mm, 34*mm, 25*mm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#183153")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story += [t2, Spacer(1, 10),
              Paragraph("Interpretation and Limitations", styles["Heading1"]),
              Paragraph(
                  "These results describe the supplied dataset and should not be treated as "
                  "proof of causation or as guaranteed outcomes of operational changes. "
                  "Capacity scenarios are sensitivity illustrations, not validated forecasts. "
                  "The dataset is operational and does not support clinical diagnosis or treatment.",
                  styles["BodyText"])]
    doc.build(story)
    buffer.seek(0)
    return buffer
