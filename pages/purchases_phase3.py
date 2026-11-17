"""Approvisionnements et règlements liés à la caisse fournisseur."""
from uuid import uuid4
from nicegui import ui
from models.debt import SupplierDebt
from models.packaging import ProductPackaging
from models.purchase import PurchaseOrder
from models.reception import PurchaseReceipt
from models.supplier import Supplier
from services.purchase_service import PurchaseService, SupplierPaymentService
from services.managed_cash_service import ManagedCashService
from services.supplier_phase3_service import SupplierPhase3Service
from services.cash_methods import METHODS


STATUS = {'draft': 'Brouillon', 'validated': 'Validée', 'partially_received': 'Partiellement réceptionnée',
          'received': 'Réceptionnée', 'cancelled': 'Annulée'}


def create_purchases_page(db, refresh_page):
    service = PurchaseService(db)
    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    ui.label('Approvisionnements').classes('text-2xl font-bold')
    ui.label('Les nouveaux règlements exigent une caisse ouverte. Les anciens règlements hors caisse restent inchangés.').classes('text-orange-800')
    ui.label('Les dettes et réceptions historiques non rapprochées restent en lecture seule.').classes('text-orange-800')

    def supplier_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Nouveau fournisseur').classes('text-lg font-bold')
            name, phone = ui.input('Nom fournisseur'), ui.input('Téléphone fournisseur')
            def save():
                def action():
                    SupplierPhase3Service(db).create(name.value, phone.value)
                    dialog.close(); refresh_page(); ui.notify('Fournisseur enregistré.', type='positive')
                run(action)
            ui.button('Enregistrer fournisseur', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    ui.button('Nouveau fournisseur', on_click=supplier_dialog)
    suppliers = db.query(Supplier).filter_by(is_active=True).order_by(Supplier.name).all()
    supplier_options = {s.id: f'{s.name} ({s.code})' for s in suppliers}
    packages = db.query(ProductPackaging).join(ProductPackaging.product).filter(
        ProductPackaging.is_active.is_(True), ProductPackaging.product.has(is_active=True)).all()
    package_options = {p.id: f'{p.product.name} — {p.name} ({p.coefficient} {p.base_unit})' for p in packages}

    def order_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl'):
            ui.label('Nouvelle commande').classes('text-lg font-bold')
            supplier = ui.select(supplier_options, label='Fournisseur').classes('w-full')
            reference = ui.input('Référence facultative')
            order_date = ui.input('Date commande facultative (AAAA-MM-JJ)')
            expected = ui.input('Date prévue facultative (AAAA-MM-JJ)')
            notes = ui.input('Notes commande facultatives')
            package = ui.select(package_options, label='Conditionnement').classes('w-full')
            count = ui.input('Quantité commandée')
            price = ui.input('Prix par conditionnement FCFA')
            discount = ui.input('Remise par conditionnement FCFA', value='0')
            fee = ui.input('Frais par conditionnement FCFA', value='0')
            ui.label('Remise et frais sont saisis par conditionnement et répartis uniquement selon la quantité reçue.')
            lines = []
            line_list = ui.column()
            def redraw():
                line_list.clear()
                with line_list:
                    for idx, line in enumerate(lines):
                        with ui.row():
                            ui.label(f'{package_options.get(line["packaging_id"])} : {line["ordered_quantity"]} × '
                                     f'({line["unit_price"]} − {line["unit_discount"]} + {line["unit_fee"]}) FCFA')
                            ui.button('Retirer ligne', on_click=lambda i=idx: remove(i))
            def remove(idx):
                lines.pop(idx); redraw()
            def add():
                def action():
                    from services.packaging_service import quantity
                    from validation import validate_price
                    from money import fcfa
                    if package.value not in package_options:
                        raise ValueError('Sélectionnez un conditionnement.')
                    item = db.get(ProductPackaging, package.value)
                    n = quantity(count.value, 'Quantité commandée')
                    if not item.allow_fraction and n != n.to_integral_value():
                        raise ValueError('Ce conditionnement exige une quantité entière.')
                    quantity(n * item.coefficient, 'Quantité de base')
                    p = validate_price(price.value, 'Prix')
                    d = validate_price(discount.value, 'Remise')
                    f = validate_price(fee.value, 'Frais')
                    if d > p:
                        raise ValueError('La remise dépasse le prix.')
                    fcfa(n * (p - d + f), 'Total de ligne')
                    lines.append({'packaging_id': package.value, 'ordered_quantity': str(n),
                                  'unit_price': p, 'unit_discount': d, 'unit_fee': f})
                    redraw()
                run(action)
            def save():
                def action():
                    service.create_purchase_order({'supplier_id': supplier.value, 'reference': reference.value,
                        'order_date': order_date.value, 'expected_date': expected.value, 'notes': notes.value}, lines)
                    dialog.close(); refresh_page(); ui.notify('Commande enregistrée en brouillon.', type='positive')
                run(action)
            ui.button('Ajouter ligne', on_click=add)
            ui.button('Enregistrer commande', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    ui.button('Nouvelle commande', on_click=order_dialog)
    with ui.expansion('Fournisseurs et soldes', icon='local_shipping').classes('w-full'):
        for supplier in suppliers:
            ui.label(f'{supplier.name} — achats enregistrés : {supplier.total_purchases} FCFA — solde : {supplier.balance_due} FCFA')
        ui.label('Les soldes historiques ne sont pas automatiquement rapprochés des réceptions.')
        legacy_debts = db.query(SupplierDebt).filter(SupplierDebt.receipt_id.is_(None)).all()
        for debt in legacy_debts:
            ui.label(f'Dette historique {debt.reference} — fournisseur {debt.supplier.name} — total {debt.initial_amount} FCFA — payé {debt.paid_amount} FCFA — reste {debt.remaining_amount} FCFA — lecture seule')
            for payment in debt.payments:
                ui.label(f'Règlement historique {payment.date} : {payment.amount} FCFA — {METHODS.get(payment.payment_method, payment.payment_method)}')
    ui.label('Commandes récentes').classes('text-xl font-semibold')

    def order_details(order_id):
        def action():
            order = db.get(PurchaseOrder, order_id)
            if not order:
                raise ValueError('Commande introuvable.')
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl'):
                ui.label(f'{order.reference} — {STATUS.get(order.status, order.status)}').classes('text-lg font-bold')
                ui.label(f'Fournisseur : {order.supplier.name} — total : {order.total_amount} FCFA — réceptionné : {order.received_amount} FCFA')
                for line in order.purchase_order_lines:
                    ui.label(f'{line.product.name} — {line.packaging_name or "conditionnement historique inconnu"} '
                             f'× {line.conversion_factor} {line.base_unit} — commandé {line.ordered_quantity}, reçu {line.received_quantity} '
                             f'— prix {line.unit_price}, remise {line.unit_discount}, frais {line.unit_fee} FCFA')
                if order.status == 'draft':
                    def validate():
                        def do():
                            service.validate_purchase_order(order.id)
                            dialog.close(); refresh_page(); ui.notify('Commande validée.', type='positive')
                        run(do)
                    ui.button('Valider commande', on_click=validate)
                if order.status in ('draft', 'validated') and not order.is_cancelled:
                    def cancel():
                        def do():
                            service.cancel_purchase_order(order.id)
                            dialog.close(); refresh_page(); ui.notify('Commande annulée.', type='positive')
                        run(do)
                    ui.button('Annuler commande', on_click=cancel)
                if order.status in ('validated', 'partially_received') and not order.is_cancelled:
                    ui.label('Quantités reçues : laisser vide les lignes non livrées.')
                    fields = [(line.id, ui.input(f'Reçu ligne {line.id} — {line.product.name} ({line.packaging_name})'))
                              for line in order.purchase_order_lines if line.received_quantity < line.ordered_quantity]
                    due_date = ui.input('Échéance facultative (AAAA-MM-JJ)')
                    key = uuid4().hex
                    def receive():
                        def do():
                            data = [{'line_id': ident, 'received_quantity': field.value} for ident, field in fields if field.value not in ('', None)]
                            service.receive_purchase_order(order.id, data, request_key=key, due_date=due_date.value)
                            dialog.close(); refresh_page(); ui.notify('Réception enregistrée.', type='positive')
                        run(do)
                    ui.button('Enregistrer réception', on_click=receive)
                receipts = db.query(PurchaseReceipt).filter_by(purchase_order_id=order.id).all()
                for receipt in receipts:
                    ui.label(f'Réception {receipt.reference} — {receipt.date} — {receipt.total_amount} FCFA')
                debts = db.query(SupplierDebt).filter_by(purchase_order_id=order.id).all()
                for debt in debts:
                    ui.label(f'Dette {debt.reference} — total {debt.initial_amount} FCFA — payé {debt.paid_amount} FCFA — reste {debt.remaining_amount} FCFA — échéance {debt.due_date or "non renseignée"}')
                    for payment in debt.payments:
                        ui.label(f'Règlement {payment.date} : {payment.amount} FCFA — {METHODS.get(payment.payment_method, payment.payment_method)} — {payment.reference} — {"lié à la caisse" if payment.cash_link_status == "linked_cash" else "hors caisse / historique"}')
                    if debt.receipt_id is not None and debt.remaining_amount and not debt.is_cancelled:
                        def payment_dialog(debt_id=debt.id):
                            with ui.dialog() as payment_box, ui.card():
                                session = ManagedCashService(db).get_open()
                                ui.label('Règlement fournisseur avec caisse')
                                ui.label(f'Caisse : {session.reference}' if session else 'Ouvrez d’abord une caisse.')
                                amount = ui.input('Montant à régler FCFA')
                                method = ui.select(METHODS, label='Moyen de paiement')
                                note = ui.input('Note facultative')
                                key = uuid4().hex
                                def pay():
                                    def do():
                                        SupplierPaymentService(db).pay(debt_id, amount.value, method.value, key, note.value, cash_session_id=session.id if session else None)
                                        payment_box.close(); dialog.close(); refresh_page(); ui.notify('Règlement enregistré en caisse.', type='positive')
                                    run(do)
                                ui.button('Enregistrer règlement', on_click=pay)
                                ui.button('Fermer règlement', on_click=payment_box.close)
                            payment_box.open()
                        ui.button('Régler cette dette', on_click=payment_dialog)
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        run(action)

    for order in service.get_all_purchase_orders(include_cancelled=True)[:100]:
        with ui.row().classes('items-center'):
            ui.label(f'{order.reference} — {STATUS.get(order.status, order.status)} — {order.total_amount} FCFA')
            ui.button('Ouvrir commande', on_click=lambda ident=order.id: order_details(ident))
