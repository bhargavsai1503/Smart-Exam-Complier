"""
PDF Report Generation Module
Creates professional PDF report with analysis and charts
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
import matplotlib.pyplot as plt
import io

def generate_pdf_report(report, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a2332'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    story.append(Paragraph("SmartExam Compiler", title_style))
    story.append(Paragraph("AI-Driven Question Paper Analysis Report", styles['Heading3']))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Executive Summary", heading_style))
    summary_data = [
        ['Metric', 'Value', 'Status'],
        ['Total Questions', str(report['statistics']['total_questions']), '✓'],
        ['Total Marks (Calculated)', str(report['statistics']['total_marks_calculated']),
         '✓' if report['checks']['marks_validation']['status'] == 'PASS' else '✗'],
        ['Total Marks (Declared)', str(report['statistics']['total_marks_declared']), ''],
        ['Estimated Time', f"{report['statistics']['estimated_time_minutes']} min", ''],
        ['Declared Time', f"{report['statistics']['declared_time_minutes']} min", ''],
        ['Overall Quality Score', f"{report['crispness_score']}/100",
         '✓' if report['crispness_score'] >= 70 else '⚠']
    ]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2332')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Detailed Analysis", heading_style))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("1. Marks Validation", styles['Heading3']))
    marks_check = report['checks']['marks_validation']
    marks_text = f"Status: <b>{marks_check['status']}</b><br/>"
    marks_text += f"Message: {marks_check['message']}<br/>"
    marks_text += f"Difference: {marks_check['difference']} marks"
    story.append(Paragraph(marks_text, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("2. Time Estimation", styles['Heading3']))
    time_check = report['checks']['time_estimation']
    time_text = f"Status: <b>{time_check['status']}</b><br/>"
    time_text += f"Estimated: {time_check['estimated_time']} minutes<br/>"
    time_text += f"Declared: {time_check['declared_time']} minutes<br/>"
    time_text += f"Difference: {time_check['difference']} minutes"
    story.append(Paragraph(time_text, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("3. Difficulty Distribution", styles['Heading3']))
    diff_check = report['checks']['difficulty_distribution']
    try:
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = ['Easy', 'Medium', 'Hard']
        sizes = [diff_check['easy_count'], diff_check['medium_count'], diff_check['hard_count']]
        colors_pie = ['#90EE90', '#FFD700', '#FF6347']
        ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        plt.title('Difficulty Distribution')
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        img = Image(img_buffer, width=4*inch, height=3*inch)
        story.append(img)
    except Exception as e:
        story.append(Paragraph(f"Chart generation failed: {str(e)}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("4. Question Crispness", styles['Heading3']))
    crisp_check = report['checks']['crispness_analysis']
    crisp_text = f"Crisp Questions: {crisp_check['crisp_count']}<br/>"
    crisp_text += f"Verbose Questions: {crisp_check['verbose_count']}<br/>"
    crisp_text += f"Ambiguous Questions: {crisp_check['ambiguous_count']}<br/>"
    crisp_text += f"Crispness Score: {crisp_check['crispness_percentage']}%"
    story.append(Paragraph(crisp_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    if report['warnings']:
        story.append(Paragraph("Warnings", heading_style))
        for warning in report['warnings']:
            story.append(Paragraph(f"⚠ {warning}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))
    if report['suggestions']:
        story.append(Paragraph("Improvement Suggestions", heading_style))
        for i, suggestion in enumerate(report['suggestions'], 1):
            story.append(Paragraph(f"{i}. {suggestion}", styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))
    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Report generated by SmartExam Compiler v1.0.0", styles['Italic']))
    story.append(Paragraph("Powered by Lex, Yacc, Python, and AI", styles['Italic']))
    doc.build(story)
<<<<<<< HEAD
    print(f"PDF report generated: {output_path}")
=======
    print(f"PDF report generated: {output_path}")

def generate_enhanced_pdf(enhanced_text, enhanced_report, output_path):
    """Generate PDF for the enhanced question paper"""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a2332'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Title
    story.append(Paragraph("Enhanced Question Paper", title_style))
    story.append(Paragraph("Generated by SmartExam Compiler", styles['Heading3']))
    story.append(Spacer(1, 0.3 * inch))

    # Subject and basic info
    story.append(Paragraph(f"Subject: {enhanced_report.get('subject', 'Computer Science')}", styles['Normal']))
    story.append(Paragraph(f"Total Marks: {enhanced_report['statistics']['total_marks_calculated']}", styles['Normal']))
    story.append(Paragraph(f"Time Allowed: {enhanced_report['total_time']} minutes", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Improvements section
    story.append(Paragraph("Improvements Made", heading_style))
    for suggestion in enhanced_report.get('suggestions', []):
        story.append(Paragraph(f"• {suggestion}", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
    story.append(Spacer(1, 0.3 * inch))

    # Questions section
    story.append(Paragraph("Questions", heading_style))
    for q in enhanced_report.get('questions', []):
        q_num = q['number']
        q_text = q['text']
        q_marks = q['marks']
        q_difficulty = q['difficulty']
        q_time = q.get('estimated_time', 0)

        question_text = f"Q{q_num}. {q_text}"
        question_text += f"<br/><b>Marks: {q_marks} | Difficulty: {q_difficulty} | Time: {q_time} min</b>"

        story.append(Paragraph(question_text, styles['Normal']))
        story.append(Spacer(1, 0.2 * inch))

    story.append(PageBreak())

    # Statistics section
    story.append(Paragraph("Analysis Statistics", heading_style))

    # Difficulty distribution
    story.append(Paragraph("Difficulty Distribution", styles['Heading3']))
    diff_check = enhanced_report['checks']['difficulty_distribution']
    story.append(Paragraph(f"Easy: {diff_check['easy_count']} questions ({diff_check['easy_percentage']}%)", styles['Normal']))
    story.append(Paragraph(f"Medium: {diff_check['medium_count']} questions ({diff_check['medium_percentage']}%)", styles['Normal']))
    story.append(Paragraph(f"Hard: {diff_check['hard_count']} questions ({diff_check['hard_percentage']}%)", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    # Quality metrics
    story.append(Paragraph("Quality Metrics", styles['Heading3']))
    story.append(Paragraph(f"Overall Score: {enhanced_report['crispness_score']}/100", styles['Normal']))
    crispness = enhanced_report['checks']['crispness_analysis']['crispness_percentage']
    story.append(Paragraph(f"Crispness: {crispness}%", styles['Normal']))

    story.append(Spacer(1, 0.5 * inch))
    story.append(Paragraph("Generated by SmartExam Compiler v1.0.0", styles['Italic']))
    story.append(Paragraph("Powered by AI and Advanced Analysis", styles['Italic']))

    doc.build(story)
    print(f"Enhanced PDF generated: {output_path}")
>>>>>>> final_version
