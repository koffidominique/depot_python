from nicegui import ui
from sqlalchemy.orm import Session
from services.client_service import ClientService
from decimal import Decimal


def create_clients_page(db: Session):
    client_service = ClientService(db)
    clients = client_service.get_all_clients()
    
    search_query = {'value': ''}
    
    def filter_clients():
        filtered = clients
        if search_query['value']:
            filtered = [c for c in filtered if search_query['value'].lower() in c.name.lower() or 
                      (c.phone and search_query['value'] in c.phone)]
        return filtered
    
    def refresh_table():
        filtered = filter_clients()
        table.rows = []
        for client in filtered:
            debt = client_service.get_client_debt(client.id)
            debt_class = 'text-red-600' if debt > 0 else 'text-green-600'
            table.rows.append({
                'id': client.id,
                'name': client.name,
                'phone': client.phone or '-',
                'email': client.email or '-',
                'debt': f"{debt:,.0f} FCFA",
                'debt_class': debt_class,
                'created': client.created_at.strftime('%d/%m/%Y')
            })
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Gestion des clients').classes('text-2xl font-bold text-gray-800')
            ui.button('Nouveau client', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_clients = len(clients)
                ui.label(f"{total_clients}").classes('text-2xl font-bold text-blue-600')
                ui.label('Nombre de clients').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                total_debt = sum(client_service.get_client_debt(c.id) for c in clients)
                ui.label(f"{total_debt:,.0f} FCFA").classes('text-2xl font-bold text-red-600')
                ui.label('Dette totale des clients').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                active_clients = [c for c in clients if c.is_active]
                ui.label(f"{len(active_clients)}").classes('text-2xl font-bold text-green-600')
                ui.label('Clients actifs').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full mb-4'):
            with ui.input('Rechercher un client').props('placeholder=Nom, téléphone...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'name', 'label': 'Nom', 'field': 'name', 'align': 'left'},
                {'name': 'phone', 'label': 'Téléphone', 'field': 'phone', 'align': 'left'},
                {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
                {'name': 'debt', 'label': 'Dette', 'field': 'debt', 'align': 'right'},
                {'name': 'created', 'label': 'Créé le', 'field': 'created', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()