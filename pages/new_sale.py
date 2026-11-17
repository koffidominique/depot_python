from nicegui import ui
from sqlalchemy.orm import Session
from services.sales_service import SalesService
from services.client_service import ClientService
from services.product_service import ProductService
from enums import SaleStatus, PaymentMethod
from datetime import datetime


def create_new_sale_page(db: Session, on_sale_complete=None):
    sales_service = SalesService(db)
    client_service = ClientService(db)
    product_service = ProductService(db)
    
    cart_items = []
    selected_client_id = {'value': None}
    payment_method = {'value': PaymentMethod.CASH}
    payment_amount = {'value': 0}
    total_amount = {'value': 0}
    consignment_total = {'value': 0}
    
    clients = client_service.get_all_clients()
    products = product_service.get_all_products()
    
    def update_total():
        total = sum(item['total'] for item in cart_items)
        cons_total = sum(item['consignment'] * item['quantity'] for item in cart_items)
        total_amount['value'] = total + cons_total
        consignment_total['value'] = cons_total
        payment_amount['value'] = total_amount['value']
        total_label.text = f"{total_amount['value']:,.0f} FCFA"
        consignment_label.text = f"{consignment_total['value']:,.0f} FCFA"
        payment_input.value = payment_amount['value']
    
    def add_product_to_cart(product):
        existing_item = next((item for item in cart_items if item['product_id'] == product.id), None)
        if existing_item:
            existing_item['quantity'] += 1
            existing_item['total'] = existing_item['quantity'] * existing_item['unit_price']
        else:
            cart_item = {
                'product_id': product.id,
                'product_name': product.name,
                'quantity': 1,
                'unit_price': product.sale_price or 0,
                'consignment': product.consignment or 0,
                'total': product.sale_price or 0
            }
            cart_items.append(cart_item)
        update_total()
        cart_table.update()
    
    def remove_cart_item(index):
        del cart_items[index]
        update_total()
        cart_table.update()
    
    def update_cart_item_quantity(index, new_quantity):
        if new_quantity > 0:
            cart_items[index]['quantity'] = new_quantity
            cart_items[index]['total'] = cart_items[index]['quantity'] * cart_items[index]['unit_price']
            update_total()
            cart_table.update()
    
    async def confirm_sale():
        if not cart_items:
            ui.notify('Veuillez ajouter des produits au panier', type='warning')
            return
        
        sale_data = {
            'client_id': selected_client_id['value'],
            'date': datetime.now(),
            'status': SaleStatus.COMPLETED,
            'payment_method': payment_method['value'],
            'payment_amount': payment_amount['value'],
            'items': cart_items.copy()
        }
        
        try:
            sale = sales_service.create_sale(sale_data)
            ui.notify(f'Vente n°{sale.reference} enregistrée avec succès', type='success')
            clear_cart()
            if on_sale_complete:
                await on_sale_complete()
        except Exception as e:
            ui.notify(f'Erreur lors de la vente: {str(e)}', type='error')
    
    def clear_cart():
        cart_items.clear()
        selected_client_id['value'] = None
        payment_amount['value'] = 0
        total_amount['value'] = 0
        consignment_total['value'] = 0
        update_total()
        cart_table.update()
        client_select.value = None
    
    def get_client_options():
        return [{'label': c.name, 'value': c.id} for c in clients]
    
    def get_product_options():
        return [{'label': p.name, 'value': p.id} for p in products]
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Nouvelle vente').classes('text-2xl font-bold text-gray-800')
        
        with ui.row().classes('w-full gap-4'):
            with ui.column().classes('w-1/2 gap-4'):
                with ui.card().classes('p-4'):
                    ui.label('Informations client').classes('text-lg font-semibold mb-2')
                    client_select = ui.select(
                        options=get_client_options(),
                        label='Client',
                        clearable=True
                    ).classes('w-full')
                    client_select.on('update:model-value', lambda e: selected_client_id.update({'value': e.args}))
                
                with ui.card().classes('p-4'):
                    ui.label('Recherche de produits').classes('text-lg font-semibold mb-2')
                    search_input = ui.input('Rechercher un produit...').classes('w-full')
                    
                    product_grid = ui.grid(columns=3).classes('w-full gap-2 mt-4 max-h-64 overflow-auto')
                    
                    for product in products:
                        with product_grid:
                            ui.button(
                                product.name,
                                on_click=lambda p=product: add_product_to_cart(p)
                            ).classes('w-full p-2 text-left text-sm')
            
            with ui.column().classes('w-1/2 gap-4'):
                with ui.card().classes('p-4'):
                    ui.label('Panier').classes('text-lg font-semibold mb-2')
                    
                    cart_table = ui.table(
                        columns=[
                            {'name': 'product', 'label': 'Produit', 'field': 'product_name', 'align': 'left'},
                            {'name': 'quantity', 'label': 'Qté', 'field': 'quantity', 'align': 'center'},
                            {'name': 'price', 'label': 'Prix', 'field': 'unit_price', 'align': 'right'},
                            {'name': 'total', 'label': 'Total', 'field': 'total', 'align': 'right'},
                            {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'center'}
                        ],
                        rows=[],
                        row_key='index'
                    ).classes('w-full max-h-48 overflow-auto')
                    
                    with ui.row().classes('w-full justify-between mt-4'):
                        ui.label('Total marchandises:').classes('font-medium')
                        total_label = ui.label('0 FCFA').classes('font-bold')
                    
                    with ui.row().classes('w-full justify-between mt-2'):
                        ui.label('Total consignes:').classes('font-medium')
                        consignment_label = ui.label('0 FCFA').classes('font-bold')
                
                with ui.card().classes('p-4'):
                    ui.label('Paiement').classes('text-lg font-semibold mb-2')
                    
                    payment_select = ui.select(
                        options=[pm.value for pm in PaymentMethod],
                        label='Mode de paiement',
                        value=payment_method['value'].value
                    ).classes('w-full mb-4')
                    payment_select.on('update:model-value', lambda e: payment_method.update({'value': PaymentMethod(e.args)}))
                    
                    payment_input = ui.number(
                        'Montant reçu',
                        value=payment_amount['value'],
                        min=0
                    ).classes('w-full mb-4')
                    payment_input.on('update:model-value', lambda e: payment_amount.update({'value': e.args}))
                    
                    with ui.row().classes('w-full gap-2 mt-4'):
                        ui.button('Annuler', color='gray', on_click=clear_cart).classes('flex-1')
                        ui.button('Confirmer la vente', color='green', on_click=confirm_sale).classes('flex-1')