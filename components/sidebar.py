from nicegui import ui
from typing import Callable

def create_sidebar(on_navigate: Callable[[str], None], current_page: str = 'dashboard'):
    menu_items = [
        {'id': 'dashboard', 'label': 'Tableau de bord', 'icon': 'dashboard'},
        {'id': 'sales', 'label': 'Ventes', 'icon': 'shopping_cart'},
        {'id': 'new_sale', 'label': 'Nouvelle vente', 'icon': 'add_shopping_cart'},
        {'id': 'products', 'label': 'Produits', 'icon': 'inventory_2'},
        {'id': 'stock', 'label': 'Stocks', 'icon': 'warehouse'},
        {'id': 'purchases', 'label': 'Achats', 'icon': 'shopping_bag'},
        {'id': 'suppliers', 'label': 'Fournisseurs', 'icon': 'business'},
        {'id': 'clients', 'label': 'Clients', 'icon': 'people'},
        {'id': 'deliveries', 'label': 'Livraisons', 'icon': 'local_shipping'},
        {'id': 'debts', 'label': 'Créances & Dettes', 'icon': 'payments'},
        {'id': 'consignations', 'label': 'Consignations', 'icon': 'package'},
        {'id': 'cash', 'label': 'Caisse', 'icon': 'point_of_sale'},
        {'id': 'expenses', 'label': 'Dépenses', 'icon': 'receipt_long'},
        {'id': 'inventory', 'label': 'Inventaires', 'icon': 'fact_check'},
        {'id': 'reports', 'label': 'Rapports', 'icon': 'bar_chart'},
        {'id': 'users', 'label': 'Utilisateurs', 'icon': 'manage_accounts'},
        {'id': 'settings', 'label': 'Paramètres', 'icon': 'settings'},
        {'id': 'advanced_settings', 'label': 'Paramètres avancés', 'icon': 'lock'}
    ]
    
    with ui.column().classes('w-64 h-full bg-slate-900 text-white p-4 gap-2'):
        ui.label('DEPOTPRO').classes('text-xl font-bold mb-6')
        
        for item in menu_items:
            is_active = item['id'] == current_page
            button_classes = 'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all '
            if is_active:
                button_classes += 'bg-blue-600 text-white'
            else:
                button_classes += 'hover:bg-slate-800 text-slate-300'
            
            ui.button(icon=item['icon'], on_click=lambda item_id=item['id']: on_navigate(item_id)) \
                .classes(button_classes) \
                .props(f'label="{item["label"]}"')
        
        ui.spacer()
        
        ui.label('Mode hors ligne').classes('text-xs text-slate-400 mt-auto')