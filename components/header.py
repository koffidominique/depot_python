from nicegui import ui
from datetime import datetime

def create_header(page_title: str = "Tableau de bord", user_name: str = "Utilisateur"):
    with ui.row().classes('w-full h-16 bg-white border-b border-slate-200 px-6 items-center justify-between'):
        with ui.row().classes('items-center gap-4'):
            ui.label(page_title).classes('text-xl font-semibold text-slate-900')
            ui.label(f"/ {page_title}").classes('text-sm text-slate-500')
        
        with ui.row().classes('items-center gap-4'):
            ui.label(datetime.now().strftime("%d/%m/%Y")).classes('text-sm text-slate-600')
            ui.label(user_name).classes('text-sm font-medium text-slate-900')
            ui.button('Nouvelle vente', icon='add_shopping_cart', color='primary').classes('px-4 py-2')