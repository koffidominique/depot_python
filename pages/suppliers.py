from nicegui import ui
from sqlalchemy.orm import Session
from services.supplier_service import SupplierService


def create_suppliers_page(db: Session):
    supplier_service = SupplierService(db)
    suppliers = supplier_service.get_all_suppliers()
    
    search_query = {'value': ''}
    
    def filter_suppliers():
        filtered = suppliers
        if search_query['value']:
            filtered = [s for s in filtered if search_query['value'].lower() in s.name.lower() or 
                      (s.phone and search_query['value'] in s.phone)]
        return filtered
    
    def refresh_table():
        filtered = filter_suppliers()
        table.rows = []
        for supplier in filtered:
            debt = supplier_service.get_supplier_debt(supplier.id)
            debt_class = 'text-red-600' if debt > 0 else 'text-green-600'
            table.rows.append({
                'id': supplier.id,
                'name': supplier.name,
                'phone': supplier.phone or '-',
                'email': supplier.email or '-',
                'debt': f"{debt:,.0f} FCFA",
                'debt_class': debt_class,
                'created': supplier.created_at.strftime('%d/%m/%Y')
            })
        table.update()
    
    with ui.column().classes('w-full gap-4 p-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('Gestion des fournisseurs').classes('text-2xl font-bold text-gray-800')
            ui.button('Nouveau fournisseur', icon='add', color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.row().classes('w-full gap-4 mb-4'):
            with ui.card().classes('flex-1 p-4'):
                total_suppliers = len(suppliers)
                ui.label(f"{total_suppliers}").classes('text-2xl font-bold text-purple-600')
                ui.label('Nombre de fournisseurs').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                total_debt = sum(supplier_service.get_supplier_debt(s.id) for s in suppliers)
                ui.label(f"{total_debt:,.0f} FCFA").classes('text-2xl font-bold text-red-600')
                ui.label('Dette totale aux fournisseurs').classes('text-sm text-gray-500')
            
            with ui.card().classes('flex-1 p-4'):
                active_suppliers = [s for s in suppliers if s.is_active]
                ui.label(f"{len(active_suppliers)}").classes('text-2xl font-bold text-green-600')
                ui.label('Fournisseurs actifs').classes('text-sm text-gray-500')
        
        with ui.row().classes('w-full mb-4'):
            with ui.input('Rechercher un fournisseur').props('placeholder=Nom, téléphone...').classes('flex-1') as search_input:
                search_query['value'] = search_input.value
                search_input.on('update:model-value', lambda e: (search_query.update({'value': e.args}), refresh_table()))
        
        table = ui.table(
            columns=[
                {'name': 'name', 'label': 'Nom', 'field': 'name', 'align': 'left'},
                {'name': 'phone', 'label': 'Téléphone', 'field': 'phone', 'align': 'left'},
                {'name': 'email', 'label': 'Email', 'field': 'email', 'align': 'left'},
                {'name': 'debt', 'label': 'Dette', 'field': 'debt', 'align': 'right'},
                {'name': 'created', 'label': 'Créé le', 'field': 'created', 'align': 'left'},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'center'}
            ],
            rows=[],
            row_key='id'
        ).classes('w-full')
        
        refresh_table()