"""
Clinical Report Generator (PDF)
Generates downloadable medical PDF reports containing patient demographics,
vital metrics, risk level, confidence percentage, top factors breakdown, and recommendations.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_report(
    patient_name: str,
    patient_email: str,
    vitals: dict,
    prediction: dict,
    report_id: str = "GLUCO-REP-001"
) -> bytes:
    """
    Generates a PDF bytes object formatted as an official clinical assessment report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#35607f")
    )
    subheader_style = ParagraphStyle(
        "SubHeaderStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#615e57")
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1a1c1a"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1a1c1a")
    )

    # 1. Header Banner
    story.append(Paragraph("Intelligent Diabetes Risk Predictor", header_style))
    story.append(Paragraph("Clinical Decision Support & Risk Assessment Report", subheader_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#35607f"), spaceAfter=15))

    # 2. Patient & Assessment Meta Table
    risk_level = prediction.get("risk_level", "Low")
    risk_color = colors.HexColor("#ba1a1a") if risk_level == "High" else colors.HexColor("#1b5e20")
    confidence = prediction.get("confidence", 0.0)

    now_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")
    meta_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {patient_name}", body_style),
            Paragraph(f"<b>Report ID:</b> {report_id}", body_style)
        ],
        [
            Paragraph(f"<b>Patient Email:</b> {patient_email}", body_style),
            Paragraph(f"<b>Assessment Date:</b> {now_str}", body_style)
        ],
        [
            Paragraph(f"<b>Model Used:</b> {prediction.get('model_used', 'Decision Tree')}", body_style),
            Paragraph(f"<b>Status:</b> Completed & Verified", body_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[260, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f3f1")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # 3. Overall Risk Result Banner
    risk_box_data = [
        [
            Paragraph(f"<font size=14><b>Calculated Risk Level: {risk_level.upper()} RISK</b></font><br/>"
                      f"<font size=10>Model Confidence Score: <b>{confidence:.1f}%</b></font>",
                      ParagraphStyle("RiskBox", parent=body_style, textColor=risk_color, alignment=1))
        ]
    ]
    risk_table = Table(risk_box_data, colWidths=[530])
    risk_bg = colors.HexColor("#ffdad6") if risk_level == "High" else colors.HexColor("#e8f5e9")
    risk_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), risk_bg),
        ("BOX", (0, 0), (-1, -1), 1.5, risk_color),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 15))

    # 4. Submitted Clinical Vitals Table
    story.append(Paragraph("1. Submitted Clinical Vitals", section_title))
    vitals_table_data = [
        ["Clinical Metric", "Recorded Value", "Standard Normal Range", "Status"],
        ["Plasma Glucose", f"{vitals.get('glucose', 0):.1f} mg/dL", "70 - 99 mg/dL", "Elevated" if vitals.get('glucose', 0) >= 100 else "Normal"],
        ["Body Mass Index (BMI)", f"{vitals.get('bmi', 0):.1f} kg/m²", "18.5 - 24.9 kg/m²", "High" if vitals.get('bmi', 0) >= 25 else "Normal"],
        ["Blood Pressure (Diastolic)", f"{vitals.get('blood_pressure', 0):.0f} mm Hg", "60 - 80 mm Hg", "Elevated" if vitals.get('blood_pressure', 0) >= 85 else "Normal"],
        ["Serum Insulin", f"{vitals.get('insulin', 0):.1f} μU/mL", "16 - 166 μU/mL", "Elevated" if vitals.get('insulin', 0) > 166 else "Normal"],
        ["Triceps Skin Thickness", f"{vitals.get('skin_thickness', 0):.1f} mm", "10 - 25 mm", "Normal"],
        ["Pregnancies", f"{int(vitals.get('pregnancies', 0))}", "0 - 2", "Recorded"],
        ["Diabetes Pedigree Function", f"{vitals.get('diabetes_pedigree_function', 0):.3f}", "< 0.500", "Elevated" if vitals.get('diabetes_pedigree_function', 0) >= 0.5 else "Normal"],
        ["Patient Age", f"{int(vitals.get('age', 0))} Years", "Adult", "Recorded"],
    ]
    vt = Table(vitals_table_data, colWidths=[180, 110, 130, 110])
    vt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#35607f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#faf9f6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f4f3f1")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2c7ce")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(vt)
    story.append(Spacer(1, 15))

    # 5. Top Contributing Risk Factors Breakdown
    story.append(Paragraph("2. Primary Contributing Risk Factors", section_title))
    top_factors = prediction.get("top_factors", [])
    factors_data = [["Rank", "Factor", "Recorded Value", "Relative Impact", "Clinical Status"]]
    for idx, f in enumerate(top_factors[:4], 1):
        factors_data.append([
            f"#{idx}",
            f.get("label", f.get("feature")),
            str(f.get("value")),
            f"{f.get('impact', 0):.1f}%",
            f.get("status", "Elevated")
        ])
    ft = Table(factors_data, colWidths=[40, 180, 110, 100, 100])
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f7999")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f4f3f1")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c2c7ce")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(ft)
    story.append(Spacer(1, 15))

    # 6. Personalized Clinical Recommendations
    story.append(Paragraph("3. Actionable Clinical Recommendations", section_title))
    recs = prediction.get("recommendations", [])
    for idx, r in enumerate(recs, 1):
        story.append(Paragraph(f"• <b>Recommendation {idx}:</b> {r}", body_style))
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#c2c7ce"), spaceAfter=10))
    disclaimer = ("<b>Disclaimer:</b> This report is generated by an artificial intelligence decision-support tool "
                  "(CS619 Final Project S26PROJECTA7FFD) and is intended for informational and educational purposes only. "
                  "It does not constitute formal medical diagnosis or replace consultation with a certified physician.")
    story.append(Paragraph(disclaimer, ParagraphStyle("Disc", parent=body_style, fontSize=7, leading=9, textColor=colors.HexColor("#72787e"))))

    doc.build(story)
    return buffer.getvalue()
