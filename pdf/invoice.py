from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from pathlib import Path
from datetime import datetime
from config import APP_NAME


def get_invoice_path(invoice_number: str) -> Path:
    from config import DATA_DIR
    invoices_dir = DATA_DIR / "Factures"
    invoices_dir.mkdir(parents=True, exist_ok=True)
    return invoices_dir / f"facture_{invoice_number}.pdf"


def generate_invoice_pdf(sale_data: dict) -> Path:
    invoice_path = get_invoice_path(sale_data.get('invoice_number', 'unknown'))
    doc = SimpleDocTemplate(str(invoice_path), pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{APP_NAME}", styles['Title']))
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(Paragraph(f"Facture n° {sale_data.get('invoice_number', 'N/A')}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {sale_data.get('sale_date', datetime.now()).strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    client_info = sale_data.get('client', {})
    elements.append(Paragraph("Informations client:", styles['Heading3']))
    elements.append(Paragraph(f"Nom: {client_info.get('name', 'Client anonyme')}", styles['Normal']))
    if client_info.get('phone'):
        elements.append(Paragraph(f"Téléphone: {client_info.get('phone')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    items = sale_data.get('items', [])
    table_data = [['Produit', 'Qté', 'Prix unitaire', 'Total']]
    for item in items:
        table_data.append([
            item.get('product_name', ''),
            str(item.get('quantity', 0)),
            f"{item.get('unit_price', 0):,.0f} FCFA",
            f"{item.get('total', 0):,.0f} FCFA"
        ])
    
    item_table = Table(table_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(item_table)
    elements.append(Spacer(1, 0.5*cm))
    
    total = sale_data.get('total_amount', 0)
    consignment = sale_data.get('consignment_total', 0)
    total_general = total + consignment
    
    summary_data = [
        ['Total marchandises:', f"{total:,.0f} FCFA"],
        ['Total consignes:', f"{consignment:,.0f} FCFA"],
        ['Total général:', f"{total_general:,.0f} FCFA"]
    ]
    
    summary_table = Table(summary_data, colWidths=[12*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (-1,-1), (-1,-1), 12)
    ]))
    elements.append(summary_table)
    
    doc.build(elements)
    return invoice_path