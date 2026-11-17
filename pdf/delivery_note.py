from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from pathlib import Path
from datetime import datetime
from config import APP_NAME


def get_delivery_note_path(delivery_number: str) -> Path:
    from config import DATA_DIR
    delivery_dir = DATA_DIR / "Bons_Livraison"
    delivery_dir.mkdir(parents=True, exist_ok=True)
    return delivery_dir / f"bon_livraison_{delivery_number}.pdf"


def generate_delivery_note_pdf(delivery_data: dict) -> Path:
    delivery_path = get_delivery_note_path(delivery_data.get('delivery_number', 'unknown'))
    doc = SimpleDocTemplate(str(delivery_path), pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{APP_NAME}", styles['Title']))
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(Paragraph(f"Bon de livraison n° {delivery_data.get('delivery_number', 'N/A')}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {delivery_data.get('delivery_date', datetime.now()).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    client_info = delivery_data.get('client', {})
    elements.append(Paragraph("Informations client:", styles['Heading3']))
    elements.append(Paragraph(f"Nom: {client_info.get('name', 'Client anonyme')}", styles['Normal']))
    if client_info.get('phone'):
        elements.append(Paragraph(f"Téléphone: {client_info.get('phone')}", styles['Normal']))
    if client_info.get('address'):
        elements.append(Paragraph(f"Adresse: {client_info.get('address')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    items = delivery_data.get('items', [])
    table_data = [['Produit', 'Conditionnement', 'Qté']]
    for item in items:
        table_data.append([
            item.get('product_name', ''),
            item.get('packaging', 'Unité'),
            str(item.get('quantity', 0))
        ])
    
    item_table = Table(table_data, colWidths=[10*cm, 4*cm, 2*cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 1*cm))
    
    elements.append(Paragraph("Signature du livreur:", styles['Normal']))
    elements.append(Spacer(1, 1*cm))
    elements.append(Paragraph("Signature du client:", styles['Normal']))
    
    doc.build(elements)
    return delivery_path