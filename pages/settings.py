from nicegui import ui
from sqlalchemy.orm import Session
from services.auth_service import AuthService
from services.backup_service import BackupService
from config import DATA_DIR


def create_settings_page(db: Session):
    auth_service = AuthService(db)
    backup_service = BackupService()
    
    users = auth_service.get_all_users()
    
    with ui.column().classes('w-full gap-6 p-6'):
        ui.label('Paramètres').classes('text-2xl font-bold text-gray-800')
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Paramètres généraux').classes('text-xl font-semibold text-gray-700 mb-4')
            with ui.row().classes('w-full gap-4 mb-3'):
                with ui.input('Nom de l\'entreprise').classes('flex-1'):
                    ui.tooltip('Nom de votre entreprise affiché sur les documents')
                with ui.input('Adresse').classes('flex-1'):
                    ui.tooltip('Adresse de l\'entreprise')
            with ui.row().classes('w-full gap-4 mb-3'):
                with ui.input('Téléphone').classes('flex-1'):
                    ui.tooltip('Numéro de téléphone de l\'entreprise')
                with ui.input('Email').classes('flex-1'):
                    ui.tooltip('Adresse email de contact')
            with ui.row().classes('w-full gap-4 mb-3'):
                with ui.input('TVA (%)').classes('w-48'):
                    ui.tooltip('Taux de TVA par défaut')
                with ui.select(options=['EUR', 'USD', 'FCFA'], label='Devise').classes('w-48'):
                    ui.tooltip('Devise utilisée dans l\'application')
            ui.button('Enregistrer paramètres généraux', icon='save', color='blue').classes('bg-blue-600 hover:bg-blue-700 mt-2')
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Gestion des utilisateurs').classes('text-xl font-semibold text-gray-700 mb-4')
            ui.button('Ajouter un utilisateur', icon='person_add', color='green').classes('bg-green-600 hover:bg-green-700 mb-3')
            
            table = ui.table(
                columns=[
                    {'name': 'username', 'label': 'Nom d\'utilisateur', 'field': 'username', 'align': 'left'},
                    {'name': 'full_name', 'label': 'Nom complet', 'field': 'full_name', 'align': 'left'},
                    {'name': 'role', 'label': 'Rôle', 'field': 'role', 'align': 'center'},
                    {'name': 'is_active', 'label': 'Actif', 'field': 'is_active', 'align': 'center'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
                ],
                rows=[],
                row_key='id'
            ).classes('w-full')
            
            for user in users:
                is_active_icon = 'check_circle' if user.is_active else 'cancel'
                is_active_color = 'text-green-600' if user.is_active else 'text-red-600'
                table.rows.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'role': user.role.value,
                    'is_active': f'<span class="{is_active_color} material-icons">{is_active_icon}</span>'
                })
            table.update()
        
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('Sauvegardes et restauration').classes('text-xl font-semibold text-gray-700 mb-4')
            ui.label(f'Dossier de sauvegarde: {DATA_DIR / "backups"}').classes('text-sm text-gray-500 mb-3')
            with ui.row().classes('w-full gap-4 mb-3'):
                ui.button('Créer une sauvegarde', icon='backup', color='purple').classes('bg-purple-600 hover:bg-purple-700')
                ui.button('Restaurer une sauvegarde', icon='restore', color='orange').classes('bg-orange-600 hover:bg-orange-700')
                ui.button('Exporter les données', icon='download', color='teal').classes('bg-teal-600 hover:bg-teal-700')
        
        with ui.card().classes('w-full p-4'):
            ui.label('Informations système').classes('text-xl font-semibold text-gray-700 mb-4')
            with ui.column().classes('gap-2 text-sm text-gray-600'):
                ui.label(f'Version DEPOTPRO: 1.0.0')
                ui.label(f'Base de données: SQLite')
                ui.label(f'Dossier de données: {DATA_DIR}')
                ui.label(f'Dernière sauvegarde: {backup_service.get_last_backup_date() or "Jamais"}')