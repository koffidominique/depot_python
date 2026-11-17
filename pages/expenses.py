from nicegui import ui
from sqlalchemy.orm import Session
from services.expense_service import ExpenseService
from datetime import datetime, timedelta


def create_expenses_page(db: Session):
    expense_service = ExpenseService(db)
    
    search_query = {'value': ''}
    date_range = {'start': datetime.now() - timedelta(days=30), 'end': datetime.now()}
    
    def filter_expenses():
        expenses = expense_service.get_expenses_by_date_range(date_range['start'], date_range['end'])
        filtered = expenses
        if search_query['value']:
            filtered = [e for e in filtered if search_query['value'].lower() in e.description.lower()]
        return filtered
    
    def refresh_table():
        filtered = filter_expenses()
        table.rows = []
        total_expenses = 0
        for expense in filtered:
            total_expenses += expense.amount
            table.rows.append({
                'id': expense.id,
                'description': expense.description,
                'amount': f"{expense.amount:,.0f} FCFA",
                'category': expense.category,
                'date': expense.expense_date.strftime('%d/%m/%Y'),
                'created': expense.created_at.strftime('%d/%m/%Y')
            })
        total_label.text = f"{total_expenses:,.0f} FCFA"
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Gestion des dépenses').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full justify-between items-center mb-4'):
            ui.button('Nouvelle dépense', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_label = ui.label('0 FCFA').classes('text-2xl font-bold text-red-600')
                ui.label('Total des dépenses').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                expense_count = len(filter_expenses())
                ui.label(f"{expense_count}").classes('text-2xl font-bold text-orange-600')
                ui.label('Nombre de dépenses').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                avg_expense = total_label.value / expense_count if expense_count > 0 else 0
                ui.label(f"{avg_expense:,.0f} FCFA").classes('text-2xl font-bold text-blue-600')
                ui.label('Dépense moyenne').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.input('Rechercher une dépense').props('placeholder=Description...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
            
            ui.button('Actualiser', on_click=refresh_table).classes('ml-2')
        
        table = ui.table(
            columns=[
                {'name': 'description', 'label': 'Description', 'field': 'description', 'align': 'left'},
                {'name': 'amount', 'label': 'Montant', 'field': 'amount', 'align': 'right'},
                {'name': 'category', 'label': 'Catégorie', 'field': 'category', 'align': 'left'},
                {'name': 'date', 'label': 'Date', 'field': 'date', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()