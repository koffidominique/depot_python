from nicegui import ui
from sqlalchemy.orm import Session
from services.stock_service import StockService
from services.product_service import ProductService

def create_stock_page(db: Session):
    stock_service = StockService(db)
    product_service = ProductService(db)
    
    all_products = product_service.get_all_products()
    low_stock = stock_service.get_low_stock_products()
    out_of_stock = stock_service.get_out_of_stock_products()
    total_stock_value = stock_service.get_total_stock_value()
    
    stock_list = [
        {
            'reference': p.reference,
            'name': p.name,
            'category': p.category.name if p.category else 'N/A',
            'stock': float(p.stock_quantity),
            'min_stock': float(p.min_stock),
            'stock_status': 'OK' if p.stock_quantity > p.min_stock else 'Alerte' if p.stock_quantity > 0 else 'Rupture',
            'value': float(p.stock_quantity * p.purchase_price)
        } for p in all_products
    ]
    
    with ui.column().classes('w-full gap-6 p-6'):
        ui.label('Gestion des stocks').classes('text-2xl font-bold text-slate-900')
        
        with ui.row().classes('w-full gap-4 grid grid-cols-3'):
            with ui.card().classes('p-4'):
                ui.label('Valeur totale du stock').classes('text-sm text-slate-500')
                ui.label(f"{total_stock_value:,.0f} FCFA").classes('text-2xl font-bold text-slate-900')
            
            with ui.card().classes('p-4'):
                ui.label('Produits en alerte').classes('text-sm text-slate-500')
                ui.label(f"{len(low_stock)}").classes('text-2xl font-bold text-orange-600')
            
            with ui.card().classes('p-4'):
                ui.label('Produits en rupture').classes('text-sm text-slate-500')
                ui.label(f"{len(out_of_stock)}").classes('text-2xl font-bold text-red-600')
        
        with ui.row().classes('w-full gap-4 justify-between'):
            ui.input('Rechercher un produit').props('placeholder="Nom, référence..."').classes('flex-1 max-w-md')
            ui.row().classes('gap-2')
            ui.button('Ajustement de stock', icon='edit', color='secondary').classes('px-4 py-2')
            ui.button('Inventaire', icon='fact_check', color='primary').classes('px-4 py-2')
        
        with ui.card().classes('p-4'):
            if stock_list:
                with ui.table(rows=stock_list, columns=[
                    {'name': 'reference', 'label': 'Référence', 'field': 'reference'},
                    {'name': 'name', 'label': 'Nom', 'field': 'name'},
                    {'name': 'category', 'label': 'Catégorie', 'field': 'category'},
                    {'name': 'stock', 'label': 'Stock actuel', 'field': 'stock'},
                    {'name': 'min_stock', 'label': 'Stock minimum', 'field': 'min_stock'},
                    {'name': 'stock_status', 'label': 'Statut', 'field': 'stock_status'},
                    {'name': 'value', 'label': 'Valeur', 'field': 'value'},
                    {'name': 'actions', 'label': 'Actions', 'field': 'actions'}
                ]).classes('w-full'):
                    pass
            else:
                ui.label('Aucun produit trouvé').classes('text-slate-500')