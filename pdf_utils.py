"""PDF generation helpers for ChiwetoCare.

Uses reportlab for layout and matplotlib (thread-safe Figure OO API, Agg) for
charts embedded as PNG images. Kept separate from app.py to isolate the
dependency and avoid touching the core request flow.
"""
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

PRIMARY = colors.HexColor('#1a4a2e')
ACCENT = colors.HexColor('#2c7744')
LIGHT = colors.HexColor('#f1f5f9')
PALETTE = ['#1a4a2e', '#2c7744', '#f59e0b', '#3b82f6', '#ef4444',
           '#8b5cf6', '#10b981', '#6c757d']


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CTitle', parent=styles['Title'], textColor=PRIMARY, fontSize=20, spaceAfter=2))
    styles.add(ParagraphStyle('CSub', parent=styles['Normal'], textColor=colors.grey, fontSize=9, spaceAfter=10))
    styles.add(ParagraphStyle('CH2', parent=styles['Heading2'], textColor=ACCENT, fontSize=13, spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle('CBody', parent=styles['Normal'], fontSize=10, leading=15))
    styles.add(ParagraphStyle('CSmall', parent=styles['Normal'], fontSize=8, textColor=colors.grey))
    return styles


def _bar_png(labels, values, title='', horizontal=True, height_in=2.6):
    """Render a bar chart to a PNG BytesIO using the OO API (thread-safe)."""
    fig = Figure(figsize=(6.3, height_in), dpi=150)
    ax = fig.subplots()
    colours = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
    if horizontal:
        ypos = list(range(len(labels)))
        ax.barh(ypos, values, color=colours)
        ax.set_yticks(ypos)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        for i, v in enumerate(values):
            ax.text(v, i, ' ' + str(round(v, 2)), va='center', fontsize=8)
    else:
        xpos = list(range(len(labels)))
        ax.bar(xpos, values, color=colours)
        ax.set_xticks(xpos)
        ax.set_xticklabels(labels, fontsize=7, rotation=30, ha='right')
    if title:
        ax.set_title(title, fontsize=10, color='#1a4a2e')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf


def _line_png(x_labels, series, title=''):
    """series: dict name -> list[values] aligned with x_labels."""
    fig = Figure(figsize=(6.3, 2.6), dpi=150)
    ax = fig.subplots()
    xpos = list(range(len(x_labels)))
    for i, (name, vals) in enumerate(series.items()):
        ax.plot(xpos, vals, marker='o', linewidth=2, label=name,
                color=PALETTE[i % len(PALETTE)])
    ax.set_xticks(xpos)
    ax.set_xticklabels(x_labels, fontsize=8, rotation=20, ha='right')
    if title:
        ax.set_title(title, fontsize=10, color='#1a4a2e')
    if len(series) > 1:
        ax.legend(fontsize=7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return buf


def _kv_table(rows, col_widths=(45 * mm, 120 * mm)):
    t = Table(rows, colWidths=list(col_widths))
    t.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), PRIMARY),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.4, LIGHT),
    ]))
    return t


def _data_table(header, rows):
    data = [header] + rows
    t = Table(data, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#d0d7de')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.grey)
    canvas.drawString(15 * mm, 10 * mm, 'ChiwetoCare — Livestock Disease Prediction System')
    canvas.drawRightString(A4[0] - 15 * mm, 10 * mm, 'Page %d' % doc.page)
    canvas.restoreState()


def _doc(buf, title):
    return SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=18 * mm, title=title)


def build_prediction_pdf(prediction, report, possible_diseases, generated_on):
    """Return a BytesIO PDF for a single prediction/report."""
    buf = BytesIO()
    doc = _doc(buf, 'Prediction Report %s' % (prediction.prediction_id or ''))
    s = _styles()
    story = []

    story.append(Paragraph('Disease Prediction Report', s['CTitle']))
    story.append(Paragraph('Report %s &nbsp;|&nbsp; Generated %s' % (
        report.report_id or '-', generated_on), s['CSub']))
    story.append(HRFlowable(width='100%', thickness=1, color=ACCENT, spaceAfter=8))

    # Result banner
    conf_pct = round((prediction.confidence or 0) * 100, 1)
    story.append(Paragraph('Predicted Condition', s['CH2']))
    story.append(_kv_table([
        ['Disease', str(prediction.disease_name or '-')],
        ['Confidence', '%s%%' % conf_pct],
        ['Severity', str(prediction.severity or '-').capitalize()],
        ['Category', str(prediction.disease_category or '-').capitalize()],
        ['Veterinary review', str(prediction.review_status or 'pending').capitalize()],
    ]))
    story.append(Spacer(1, 8))

    # Possible diseases chart
    if possible_diseases:
        labels = [d.get('disease', '-') for d in possible_diseases]
        values = [round(float(d.get('probability', 0)) * 100, 1) for d in possible_diseases]
        story.append(Paragraph('Top Possible Conditions (%)', s['CH2']))
        story.append(Image(_bar_png(labels, values, height_in=1.8),
                           width=165 * mm, height=47 * mm))
        story.append(Spacer(1, 6))

    # Animal & report info
    story.append(Paragraph('Animal &amp; Case Information', s['CH2']))
    story.append(_kv_table([
        ['Animal', str(report.animal_name or '-')],
        ['Species', str(report.animal_type or '-').capitalize()],
        ['Sex', str(report.animal_sex or '-').capitalize()],
        ['Age (months)', str(report.animal_age if report.animal_age is not None else '-')],
        ['Temperature (C)', str(report.temperature if report.temperature is not None else '-')],
        ['Status', str(report.status or '-').capitalize()],
    ]))
    story.append(Spacer(1, 8))

    # Symptoms
    symptoms = report.get_additional_symptoms_list() if hasattr(report, 'get_additional_symptoms_list') else []
    story.append(Paragraph('Reported Symptoms', s['CH2']))
    story.append(Paragraph(', '.join(symptoms) if symptoms else 'None recorded', s['CBody']))
    story.append(Spacer(1, 8))

    # Recommendation
    story.append(Paragraph('Recommended Action', s['CH2']))
    story.append(Paragraph(
        str(prediction.recommendation_text or 'Isolate the animal and wait for veterinarian review and prescription.'),
        s['CBody']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        'This AI-generated prediction is a decision-support aid and does not replace professional '
        'veterinary diagnosis. Always confirm with a qualified veterinarian before treatment.',
        s['CSmall']))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf


def build_reports_pdf(meta, disease_rows, location_rows, vet_rows,
                      trend_labels=None, trend_values=None, generated_on=''):
    """Analytics PDF for the organization admin (respects active filters).

    meta: dict with title + filter description fields.
    disease_rows: list of (disease, count) already sorted desc.
    location_rows: list of dicts {location, disease_name, frequency}.
    vet_rows: list of dicts {full_name, service_location, status,
              reviewed_predictions_count, assigned_farmers_count}.
    trend_labels/trend_values: optional period labels and counts for a trend line.
    """
    buf = BytesIO()
    doc = _doc(buf, meta.get('title', 'Analytics Report'))
    s = _styles()
    story = []

    story.append(Paragraph(meta.get('title', 'Disease Analytics Report'), s['CTitle']))
    story.append(Paragraph(meta.get('subtitle', ''), s['CSub']))
    story.append(HRFlowable(width='100%', thickness=1, color=ACCENT, spaceAfter=8))

    # Filters summary
    filt = meta.get('filters')
    if filt:
        story.append(Paragraph('Filters', s['CH2']))
        story.append(_kv_table([[k, v] for k, v in filt]))
        story.append(Spacer(1, 8))

    # Most frequent diseases chart + table
    story.append(Paragraph('Most Frequent Diseases', s['CH2']))
    if disease_rows:
        labels = [d for d, _ in disease_rows]
        values = [c for _, c in disease_rows]
        story.append(Image(_bar_png(labels, values, height_in=2.4),
                           width=165 * mm, height=58 * mm))
        story.append(Spacer(1, 4))
        total = sum(values) or 1
        story.append(_data_table(
            ['Disease', 'Cases', 'Share'],
            [[d, str(c), '%.1f%%' % (100 * c / total)] for d, c in disease_rows]))
    else:
        story.append(Paragraph('No prediction data for the selected filters.', s['CBody']))
    story.append(Spacer(1, 8))

    # Trend
    if trend_labels and trend_values and any(trend_values):
        story.append(Paragraph('Disease Trend Over Time', s['CH2']))
        story.append(Image(_line_png(trend_labels, {'Predictions': trend_values}),
                           width=165 * mm, height=58 * mm))
        story.append(Spacer(1, 8))

    # Dominant disease by location
    if location_rows:
        story.append(Paragraph('Dominant Disease by Location', s['CH2']))
        story.append(_data_table(
            ['Location', 'Most Common Disease', 'Cases'],
            [[r.get('location', '-'), r.get('disease_name', '-'), str(r.get('frequency', 0))]
             for r in location_rows]))
        story.append(Spacer(1, 8))

    # Vet activity
    if vet_rows:
        story.append(Paragraph('Veterinarian Activity', s['CH2']))
        story.append(_data_table(
            ['Veterinarian', 'Location', 'Status', 'Reviews', 'Farmers'],
            [[r.get('full_name', '-'), r.get('service_location', '-'),
              str(r.get('status', '-')).capitalize(),
              str(r.get('reviewed_predictions_count', 0)),
              str(r.get('assigned_farmers_count', 0))] for r in vet_rows]))

    story.append(Spacer(1, 10))
    story.append(Paragraph('Generated %s by ChiwetoCare.' % generated_on, s['CSmall']))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buf.seek(0)
    return buf
