from nicegui import ui
from sqlalchemy.orm import Session
from services.product_service import ProductService

def create_products_page(db: Session):
    product_service = ProductService(db)
    products = product_service.get_all_products()
    categories = product_service.get_all_categories()
    
    search_query = {'value': ''}
    selected_category = {'value': None}
    
    def filter_products():
        filtered = products
        if search_query['value']:
            filtered = [p for p in filtered if search_query['value'].lower() in p.name.lower()]
        if selected_category['value']:
            filtered = [p for p in filtered if p.category_id == selected_category['value']]
        return filtered
    
    def refresh_table():
        filtered = filter_products()
        table.rows = [
            {
                'reference': p.reference,
                'name': p.name,
                'category': p.category.name if p.category else '',
                'stock': float(p.stock_quantity),
                'price': float(p.retail_price),
                'status': 'Actif' if p.is_active else 'Inactif'
            } for p in filtered
        ]
        table.update()
    
    with ui.column().classes('w-full gap-6 p-6'):
        ui.label('Gestion des produits').classes('text-2xl font-bold')
        
        with ui.row().classes('w-full gap-4 items-center'):
            search_input = ui.input(placeholder='Rechercher un produit...', on_change=lambda e: (setattr(search_query, 'value', e.value), refresh_table())).classes('w-64')
            
            category_options = [('Toutes les catégories', None)] + [(c.name, c.id) for c in categories]
            category_select = ui.select(options=category_options, value=None, on_change=lambda e: (setattr(selected_category, 'value', e.value), refresh_table())).classes('w-48')
            
            ui.button('Ajouter un produit', icon='add', color='primary').classes('ml-auto')
        
        table_columns = [
            {'name': 'reference', 'label': 'Référence', 'field': 'reference'},
            {'name': 'name', 'label': 'Nom', 'field': 'name'},
            {'name': 'category', 'label': 'Catégorie', 'field': 'category'},
            {'name': 'stock', 'label': 'Stock', 'field': 'stock'},
            {'name': 'price', 'label': 'Prix détail', 'field': 'price'},
            {'name': 'status', 'label': 'Statut', 'field': 'status'},
            {'name': 'actions', 'label': 'Actions', 'field': 'actions'}
        ]
        
        initial_rows = [
            {
                'reference': p.reference,
                'name': p.name,
                'category': p.category.name if p.category else '',
                'stock': float(p.stock_quantity),
                'price': float(p.retail_price),
                'status': 'Actif' if p.is_active else 'Inactif'
            } for p in products
        ]
        
        table = ui.table(rows=initial_rows, columns=table_columns, pagination=15).classes('w-full')