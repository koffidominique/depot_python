from nicegui import ui


def create_sidebar(on_navigate, current_page='dashboard'):
    # Les écrans métier historiques sont conservés dans pages/, mais ne sont pas
    # exposés tant que leurs opérations ne sont pas sûres et testées.
    items = [('dashboard', 'Tableau de bord', 'dashboard'),
             ('products', 'Produits', 'inventory_2'),
             ('stock', 'Stocks et inventaires', 'warehouse'),
             ('returnables', 'Emballages consignés', 'inventory'),
             ('purchases', 'Approvisionnements', 'local_shipping'),
             ('sales', 'Ventes au comptant', 'shopping_cart'),
             ('cash', 'Caisse et trésorerie', 'point_of_sale'),
             ('settings', 'Paramètres et sécurité', 'settings')]
    with ui.column().classes('w-64 h-full bg-slate-900 text-white p-4 gap-2'):
        ui.label('DEPOTPRO').classes('text-xl font-bold mb-6')
        for page, label, icon in items:
            button = ui.button(label, icon=icon, on_click=lambda p=page: on_navigate(p)).classes('w-full')
            if current_page == page:
                button.props('color=primary')
        ui.element('div').classes('flex-grow')
        ui.label('Mode local').classes('text-xs text-slate-400')
