from nicegui import ui
from sqlalchemy.orm import Session
from services.reporting_service import ReportingService
from services.stock_service import StockService
from services.sales_service import SalesService
from datetime import datetime

def create_dashboard_page(db: Session):
    reporting_service = ReportingService(db)
    stock_service = StockService(db)
    sales_service = SalesService(db)
    
    kpis = reporting_service.get_dashboard_kpis()
    sales_trend = reporting_service.get_sales_trend(days=7)
    top_products = reporting_service.get_top_selling_products(limit=5)
    low_stock_products = stock_service.get_low_stock_products()
    recent_sales = sales_service.get_all_sales()[:5]
    
    with ui.column().classes('w-full gap-6 p-6'):
        with ui.row().classes('w-full gap-4 grid grid-cols-4'):
            with ui.card().classes('p-4'):
                ui.label('Chiffre d\'affaires du jour').classes('text-sm text-slate-500')
                ui.label(f"{kpis['daily_sales']:,.0f} FCFA").classes('text-2xl font-bold text-slate-900')
            
            with ui.card().classes('p-4'):
                ui.label('Ventes du jour').classes('text-sm text-slate-500')
                ui.label(f"{kpis['daily_sales_count']}").classes('text-2xl font-bold text-slate-900')
            
            with ui.card().classes('p-4'):
                ui.label('Valeur du stock').classes('text-sm text-slate-500')
                ui.label(f"{kpis['stock_value']:,.0f} FCFA").classes('text-2xl font-bold text-slate-900')
            
            with ui.card().classes('p-4'):
                ui.label('Produits en alerte').classes('text-sm text-slate-500')
                ui.label(f"{kpis['low_stock_count']}").classes('text-2xl font-bold text-orange-600')
        
        with ui.row().classes('w-full gap-4 grid grid-cols-4'):
            with ui.card().classes('p-4'):
                ui.label('Créances clients').classes('text-sm text-slate-500')
                ui.label(f"{kpis['client_debts']:,.0f} FCFA").classes('text-2xl font-bold text-red-600')
            
            with ui.card().classes('p-4'):
                ui.label('Dettes fournisseurs').classes('text-sm text-slate-500')
                ui.label(f"{kpis['supplier_debts']:,.0f} FCFA").classes('text-2xl font-bold text-orange-600')
            
            with ui.card().classes('p-4'):
                ui.label('Clients actifs').classes('text-sm text-slate-500')
                ui.label(f"{kpis['active_clients']}").classes('text-2xl font-bold text-slate-900')
            
            with ui.card().classes('p-4'):
                ui.label('Consignes en circulation').classes('text-sm text-slate-500')
                ui.label(f"{kpis['consignment_balance']:,.0f} FCFA").classes('text-2xl font-bold text-blue-600')
        
        with ui.row().classes('w-full gap-4 grid grid-cols-2'):
            with ui.card().classes('p-4 col-span-1'):
                ui.label('Évolution du chiffre d\'affaires (7 jours)').classes('text-lg font-semibold mb-4')
                if sales_trend['dates']:
                    ui.line_plot(
                        sales_trend['dates'],
                        [sales_trend['sales']],
                        ['CA'],
                        ['#2563eb']
                    ).classes('h-64')
                else:
                    ui.label('Pas de données disponibles').classes('text-slate-500')
            
            with ui.card().classes('p-4 col-span-1'):
                ui.label('Top 5 produits vendus').classes('text-lg font-semibold mb-4')
                if top_products:
                    with ui.table(rows=top_products, columns=[
                        {'name': 'name', 'label': 'Produit', 'field': 'name'},
                        {'name': 'quantity', 'label': 'Quantité', 'field': 'quantity'},
                        {'name': 'revenue', 'label': 'CA', 'field': 'revenue'}
                    ]).classes('w-full'):
                        pass
                else:
                    ui.label('Pas de données disponibles').classes('text-slate-500')
        
        with ui.row().classes('w-full gap-4 grid grid-cols-2'):
            with ui.card().classes('p-4 col-span-1'):
                ui.label('Produits à réapprovisionner').classes('text-lg font-semibold mb-4')
                if low_stock_products:
                    product_list = [
                        {
                            'name': p.name,
                            'stock': float(p.stock_quantity),
                            'min': float(p.min_stock)
                        } for p in low_stock_products
                    ]
                    with ui.table(rows=product_list, columns=[
                        {'name': 'name', 'label': 'Produit', 'field': 'name'},
                        {'name': 'stock', 'label': 'Stock actuel', 'field': 'stock'},
                        {'name': 'min', 'label': 'Stock minimum', 'field': 'min'}
                    ]).classes('w-full'):
                        pass
                else:
                    ui.label('Aucun produit en alerte').classes('text-green-600')
            
            with ui.card().classes('p-4 col-span-1'):
                ui.label('Dernières ventes').classes('text-lg font-semibold mb-4')
                if recent_sales:
                    sales_list = [
                        {
                            'reference': s.reference,
                            'date': s.date.strftime('%d/%m/%Y'),
                            'amount': float(s.total_amount)
                        } for s in recent_sales
                    ]
                    with ui.table(rows=sales_list, columns=[
                        {'name': 'reference', 'label': 'Référence', 'field': 'reference'},
                        {'name': 'date', 'label': 'Date', 'field': 'date'},
                        {'name': 'amount', 'label': 'Montant', 'field': 'amount'}
                    ]).classes('w-full'):
                        pass
                else:
                    ui.label('Pas de ventes récentes').classes('text-slate-500')