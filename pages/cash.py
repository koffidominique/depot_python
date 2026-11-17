from nicegui import ui
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from services.stock_service import StockService
from services.sales_service import SalesService
from services.purchase_service import PurchaseService


def create_cash_page(db: Session):
    stock_service = StockService(db)
    sales_service = SalesService(db)
    purchase_service = PurchaseService(db)
    
    today = datetime.now().date()
    opening_balance = stock_service.get_cash_balance(today)
    sales_today = sales_service.get_sales_by_date(today)
    total_sales_today = sum(s.total_amount for s in sales_today)
    purchases_today = purchase_service.get_purchases_by_date(today)
    total_purchases_today = sum(p.total_amount for p in purchases_today)
    closing_balance = opening_balance + total_sales_today - total_purchases_today
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion de la caisse').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{opening_balance:,.0f} FCFA").classes('text-2xl font-bold text-blue-600')
                ui.label('Solde d\'ouverture').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{total_sales_today:,.0f} FCFA").classes('text-2xl font-bold text-green-600')
                ui.label('Ventes du jour').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{total_purchases_today:,.0f} FCFA").classes('text-2xl font-bold text-red-600')
                ui.label('Achats du jour').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                ui.label(f"{closing_balance:,.0f} FCFA").classes('text-2xl font-bold text-purple-600')
                ui.label('Solde de clôture').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            ui.button('Ouvrir caisse', icon='lock_open', color='green').classes('bg-green-600 hover:bg-green-700')
            ui.button('Fermer caisse', icon='lock', color='red').classes('bg-red-600 hover:bg-red-700')
            ui.button('Ajouter dépense', icon='add_circle', color='orange').classes('bg-orange-600 hover:bg-orange-700')
            ui.button('Ajouter recette', icon='add_circle_outline', color='teal').classes('bg-teal-600 hover:bg-teal-700')
        
        ui.label('Mouvements de caisse du jour').classes('text-xl font-semibold text-gray-700 mb-2')
        
        table = ui.table(
            columns=[
                {'name': 'date', 'label': 'Heure', 'field': 'date', 'align': 'left'},
                {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'left'},
                {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
                {'name': 'amount', 'label': 'Montant', 'field': 'amount', 'align': 'right'},
                {'name': 'balance', 'label': 'Solde', 'field': 'balance', 'align': 'right'}
            ],
            rows=[
                {'date': '08:00', 'type': 'Ouverture', 'description': 'Solde initial', 'amount': f"{opening_balance:,.0f} FCFA", 'balance': f"{opening_balance:,.0f} FCFA"}
            ],
            row_key='id'
        ).classes('w-full')