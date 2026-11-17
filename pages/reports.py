from nicegui import ui
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from services.reporting_service import ReportingService


def create_reports_page(db: Session):
    reporting_service = ReportingService(db)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    dashboard_kpis = reporting_service.get_dashboard_kpis()
    sales_trend = reporting_service.get_sales_trend(start_date, end_date)
    top_products = reporting_service.get_top_products(start_date, end_date, limit=10)
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Rapports et analyses').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            ui.button('Rapport de ventes', icon='receipt_long', color='blue').classes('bg-blue-600 hover:bg-blue-700')
            ui.button('Rapport de stock', icon='inventory_2', color='purple').classes('bg-purple-600 hover:bg-purple-700')
            ui.button('Rapport financier', icon='account_balance', color='green').classes('bg-green-600 hover:bg-green-700')
            ui.button('Exporter PDF', icon='picture_as_pdf', color='red').classes('bg-red-600 hover:bg-red-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{dashboard_kpis.total_revenue:,.0f} FCFA").classes('text-2xl font-bold text-green-600')
                ui.label('Chiffre d\'affaires total').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{dashboard_kpis.total_profit:,.0f} FCFA").classes('text-2xl font-bold text-blue-600')
                ui.label('Bénéfice total').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{dashboard_kpis.total_sales}").classes('text-2xl font-bold text-purple-600')
                ui.label('Nombre de ventes').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{dashboard_kpis.stock_value:,.0f} FCFA").classes('text-2xl font-bold text-orange-600')
                ui.label('Valeur du stock').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('Tendance des ventes (30 jours)').classes('text-lg font-semibold text-gray-700 mb-2')
                chart = ui.line_plot(n=1).classes('w-full h-64')
                dates = [day.date.strftime('%d/%m') for day in sales_trend]
                values = [float(day.total) for day in sales_trend]
                chart.push(values)
                chart.set_legend(['Ventes'])
        
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label('Top 10 produits vendus').classes('text-lg font-semibold text-gray-700 mb-2')
                table = ui.table(
                    columns=[
                        {'name': 'rank', 'label': '#', 'field': 'rank', 'align': 'center'},
                        {'name': 'product', 'label': 'Produit', 'field': 'product', 'align': 'left'},
                        {'name': 'quantity', 'label': 'Quantité', 'field': 'quantity', 'align': 'right'},
                        {'name': 'revenue', 'label': 'Chiffre d\'affaires', 'field': 'revenue', 'align': 'right'}
                    ],
                    rows=[],
                    row_key='id'
                ).classes('w-full')
                
                for i, product in enumerate(top_products, 1):
                    table.rows.append({
                        'rank': i,
                        'product': product.name,
                        'quantity': f"{product.quantity_sold}",
                        'revenue': f"{product.total_revenue:,.0f} FCFA"
                    })
                table.update()