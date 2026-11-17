from nicegui import ui
from sqlalchemy.orm import Session
from services.client_service import ClientService
from services.supplier_service import SupplierService
from enums import DebtType


def create_debts_page(db: Session):
    client_service = ClientService(db)
    supplier_service = SupplierService(db)
    
    selected_tab = {'value': 'clients'}
    
    def refresh_client_debts():
        clients = client_service.get_all_clients()
        client_debts_table.rows = []
        total_client_debt = 0
        for client in clients:
            debt = client_service.get_client_debt(client.id)
            if debt > 0:
                total_client_debt += debt
                client_debts_table.rows.append({
                    'id': client.id,
                    'name': client.name,
                    'phone': client.phone or '-',
                    'debt': f"{debt:,.0f} FCFA",
                    'debt_class': 'text-red-600'
                })
        total_client_label.text = f"{total_client_debt:,.0f} FCFA"
        client_debts_table.update()
    
    def refresh_supplier_debts():
        suppliers = supplier_service.get_all_suppliers()
        supplier_debts_table.rows = []
        total_supplier_debt = 0
        for supplier in suppliers:
            debt = supplier_service.get_supplier_debt(supplier.id)
            if debt > 0:
                total_supplier_debt += debt
                supplier_debts_table.rows.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'phone': supplier.phone or '-',
                    'debt': f"{debt:,.0f} FCFA",
                    'debt_class': 'text-red-600'
                })
        total_supplier_label.text = f"{total_supplier_debt:,.0f} FCFA"
        supplier_debts_table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion des créances et dettes').classes('text-2xl font-bold text-gray-800')
        
        with ui.tabs().classes('w-full') as tabs:
            client_tab = ui.tab('Créances clients')
            supplier_tab = ui.tab('Dettes fournisseurs')
        
        with ui.tab_panels(tabs, value=client_tab).classes('w-full'):
            with ui.tab_panel(client_tab):
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.card().classes('flex-1 p-4'):
                        total_client_label = ui.label('0 FCFA').classes('text-2xl font-bold text-red-600')
                        ui.label('Total des créances clients').classes('text-sm text-gray-500')
                    
                    with ui.card().classes('flex-1 p-4'):
                        client_count_label = ui.label('0').classes('text-2xl font-bold text-orange-600')
                        ui.label('Clients en dette').classes('text-sm text-gray-500')
                
                client_debts_table = ui.table(
                    columns=[
                        {'name': 'name', 'label': 'Client', 'field': 'name', 'align': 'left'},
                        {'name': 'phone', 'label': 'Téléphone', 'field': 'phone', 'align': 'left'},
                        {'name': 'debt', 'label': 'Montant dû', 'field': 'debt', 'align': 'right'},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                    ],
                    rows=[],
                    row_key='id'
                ).classes('w-full')
                
                ui.button('Actualiser', on_click=refresh_client_debts).classes('mt-4')
            
            with ui.tab_panel(supplier_tab):
                with ui.row().classes('w-full gap-4 mb-4'):
                    with ui.card().classes('flex-1 p-4'):
                        total_supplier_label = ui.label('0 FCFA').classes('text-2xl font-bold text-red-600')
                        ui.label('Total des dettes fournisseurs').classes('text-sm text-gray-500')
                    
                    with ui.card().classes('flex-1 p-4'):
                        supplier_count_label = ui.label('0').classes('text-2xl font-bold text-orange-600')
                        ui.label('Fournisseurs en dette').classes('text-sm text-gray-500')
                
                supplier_debts_table = ui.table(
                    columns=[
                        {'name': 'name', 'label': 'Fournisseur', 'field': 'name', 'align': 'left'},
                        {'name': 'phone', 'label': 'Téléphone', 'field': 'phone', 'align': 'left'},
                        {'name': 'debt', 'label': 'Montant dû', 'field': 'debt', 'align': 'right'},
                        {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                    ],
                    rows=[],
                    row_key='id'
                ).classes('w-full')
                
                ui.button('Actualiser', on_click=refresh_supplier_debts).classes('mt-4')
    
    refresh_client_debts()
    refresh_supplier_debts()