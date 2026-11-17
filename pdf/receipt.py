from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from pathlib import Path
from datetime import datetime
from config import APP_NAME


def get_receipt_path(receipt_number: str) -> Path:
    from config import DATA_DIR
    receipts_dir = DATA_DIR / "Reçus"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    return receipts_dir / f"recu_{receipt_number}.pdf"


def generate_receipt_pdf(payment_data: dict) -> Path:
    receipt_path = get_receipt_path(payment_data.get('receipt_number', 'unknown'))
    doc = SimpleDocTemplate(str(receipt_path), pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{APP_NAME}", styles['Title']))
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(Paragraph(f"Reçu de paiement n° {payment_data.get('receipt_number', 'N/A')}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {payment_data.get('payment_date', datetime.now()).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    client_info = payment_data.get('client', {})
    elements.append(Paragraph("Informations client:", styles['Heading3']))
    elements.append(Paragraph(f"Nom: {client_info.get('name', 'Client anonyme')}", styles['Normal']))
    if client_info.get('phone'):
        elements.append(Paragraph(f"Téléphone: {client_info.get('phone')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    amount = payment_data.get('amount', 0)
    payment_method = payment_data.get('payment_method', 'Espèces')
    
    elements.append(Paragraph(f"Montant reçu: {amount:,.0f} FCFA", styles['Heading3']))
    elements.append(Paragraph(f"Mode de paiement: {payment_method}", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    
    elements.append(Paragraph("Merci pour votre confiance!", styles['Normal']))
    
    doc.build(elements)
    return receipt_path