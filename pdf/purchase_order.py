from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from pathlib import Path
from datetime import datetime
from config import APP_NAME


def get_purchase_order_path(order_number: str) -> Path:
    from config import DATA_DIR
    orders_dir = DATA_DIR / "Bons_Commande"
    orders_dir.mkdir(parents=True, exist_ok=True)
    return orders_dir / f"bon_commande_{order_number}.pdf"


def generate_purchase_order_pdf(order_data: dict) -> Path:
    order_path = get_purchase_order_path(order_data.get('order_number', 'unknown'))
    doc = SimpleDocTemplate(str(order_path), pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"{APP_NAME}", styles['Title']))
    elements.append(Spacer(1, 0.5*cm))
    
    elements.append(Paragraph(f"Bon de commande n° {order_data.get('order_number', 'N/A')}", styles['Heading2']))
    elements.append(Paragraph(f"Date: {order_data.get('order_date', datetime.now()).strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    supplier_info = order_data.get('supplier', {})
    elements.append(Paragraph("Informations fournisseur:", styles['Heading3']))
    elements.append(Paragraph(f"Nom: {supplier_info.get('name', 'Fournisseur inconnu')}", styles['Normal']))
    if supplier_info.get('phone'):
        elements.append(Paragraph(f"Téléphone: {supplier_info.get('phone')}", styles['Normal']))
    if supplier_info.get('address'):
        elements.append(Paragraph(f"Adresse: {supplier_info.get('address')}", styles['Normal']))
    elements.append(Spacer(1, 0.5*cm))
    
    items = order_data.get('items', [])
    table_data = [['Produit', 'Qté commandée', 'Prix unitaire', 'Total']]
    total_order = 0
    for item in items:
        line_total = item.get('quantity', 0) * item.get('unit_price', 0)
        total_order += line_total
        table_data.append([
            item.get('product_name', ''),
            str(item.get('quantity', 0)),
            f"{item.get('unit_price', 0):,.0f} FCFA",
            f"{line_total:,.0f} FCFA"
        ])
    
    item_table = Table(table_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
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
    
    summary_data = [['Total commande:', f"{total_order:,.0f} FCFA"]]
    summary_table = Table(summary_data, colWidths=[12*cm, 4*cm])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (-1,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (-1,-1), (-1,-1), 12)
    ]))
    elements.append(summary_table)
    
    doc.build(elements)
    return order_path