from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from pathlib import Path
from datetime import datetime
from config import APP_NAME


def get_cash_closure_report_path(closure_date: datetime) -> Path:
    from config import DATA_DIR
    reports_dir = DATA_DIR / "Rapports_Fermeture_Caisse"
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_str = closure_date.strftime('%Y%m%d')
    return reports_dir / f"fermeture_caisse_{date_str}.pdf"


def generate_cash_closure_report_pdf(closure_data: dict) -> Path:
    report_path = get_cash_closure_report_path(closure_data.get('closure_date', datetime.now()))
    doc = SimpleDocTemplate(str(report_path), pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{APP_NAME}", styles['Title']))
    elements.append(Spacer(1, 0.5*cm))
    
    closure_date = closure_data.get('closure_date', datetime.now())
    elements.append(Paragraph(f"Rapport de fermeture de caisse du {closure_date.strftime('%d/%m/%Y')}", styles['Heading2']))
    elements.append(Spacer(1, 0.5*cm))
    
    summary_data = [
        ['Total des ventes:', f"{closure_data.get('total_sales', 0):,.0f} FCFA"],
        ['Total des dépenses:', f"{closure_data.get('total_expenses', 0):,.0f} FCFA"],
        ['Bénéfice net:', f"{closure_data.get('net_profit', 0):,.0f} FCFA"],
        ['Nombre de ventes:', str(closure_data.get('sales_count', 0))],
        ['Nombre de dépenses:', str(closure_data.get('expenses_count', 0))]
    ]
    
    summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 1*cm))
    
    elements.append(Paragraph("Signature de l'opérateur:", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("Signature du gérant:", styles['Normal']))
    
    doc.build(elements)
    return report_path