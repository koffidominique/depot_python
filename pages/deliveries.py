from nicegui import ui
from sqlalchemy.orm import Session
from services.sales_service import SalesService
from services.client_service import ClientService
from enums import DeliveryStatus
from datetime import datetime, timedelta


def create_deliveries_page(db: Session):
    sales_service = SalesService(db)
    client_service = ClientService(db)
    
    search_query = {'value': ''}
    selected_status = {'value': None}
    
    def filter_deliveries():
        sales = sales_service.get_sales_by_date_range(
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        filtered = [s for s in sales if hasattr(s, 'delivery_status') and s.delivery_status is not None]
        if search_query['value']:
            filtered = [d for d in filtered if search_query['value'].lower() in str(d.invoice_number).lower()]
        if selected_status['value']:
            filtered = [d for d in filtered if d.delivery_status == selected_status['value']]
        return filtered
    
    def refresh_table():
        filtered = filter_deliveries()
        table.rows = []
        for delivery in filtered:
            client_name = delivery.client.name if delivery.client else "Client anonyme"
            table.rows.append({
                'id': delivery.id,
                'invoice': delivery.invoice_number,
                'client': client_name,
                'date': delivery.sale_date.strftime('%d/%m/%Y'),
                'total': f"{delivery.total_amount:,.0f} FCFA",
                'status': delivery.delivery_status.value if delivery.delivery_status else 'Non défini',
                'created': delivery.sale_date.strftime('%d/%m/%Y %H:%M')
            })
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Gestion des livraisons').classes('text-2xl font-bold text-gray-800')
            ui.button('Nouvelle livraison', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                pending_deliveries = len([d for d in filter_deliveries() if d.delivery_status == DeliveryStatus.PENDING])
                ui.label(f"{pending_deliveries}").classes('text-2xl font-bold text-orange-600')
                ui.label('Livraisons en attente').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                in_progress = len([d for d in filter_deliveries() if d.delivery_status == DeliveryStatus.IN_PROGRESS])
                ui.label(f"{in_progress}").classes('text-2xl font-bold text-blue-600')
                ui.label('Livraisons en cours').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                completed = len([d for d in filter_deliveries() if d.delivery_status == DeliveryStatus.DELIVERED])
                ui.label(f"{completed}").classes('text-2xl font-bold text-green-600')
                ui.label('Livraisons terminées').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher par numéro de facture').props('placeholder=Rechercher...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            status_options = [status.value for status in DeliveryStatus]
            with ui.select(options=status_options, label='Statut', clearable=True).classes('w-48') as status_select:
                selected_status['value'] = status_select.value
                status_select.on('update:model-value', lambda e: (selected_status.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'invoice', 'label': 'N° Facture', 'field': 'invoice', 'align': 'left'},
                {'name': 'client', 'label': 'Client', 'field': 'client', 'align': 'left'},
                {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'left'},
                {'name': 'total', 'label': 'Total', 'field': 'total', 'align': 'right'},
                {'name': 'status', 'label': 'Statut', 'field': 'status', 'align': 'center'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()