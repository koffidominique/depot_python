"""Consultation des stocks et inventaires physiques."""
from nicegui import ui
from models.inventory import Inventory
from models.product import Product
from services.inventory_service import InventoryService
from services.stock_adjustment_service import StockAdjustmentService
from services.stock_service import StockService


INVENTORY_STATUS = {'draft': 'Brouillon', 'validated': 'Validé', 'cancelled': 'Annulé'}
MOVEMENT_NAMES = {'initial_stock': 'Stock initial', 'purchase_reception': 'Réception achat',
                  'inventory_adjustment': 'Régularisation inventaire', 'breakage': 'Casse',
                  'loss': 'Perte', 'supplier_return': 'Retour fournisseur', 'customer_return': 'Retour client',
                  'correction_in': 'Correction entrée', 'correction_out': 'Correction sortie',
                  'unit_declaration': 'Déclaration unité'}


def create_stock_page(db, refresh_page):
    inventories = InventoryService(db)
    stock = StockService(db)

    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    products = db.query(Product).filter_by(is_active=True).order_by(Product.name).all()
    choices = {p.id: f'{p.name} — {p.stock_quantity} {p.unit}' for p in products}
    ui.label('Stocks et inventaires').classes('text-2xl font-bold')
    ui.label('Les quantités sont exprimées dans l’unité de base.').classes('text-slate-600')
    try:
        ui.label(f'Valorisation au coût moyen : {stock.get_total_stock_value()} FCFA')
    except ValueError as exc:
        ui.label(f'Valorisation indisponible : {exc}')
    with ui.expansion('État et alertes de stock', icon='warning').classes('w-full'):
        if not products:
            ui.label('Aucun produit actif.')
        for product in products:
            if product.stock_quantity is None or product.stock_quantity < 0 or product.min_stock is None or product.min_stock < 0:
                label = 'Quantité ou seuil incohérent'
            elif product.stock_quantity == 0:
                label = 'Rupture'
            else:
                label = 'Stock faible' if product.stock_quantity <= product.min_stock else 'Normal'
            ui.label(f'{product.name} : {product.stock_quantity} {product.unit} — {label}')
        inactive = db.query(Product).filter_by(is_active=False).count()
        ui.label(f'Produits inactifs : {inactive}')

    def adjust_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Correction manuelle').classes('text-lg font-bold')
            product = ui.select(choices, label='Produit')
            kind = ui.select({'breakage': 'Casse', 'loss': 'Perte', 'supplier_return': 'Retour fournisseur',
                              'customer_return': 'Retour client', 'correction_in': 'Correction entrée',
                              'correction_out': 'Correction sortie'}, label='Type')
            amount = ui.input('Quantité en unité de base')
            reason = ui.input('Motif obligatoire')
            ui.label('Une entrée sans coût fiable rend la valorisation de ce produit indisponible.')
            def save():
                def action():
                    StockAdjustmentService(db).adjust(product.value, kind.value, amount.value, reason.value)
                    dialog.close()
                    refresh_page()
                    ui.notify('Correction enregistrée.', type='positive')
                run(action)
            ui.button('Enregistrer correction', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    ui.button('Correction de stock', on_click=adjust_dialog)
    with ui.expansion('Historique des mouvements (100 derniers)', icon='history').classes('w-full'):
        for movement in stock.get_stock_movements(limit=100):
            product_name = movement.product.name if movement.product else f'#{movement.product_id}'
            ui.label(f'{movement.date} — {product_name} — {MOVEMENT_NAMES.get(movement.movement_type, movement.movement_type)} : {movement.quantity} {movement.unit} '
                     f'({movement.stock_before} → {movement.stock_after}) — {movement.reference_document or ""} {movement.reason or ""}')

    def start_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
            ui.label('Démarrer un inventaire').classes('text-lg font-bold')
            selected = ui.select(choices, label='Produits à compter', multiple=True).classes('w-full')
            notes = ui.input('Notes facultatives')
            def start():
                def action():
                    inventories.start(selected.value or [], notes.value)
                    dialog.close()
                    refresh_page()
                    ui.notify('Inventaire démarré.', type='positive')
                run(action)
            ui.button('Démarrer', on_click=start)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    ui.button('Nouvel inventaire', on_click=start_dialog)
    ui.label('Inventaires').classes('text-xl font-semibold')
    records = db.query(Inventory).order_by(Inventory.created_at.desc(), Inventory.id.desc()).limit(100).all()
    if not records:
        ui.label('Aucun inventaire.')

    def inventory_dialog(inventory_id):
        def action():
            inv = db.get(Inventory, inventory_id)
            if not inv:
                raise ValueError('Inventaire introuvable.')
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
                ui.label(f'{inv.reference} — {INVENTORY_STATUS.get(inv.status, inv.status)}').classes('text-lg font-bold')
                ui.label('Renseignez les quantités physiques et les motifs avant validation.')
                fields = []
                for line in inv.lines:
                    with ui.row().classes('items-center w-full'):
                        ui.label(f'{line.product.name} — théorique : {line.theoretical_quantity} {line.product.unit}')
                        count = ui.input('Stock physique', value=str(line.counted_quantity) if line.counted_quantity is not None else '').props('dense')
                        reason = ui.input('Motif de l’écart', value=line.reason or '').props('dense')
                        if line.counted_quantity is not None:
                            ui.label(f'Écart enregistré : {line.counted_quantity - line.theoretical_quantity}')
                        fields.append((line.id, count, reason))
                if inv.status == 'draft':
                    def save():
                        def do_save():
                            inventories.save_counts(inv.id, [{'line_id': ident, 'counted_quantity': count.value, 'reason': reason.value}
                                                              for ident, count, reason in fields])
                            dialog.close()
                            refresh_page()
                            ui.notify('Comptage enregistré. Rouvrez l’inventaire pour vérifier les écarts.', type='positive')
                        run(do_save)
                    def confirm_validate():
                        with ui.dialog() as confirm, ui.card():
                            ui.label('Valider les comptages enregistrés et créer les mouvements de correction ?')
                            ui.label('Les modifications non enregistrées ne sont pas prises en compte.')
                            def validate():
                                def do_validate():
                                    inventories.validate(inv.id)
                                    confirm.close()
                                    dialog.close()
                                    refresh_page()
                                    ui.notify('Inventaire validé.', type='positive')
                                run(do_validate)
                            ui.button('Confirmer validation', on_click=validate)
                            ui.button('Retour', on_click=confirm.close)
                        confirm.open()
                    def cancel():
                        def do_cancel():
                            inventories.cancel(inv.id)
                            dialog.close()
                            refresh_page()
                            ui.notify('Inventaire annulé.', type='positive')
                        run(do_cancel)
                    ui.button('Enregistrer comptage', on_click=save)
                    ui.button('Valider inventaire', on_click=confirm_validate)
                    ui.button('Annuler inventaire', on_click=cancel)
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        run(action)

    for record in records:
        with ui.row().classes('items-center'):
            ui.label(f'{record.reference} — {record.created_at} — {INVENTORY_STATUS.get(record.status, record.status)}')
            ui.button('Ouvrir inventaire', on_click=lambda ident=record.id: inventory_dialog(ident))
