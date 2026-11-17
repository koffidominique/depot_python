from nicegui import ui
from sqlalchemy.orm import Session
from services.product_service import ProductService
from services.client_service import ClientService
from enums import ConsignationStatus
from datetime import datetime, timedelta


def create_consignations_page(db: Session):
    product_service = ProductService(db)
    client_service = ClientService(db)
    
    search_query = {'value': ''}
    selected_status = {'value': None}
    
    def filter_consignations():
        products = product_service.get_all_products()
        filtered = [p for p in products if hasattr(p, 'consignment') and p.consignment > 0]
        if search_query['value']:
            filtered = [c for c in filtered if search_query['value'].lower() in c.name.lower()]
        return filtered
    
    def refresh_table():
        filtered = filter_consignations()
        table.rows = []
        total_consignment = 0
        for product in filtered:
            consignment_value = product.consignment * product.quantity
            total_consignment += consignment_value
            table.rows.append({
                'id': product.id,
                'name': product.name,
                'quantity': product.quantity,
                'unit_consignment': f"{product.consignment:,.0f} FCFA",
                'total_consignment': f"{consignment_value:,.0f} FCFA",
                'created': product.created_at.strftime('%d/%m/%Y')
            })
        total_label.text = f"{total_consignment:,.0f} FCFA"
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion des consignations').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.button('Nouvelle consignation', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_label = ui.label('0 FCFA').classes('text-2xl font-bold text-blue-600')
                ui.label('Valeur totale des consignations').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                product_count = len(filter_consignations())
                ui.label(f"{product_count}").classes('text-2xl font-bold text-purple-600')
                ui.label('Produits avec consignation').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                total_quantity = sum(p.quantity for p in filter_consignations())
                ui.label(f"{total_quantity}").classes('text-2xl font-bold text-green-600')
                ui.label('Quantité totale en consignation').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full mb-4'):
            with ui.input('Rechercher un produit').props('placeholder=Nom du produit...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'name', 'label': 'Produit', 'field': 'name', 'align': 'left'},
                {'name': 'quantity', 'label': 'Qté', 'field': 'quantity', 'align': 'center'},
                {'name': 'unit_consignment', 'label': 'Consigne unitaire', 'field': 'unit_consignment', 'align': 'right'},
                {'name': 'total_consignment', 'label': 'Consigne totale', 'field': 'total_consignment', 'align': 'right'},
                {'name': 'created', 'label': 'Créé le', 'field': 'created', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()