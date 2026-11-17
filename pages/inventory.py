from nicegui import ui
from sqlalchemy.orm import Session
from services.product_service import ProductService
from services.stock_service import StockService
from datetime import datetime, timedelta


def create_inventory_page(db: Session):
    product_service = ProductService(db)
    stock_service = StockService(db)
    
    search_query = {'value': ''}
    
    def filter_products():
        products = product_service.get_all_products()
        filtered = products
        if search_query['value']:
            filtered = [p for p in filtered if search_query['value'].lower() in p.name.lower()]
        return filtered
    
    def refresh_table():
        filtered = filter_products()
        table.rows = []
        total_products = len(filtered)
        total_value = sum(p.quantity * p.purchase_price for p in filtered if p.purchase_price)
        for product in filtered:
            stock_status = 'En stock' if product.stock_quantity > 0 else 'Rupture'
            status_class = 'text-green-600' if product.stock_quantity > 0 else 'text-red-600'
            table.rows.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku or '-',
                'quantity': product.stock_quantity,
                'unit_price': f"{product.sale_price:,.0f} FCFA" if product.sale_price else '-',
                'stock_status': stock_status,
                'status_class': status_class,
                'last_updated': product.updated_at.strftime('%d/%m/%Y %H:%M')
            })
        total_products_label.text = f"{total_products}"
        total_value_label.text = f"{total_value:,.0f} FCFA"
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion des inventaires').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.button('Nouvel inventaire', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_products_label = ui.label('0').classes('text-2xl font-bold text-purple-600')
                ui.label('Nombre de produits').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                total_value_label = ui.label('0 FCFA').classes('text-2xl font-bold text-blue-600')
                ui.label('Valeur totale du stock').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                out_of_stock = len([p for p in filter_products() if p.quantity == 0])
                ui.label(f"{out_of_stock}").classes('text-2xl font-bold text-red-600')
                ui.label('Produits en rupture').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher un produit').props('placeholder=Nom, SKU...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            ui.button('Actualiser', on_click=refresh_table).classes('ml-2')
        
        table = ui.table(
            columns=[
                {'name': 'name', 'label': 'Produit', 'field': 'name', 'align': 'left'},
                {'name': 'sku', 'label': 'SKU', 'field': 'sku', 'align': 'left'},
                {'name': 'quantity', 'label': 'Qté', 'field': 'quantity', 'align': 'center'},
                {'name': 'unit_price', 'label': 'Prix unitaire', 'field': 'unit_price', 'align': 'right'},
                {'name': 'stock_status', 'label': 'Statut', 'field': 'stock_status', 'align': 'center'},
                {'name': 'last_updated', 'label': 'Dernière mise à jour', 'field': 'last_updated', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()