from nicegui import ui
from sqlalchemy.orm import Session
from services.auth_service import AuthService


def create_users_page(db: Session):
    auth_service = AuthService(db)
    
    search_query = {'value': ''}
    
    def filter_users():
        users = auth_service.get_all_users()
        filtered = users
        if search_query['value']:
            filtered = [u for u in filtered if search_query['value'].lower() in u.username.lower() or 
                      search_query['value'].lower() in u.full_name.lower()]
        return filtered
    
    def refresh_table():
        filtered = filter_users()
        table.rows = []
        for user in filtered:
            table.rows.append({
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'role': user.role,
                'is_active': 'Actif' if user.is_active else 'Inactif',
                'created': user.created_at.strftime('%d/%m/%Y')
            })
        total_users_label.text = f"{len(filtered)}"
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion des utilisateurs').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.button('Nouvel utilisateur', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_users_label = ui.label('0').classes('text-2xl font-bold text-purple-600')
                ui.label('Nombre total d\'utilisateurs').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                active_users = len([u for u in filter_users() if u.is_active])
                ui.label(f"{active_users}").classes('text-2xl font-bold text-green-600')
                ui.label('Utilisateurs actifs').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                admin_users = len([u for u in filter_users() if u.role == 'admin'])
                ui.label(f"{admin_users}").classes('text-2xl font-bold text-blue-600')
                ui.label('Administrateurs').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher un utilisateur').props('placeholder=Nom, identifiant...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            ui.button('Actualiser', on_click=refresh_table).classes('ml-2')
        
        table = ui.table(
            columns=[
                {'name': 'username', 'label': 'Identifiant', 'field': 'username', 'align': 'left'},
                {'name': 'full_name', 'label': 'Nom complet', 'field': 'full_name', 'align': 'left'},
                {'name': 'role', 'label': 'Rôle', 'field': 'role', 'align': 'left'},
                {'name': 'is_active', 'label': 'Statut', 'field': 'is_active', 'align': 'center'},
                {'name': 'created', 'label': 'Créé le', 'field': 'created', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()