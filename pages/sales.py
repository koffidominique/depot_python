from nicegui import ui
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from services.sales_service import SalesService
from services.client_service import ClientService
from services.product_service import ProductService
from models.sale import SaleStatus, PaymentMethod


def create_sales_page(db: Session):
    sales_service = SalesService(db)
    client_service = ClientService(db)
    product_service = ProductService(db)
    
    sales = sales_service.get_sales_by_date_range(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    clients = client_service.get_all_clients()
    products = product_service.get_all_products()
    
    search_query = {'value': ''}
    selected_status = {'value': None}
    
    def filter_sales():
        filtered = sales
        if search_query['value']:
            filtered = [s for s in filtered if search_query['value'].lower() in str(s.invoice_number).lower()]
        if selected_status['value']:
            filtered = [s for s in filtered if s.status == selected_status['value']]
        return filtered
    
    def refresh_table():
        filtered = filter_sales()
        table.rows = []
        for sale in filtered:
            client_name = sale.client.name if sale.client else "Client anonyme"
            table.rows.append({
                'id': sale.id,
                'invoice': sale.invoice_number,
                'date': sale.sale_date.strftime('%d/%m/%Y %H:%M'),
                'client': client_name,
                'total': f"{sale.total_amount:,.0f} FCFA",
                'status': sale.status.value,
                'payment': sale.payment_method.value
            })
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Gestion des ventes').classes('text-2xl font-bold text-gray-800')
            with ui.row().classes('gap-2'):
                ui.button('Nouvelle vente', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_sales = sum(s.total_amount for s in sales)
                ui.label(f"{total_sales:,.0f} FCFA").classes('text-2xl font-bold text-green-600')
                ui.label('Total des ventes (30j)').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                count_sales = len(sales)
                ui.label(f"{count_sales}").classes('text-2xl font-bold text-blue-600')
                ui.label('Nombre de ventes').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                pending_sales = [s for s in sales if s.status == SaleStatus.PENDING]
                pending_total = sum(s.total_amount for s in pending_sales)
                ui.label(f"{pending_total:,.0f} FCFA").classes('text-2xl font-bold text-orange-600')
                ui.label('Ventes en attente').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher par numéro de facture').props('placeholder=Rechercher...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            status_options = [status.value for status in SaleStatus]
            with ui.select(options=status_options, label='Statut', clearable=True).classes('w-48') as status_select:
                selected_status['value'] = status_select.value
                status_select.on('update:model-value', lambda e: (selected_status.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'invoice', 'label': 'N° Facture', 'field': 'invoice', 'align': 'left'},
                {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'left'},
                {'name': 'client', 'label': 'Client', 'field': 'client', 'align': 'left'},
                {'name': 'total', 'label': 'Total', 'field': 'total', 'align': 'right'},
                {'name': 'status', 'label': 'Statut', 'field': 'status', 'align': 'center'},
                {'name': 'payment', 'label': 'Paiement', 'field': 'payment', 'align': 'center'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()