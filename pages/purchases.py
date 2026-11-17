from nicegui import ui
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from services.purchase_service import PurchaseService
from services.supplier_service import SupplierService
from models.purchase import PurchaseStatus


def create_purchases_page(db: Session):
    purchase_service = PurchaseService(db)
    supplier_service = SupplierService(db)
    
    purchases = purchase_service.get_purchases_by_date_range(
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now()
    )
    suppliers = supplier_service.get_all_suppliers()
    
    search_query = {'value': ''}
    selected_status = {'value': None}
    
    def filter_purchases():
        filtered = purchases
        if search_query['value']:
            filtered = [p for p in filtered if search_query['value'].lower() in str(p.order_number).lower()]
        if selected_status['value']:
            filtered = [p for p in filtered if p.status == selected_status['value']]
        return filtered
    
    def refresh_table():
        filtered = filter_purchases()
        table.rows = []
        for purchase in filtered:
            supplier_name = purchase.supplier.name if purchase.supplier else "Fournisseur inconnu"
            table.rows.append({
                'id': purchase.id,
                'order': purchase.order_number,
                'date': purchase.order_date.strftime('%d/%m/%Y'),
                'supplier': supplier_name,
                'total': f"{purchase.total_amount:,.0f} FCFA",
                'status': purchase.status.value,
                'received': purchase.received_date.strftime('%d/%m/%Y') if purchase.received_date else '-'
            })
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Gestion des achats').classes('text-2xl font-bold text-gray-800')
            ui.button('Nouvelle commande', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_purchases = sum(p.total_amount for p in purchases)
                ui.label(f"{total_purchases:,.0f} FCFA").classes('text-2xl font-bold text-purple-600')
                ui.label('Total des achats (30j)').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                count_purchases = len(purchases)
                ui.label(f"{count_purchases}").classes('text-2xl font-bold text-blue-600')
                ui.label('Nombre de commandes').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                pending_purchases = [p for p in purchases if p.status == PurchaseStatus.PENDING]
                pending_total = sum(p.total_amount for p in pending_purchases)
                ui.label(f"{pending_total:,.0f} FCFA").classes('text-2xl font-bold text-orange-600')
                ui.label('Commandes en attente').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher par numéro de commande').props('placeholder=Rechercher...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            status_options = [status.value for status in PurchaseStatus]
            with ui.select(options=status_options, label='Statut', clearable=True).classes('w-48') as status_select:
                selected_status['value'] = status_select.value
                status_select.on('update:model-value', lambda e: (selected_status.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'order', 'label': 'N° Commande', 'field': 'order', 'align': 'left'},
                {'name': 'date', 'label': 'Date commande', 'field': 'date', 'align': 'left'},
                {'name': 'supplier', 'label': 'Fournisseur', 'field': 'supplier', 'align': 'left'},
                {'name': 'total', 'label': 'Total', 'field': 'total', 'align': 'right'},
                {'name': 'status', 'label': 'Statut', 'field': 'status', 'align': 'center'},
                {'name': 'received', 'label': 'Reçu le', 'field': 'received', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()