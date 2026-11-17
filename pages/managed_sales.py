"""Ventes au comptant avec prix et conversion par conditionnement."""
from uuid import uuid4
from nicegui import ui
from models.packaging import ProductPackaging
from models.client import Client
from models.managed_credit import ManagedCreditProfile, ManagedCreditSale
from models.managed_deposit import ManagedDepositIssue, ManagedDepositReturn, ManagedDepositRefund, ManagedDepositReturnCancellation
from models.returnable_packaging import ReturnablePackagingType
from models.managed_operations import ManagedSale, ManagedSaleCancellation, ManagedSaleLine, ManagedCashTransaction, ManagedSalePayment
from models.managed_returns import ManagedReturn, ManagedReturnLine, ManagedReturnRefund, ManagedReturnCancellation
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.managed_credit_service import ManagedCreditService
from services.managed_deposit_service import ManagedDepositService
from services.deposit_return_cancellation_service import DepositReturnCancellationService
from services.deposit_configuration_service import DepositConfigurationService
from services.sale_cancellation_service import SaleCancellationService
from services.sale_return_service import SaleReturnService
from services.return_cancellation_service import ReturnCancellationService
from services.packaging_service import quantity
from money import fcfa

MODES = {'retail': 'Détail', 'wholesale': 'Gros', 'semi_wholesale': 'Semi-gros'}


def create_managed_sales_page(db, refresh_page):
    METHODS = labels(db, active_only=True)
    ALL_METHODS = labels(db)
    cash = ManagedCashService(db)
    sales = ManagedSaleService(db)
    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    ui.label('Ventes au comptant').classes('text-2xl font-bold')
    ui.label('Configurez chaque conditionnement. Les ventes consignées exigent un client ; leur annulation exige la récupération de tous les vides ; les retours de marchandise et de vides sont séparés. '
             'Les ventes historiques ne figurent pas dans cette liste.').classes('text-orange-800')
    credit_service = ManagedCreditService(db)
    clients = db.query(Client).join(ManagedCreditProfile, ManagedCreditProfile.client_id == Client.id).filter(Client.is_active.is_(True)).order_by(Client.name).all()
    client_options = {c.id: f'{c.name} — {c.code}' for c in clients}
    def new_client_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Nouveau client pour le crédit')
            ui.label('Les anciens clients non rapprochés ne sont pas intégrés automatiquement.')
            name = ui.input('Nom du nouveau client')
            client_type = ui.select({'particulier': 'Particulier', 'professionnel': 'Professionnel'}, label='Type du nouveau client')
            limit = ui.input('Plafond crédit FCFA')
            unlimited = ui.checkbox('Sans plafond de crédit')
            def save_client():
                def action():
                    credit_service.create_client(name.value, client_type=client_type.value, credit_limit=limit.value or None, no_limit=unlimited.value)
                    dialog.close(); refresh_page(); ui.notify('Client crédit créé.', type='positive')
                run(action)
            ui.button('Créer client crédit', on_click=save_client)
            ui.button('Fermer client', on_click=dialog.close)
        dialog.open()
    ui.button('Nouveau client crédit', on_click=new_client_dialog)
    session = cash.get_open()
    packs = db.query(ProductPackaging).join(ProductPackaging.product).filter(
        ProductPackaging.is_active.is_(True), ProductPackaging.product.has(is_active=True)).all()
    options = {p.id: f'{p.product.name} — {p.name} — {p.coefficient} {p.base_unit} — '
               f'détail {p.retail_price if p.retail_price is not None else "non défini"} / '
               f'gros {p.wholesale_price if p.wholesale_price is not None else "non défini"} / '
               f'semi-gros {p.semi_wholesale_price if p.semi_wholesale_price is not None else "non défini"} FCFA' for p in packs}
    if not session:
        ui.label('Ouvrez une caisse avant de saisir une vente.')
    else:
        def sell_dialog():
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
                ui.label('Nouvelle vente au comptant')
                mode = ui.select(MODES, label='Tarif de vente')
                method = ui.select({**METHODS, 'mixed': 'Paiement mixte', 'credit': 'Crédit client'}, label='Moyen de paiement')
                client = ui.select(client_options, label='Client crédit ou consigne').classes('w-full')
                override_limit = ui.checkbox('Confirmer un éventuel dépassement du plafond crédit')
                ui.label('Paiement mixte : au moins deux moyens. Crédit : paiements initiaux facultatifs, le solde restant sera dû.')
                split_method = ui.select(METHODS, label='Moyen du paiement mixte')
                split_amount = ui.input('Montant du paiement mixte FCFA')
                split_payments = []
                payments_list = ui.column()
                def redraw_payments():
                    payments_list.clear()
                    with payments_list:
                        for index, payment in enumerate(split_payments):
                            with ui.row():
                                ui.label(f'{METHODS[payment["method"]]} : {payment["amount"]} FCFA')
                                ui.button('Retirer paiement', on_click=lambda i=index: remove_payment(i))
                def remove_payment(index):
                    split_payments.pop(index); redraw_payments()
                def add_payment():
                    def action():
                        if split_method.value not in METHODS:
                            raise ValueError('Choisissez un moyen de paiement.')
                        if any(p['method'] == split_method.value for p in split_payments):
                            raise ValueError('Ce moyen est déjà présent.')
                        amount = fcfa(split_amount.value, 'Montant encaissé')
                        if amount <= 0:
                            raise ValueError('Le montant encaissé doit être positif.')
                        split_payments.append({'method': split_method.value, 'amount': amount})
                        split_amount.value = ''
                        redraw_payments()
                    run(action)
                ui.button('Ajouter paiement mixte', on_click=add_payment)
                pack = ui.select(options, label='Conditionnement à vendre').classes('w-full')
                count = ui.input('Quantité vendue')
                custom_price = ui.input('Prix unitaire ajusté FCFA (facultatif)')
                ui.label('Laissez vide pour utiliser le tarif configuré ; le prix appliqué sera conservé dans la vente.')
                lines = []
                line_list = ui.column()
                key = uuid4().hex
                def redraw():
                    line_list.clear()
                    with line_list:
                        for index, line in enumerate(lines):
                            with ui.row():
                                ui.label(f'{options[line["packaging_id"]]} — quantité {line["quantity"]}' + (f' — prix ajusté {line["unit_price"]} FCFA' if line.get('unit_price') is not None else ''))
                                ui.button('Retirer', on_click=lambda i=index: remove(i))
                def remove(index):
                    lines.pop(index); redraw()
                def add():
                    def action():
                        if pack.value not in options:
                            raise ValueError('Sélectionnez un conditionnement.')
                        number = quantity(count.value, 'Quantité vendue')
                        override = None if custom_price.value in (None, '') else fcfa(custom_price.value, 'Prix de vente')
                        if override is not None and override < 0:
                            raise ValueError('Le prix de vente ne peut pas être négatif.')
                        lines.append({'packaging_id': pack.value, 'quantity': str(number), 'unit_price': override})
                        custom_price.value = ''
                        redraw()
                    run(action)
                def preview():
                    def action():
                        if mode.value not in MODES or method.value not in (*METHODS, 'mixed', 'credit') or not lines:
                            raise ValueError('Sélectionnez un tarif, un moyen et au moins une ligne.')
                        verified = []
                        total = 0
                        has_deposit = False
                        db.expire_all()  # relire les tarifs avant l'aperçu
                        for line in lines:
                            package = db.get(ProductPackaging, line['packaging_id'])
                            if not package or not package.is_active or not package.product.is_active:
                                raise ValueError('Conditionnement indisponible.')
                            deposit = DepositConfigurationService(db).quote(package.id, line['quantity'])
                            if deposit:
                                has_deposit = True
                            if package.product.consignment_value is not None and package.product.consignment_value > 0:
                                raise ValueError('Consigne historique positive : diagnostic nécessaire avant vente.')
                            price = getattr(package, ManagedSaleService.PRICE_FIELDS[mode.value])
                            if price is None:
                                raise ValueError(f'Tarif non configuré pour {package.product.name}.')
                            applied = price if line.get('unit_price') is None else line['unit_price']
                            amount = fcfa(quantity(line['quantity']) * applied, 'Total de ligne')
                            total = fcfa(total + amount + sum(component['amount'] for component in deposit), 'Total vente')
                            verified_line = {**line, 'expected_unit_price': price}
                            if deposit:
                                verified_line['expected_deposits'] = deposit
                            verified.append(verified_line)
                        selected_payments = [dict(p) for p in split_payments] if method.value in ('mixed', 'credit') else None
                        if method.value == 'mixed' and (len(selected_payments) < 2 or sum(p['amount'] for p in selected_payments) != total):
                            raise ValueError('Indiquez au moins deux moyens distincts dont le total correspond à la vente.')
                        if has_deposit and client.value not in client_options:
                            raise ValueError('Sélectionnez un client pour les emballages consignés.')
                        if method.value == 'credit' and (client.value not in client_options or sum(p['amount'] for p in selected_payments) >= total):
                            raise ValueError('Choisissez un client et laissez un solde crédit positif.')
                        if method.value not in ('mixed', 'credit') and split_payments:
                            raise ValueError('Retirez les paiements saisis ou choisissez le paiement mixte ou crédit.')
                        with ui.dialog() as confirm, ui.card():
                            ui.label(f'Vente — {MODES[mode.value]} — {ALL_METHODS.get(method.value, "Crédit client" if method.value == "credit" else "Paiement mixte")}')
                            if method.value == 'credit':
                                ui.label(f'Client : {client_options[client.value]} — reste dû : {total - sum(p["amount"] for p in selected_payments)} FCFA')
                            elif has_deposit:
                                ui.label(f'Client des consignes : {client_options[client.value]}')
                            for payment in selected_payments or []:
                                ui.label(f'{METHODS[payment["method"]]} : {payment["amount"]} FCFA')
                            for line in verified:
                                applied = line['expected_unit_price'] if line.get('unit_price') is None else line['unit_price']
                                ui.label(f'{options[line["packaging_id"]]} × {line["quantity"]} au prix appliqué {applied} FCFA (tarif configuré : {line["expected_unit_price"]} FCFA)')
                                for component in line.get('expected_deposits', []):
                                    ui.label(f'Consigne {component["code"]} : {component["pieces"]} pièce(s) × {component["unit_value"]} = {component["amount"]} FCFA')
                            if method.value == 'credit':
                                ui.label(f'Total vente : {total} FCFA — encaissé maintenant : {sum(p["amount"] for p in selected_payments)} FCFA').classes('text-lg font-bold')
                            else:
                                ui.label(f'Total à encaisser : {total} FCFA').classes('text-lg font-bold')
                            chosen_mode, chosen_method = mode.value, method.value
                            chosen_client = client.value if chosen_method == 'credit' or has_deposit else None
                            chosen_override = bool(override_limit.value) if chosen_method == 'credit' else False
                            def save():
                                def do_save():
                                    sale = sales.sell(session.id, chosen_mode, chosen_method, verified, key, payments=selected_payments, client_id=chosen_client, override_limit=chosen_override)
                                    message = f'Vente enregistrée : {sale.total} FCFA.'
                                    confirm.close(); dialog.close(); refresh_page(); ui.notify(message, type='positive')
                                run(do_save)
                            ui.button('Confirmer et encaisser', on_click=save)
                            ui.button('Retour au panier', on_click=confirm.close)
                        confirm.open()
                    run(action)
                ui.button('Ajouter au panier', on_click=add)
                ui.button('Vérifier vente', on_click=preview)
                ui.button('Fermer vente', on_click=dialog.close)
            dialog.open()
        ui.button('Nouvelle vente au comptant', on_click=sell_dialog)
    ui.label('Ventes au comptant récentes').classes('text-xl font-semibold')
    recent = db.query(ManagedSale).order_by(ManagedSale.id.desc()).limit(100).all()
    cancelled = {row.sale_id for row in db.query(ManagedSaleCancellation).all()}
    deposit_sales = {row[0] for row in db.query(ManagedSaleLine.sale_id).join(ManagedDepositIssue, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).distinct()}
    for sale in recent:
        method_label = {'mixed': 'Paiement mixte', 'credit': 'Crédit client'}.get(sale.payment_method, ALL_METHODS.get(sale.payment_method, sale.payment_method))
        status = 'ANNULÉE' if sale.id in cancelled else 'valide'
        ui.label(f'{sale.reference} — {sale.created_at} — {MODES.get(sale.mode, sale.mode)} — {sale.total} FCFA — {method_label} — {status}')
    returns = db.query(ManagedReturn).order_by(ManagedReturn.id.desc()).limit(100).all()
    cancelled_returns = {row.return_id for row in db.query(ManagedReturnCancellation).all()}
    cancelled_deposit_returns = {r.return_id for r in db.query(ManagedDepositReturnCancellation).all()}
    if returns:
        with ui.expansion('Retours enregistrés', icon='assignment_return').classes('w-full'):
            for returned in returns:
                ui.label(f'Retour #{returned.id} — vente #{returned.sale_id} — {returned.total} FCFA — réduction créance {returned.credit_reduction} FCFA — {returned.reason} — {"annulé" if returned.id in cancelled_returns else "actif"}')
                for line in db.query(ManagedReturnLine).filter_by(return_id=returned.id):
                    ui.label(f'Ligne de vente #{line.sale_line_id} — quantité de base {line.base_quantity} — {line.amount} FCFA')
                for refund in db.query(ManagedReturnRefund).filter_by(return_id=returned.id):
                    movement = db.get(ManagedCashTransaction, refund.refund_transaction_id)
                    ui.label(f'Remboursement {ALL_METHODS.get(movement.method, movement.method)} : {movement.amount} FCFA — encaissement #{refund.original_transaction_id}')
    if session:
        returned_sales = {row.sale_id for row in db.query(ManagedReturn).all() if row.id not in cancelled_returns}
        available = {sale.id: f'{sale.reference} — {sale.total} FCFA' for sale in recent if sale.id not in cancelled and sale.id not in returned_sales}
        def cancellation_dialog():
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
                ui.label('Annulation totale de vente').classes('text-lg font-bold')
                ui.label('Remboursement des montants encaissés sur les moyens d’origine, annulation du solde de crédit et réintégration de toute la marchandise. Les comptes non espèces ne sont pas contrôlés automatiquement.')
                ui.label('Vérifiez qu’aucun remboursement manuel n’a déjà été effectué pour cette vente.')
                chosen = ui.select(available, label='Vente à annuler').classes('w-full')
                reason = ui.input('Motif obligatoire de l’annulation').classes('w-full')
                recovered = ui.checkbox('Je confirme avoir récupéré toutes les marchandises et pouvoir rembourser chaque moyen.')
                empties = ui.checkbox('Pour une vente consignée, je confirme avoir récupéré tous les vides vendus.')
                key = uuid4().hex
                def confirm():
                    def action():
                        SaleCancellationService(db).cancel(chosen.value, session.id, reason.value, key, goods_recovered=recovered.value, empties_recovered=empties.value)
                        dialog.close(); refresh_page(); ui.notify('Vente annulée et remboursements enregistrés.', type='positive')
                    run(action)
                ui.button('Confirmer annulation totale', on_click=confirm)
                ui.button('Fermer annulation', on_click=dialog.close)
            dialog.open()
        ui.button('Annuler une vente', on_click=cancellation_dialog)
        return_options = {sale.id: f'{sale.reference} — {sale.total} FCFA' for sale in recent if sale.id not in cancelled}
        def return_dialog():
            from fractions import Fraction
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
                ui.label('Retour partiel de marchandises').classes('text-lg font-bold')
                ui.label('Les emballages consignés sont retournés séparément. Quantités en unités de base réellement récupérées. Précisez la réduction de créance et les remboursements sur les encaissements d’origine. Pour annuler toute la vente après un retour, retournez toutes les quantités restantes et soldez les contreparties.')
                ui.label('Vérifiez les remboursements manuels éventuels et les soldes non espèces : ils ne sont pas contrôlés automatiquement.')
                sale_select = ui.select(return_options, label='Vente pour retour').classes('w-full')
                content = ui.column().classes('w-full')
                reason = ui.input('Motif obligatoire du retour').classes('w-full')
                recovered = ui.checkbox('Je confirme avoir récupéré les quantités indiquées et pouvoir effectuer les remboursements.')
                finish_sale = ui.checkbox('Annuler toute la vente après retour de toutes les quantités restantes')
                data = {'lines': {}, 'refunds': {}, 'reduction': None}
                key = uuid4().hex
                def select_sale():
                    data.update(lines={}, refunds={}, reduction=None)
                    content.clear()
                    if sale_select.value not in return_options:
                        return
                    with content:
                        selected_sale = db.get(ManagedSale, sale_select.value)
                        for line in db.query(ManagedSaleLine).filter_by(sale_id=selected_sale.id).order_by(ManagedSaleLine.id):
                            returned = sum((r.base_quantity for r in db.query(ManagedReturnLine).filter_by(sale_line_id=line.id) if r.return_id not in cancelled_returns), start=0)
                            ui.label(f'Ligne #{line.id} : {line.packaging_name} — vendu {line.base_quantity} {line.base_unit}, déjà retourné {returned} ; montant initial {line.amount} FCFA')
                            data['lines'][line.id] = (line, ui.input(f'Quantité retournée ligne {line.id}'))
                        debt = db.query(ManagedCreditSale).filter_by(sale_id=selected_sale.id).one_or_none()
                        if debt:
                            ui.label(f'Créance restante : {debt.remaining_amount} FCFA')
                            data['reduction'] = ui.input('Réduction de créance FCFA', value='0')
                        links = db.query(ManagedSalePayment).filter_by(sale_id=selected_sale.id).all()
                        if selected_sale.payment_method in ALL_METHODS and not links:
                            originals = db.query(ManagedCashTransaction).filter_by(sale_id=selected_sale.id, kind='sale').all()
                        else:
                            originals = [db.get(ManagedCashTransaction, link.transaction_id) for link in links]
                        for payment in originals:
                            if not payment:
                                continue
                            previous = sum((db.get(ManagedCashTransaction, r.refund_transaction_id).amount for r in db.query(ManagedReturnRefund).filter_by(original_transaction_id=payment.id) if r.return_id not in cancelled_returns), start=0)
                            previous += sum((db.get(ManagedCashTransaction, r.refund_transaction_id).amount for r in db.query(ManagedDepositRefund).filter_by(original_transaction_id=payment.id) if r.deposit_return_id not in cancelled_deposit_returns), start=0)
                            ui.label(f'Encaissement #{payment.id} : {ALL_METHODS.get(payment.method, payment.method)} {payment.amount} FCFA — déjà remboursé {previous} FCFA')
                            data['refunds'][payment.id] = ui.input(f'Remboursement encaissement {payment.id} FCFA')
                sale_select.on('update:model-value', lambda _: select_sale())
                def preview():
                    def action():
                        if sale_select.value not in return_options or not recovered.value:
                            raise ValueError('Sélectionnez une vente et confirmez la récupération.')
                        lines, refunds, total = [], [], 0
                        for ident, (line, widget) in data['lines'].items():
                            if widget.value in (None, ''):
                                continue
                            count = quantity(widget.value, 'Quantité retournée')
                            value = Fraction(count) * Fraction(line.amount) / Fraction(line.base_quantity)
                            if value.denominator != 1:
                                raise ValueError('Le montant du retour doit être un nombre entier de FCFA.')
                            total = fcfa(total + value.numerator, 'Total retour')
                            lines.append({'sale_line_id': ident, 'base_quantity': str(count)})
                        if not lines:
                            raise ValueError('Saisissez au moins une quantité retournée.')
                        reduction = fcfa(data['reduction'].value or 0, 'Réduction de créance') if data['reduction'] else 0
                        for ident, widget in data['refunds'].items():
                            if widget.value not in (None, ''):
                                refunds.append({'transaction_id': ident, 'amount': fcfa(widget.value, 'Remboursement')})
                        if reduction < 0 or any(r['amount'] <= 0 for r in refunds) or reduction + sum(r['amount'] for r in refunds) != total:
                            raise ValueError('La réduction de créance et les remboursements doivent correspondre au montant du retour.')
                        chosen_sale, chosen_reason, chosen_finish = sale_select.value, reason.value, bool(finish_sale.value)
                        with ui.dialog() as confirmation, ui.card():
                            ui.label(f'Total du retour : {total} FCFA — réduction de créance : {reduction} FCFA')
                            if chosen_finish:
                                ui.label('Annulation totale de la vente demandée après ce retour.')
                            for refund in refunds:
                                ui.label(f'Encaissement #{refund["transaction_id"]} : remboursement {refund["amount"]} FCFA')
                            def save():
                                def action():
                                    SaleReturnService(db).record(chosen_sale, session.id, lines, reduction, refunds, chosen_reason, key, goods_recovered=True, cancel_sale=chosen_finish)
                                    confirmation.close(); dialog.close(); refresh_page(); ui.notify('Retour enregistré.', type='positive')
                                run(action)
                            ui.button('Confirmer retour', on_click=save)
                            ui.button('Revenir au retour', on_click=confirmation.close)
                        confirmation.open()
                    run(action)
                ui.button('Vérifier retour', on_click=preview)
                ui.button('Fermer retour', on_click=dialog.close)
            dialog.open()
        ui.button('Enregistrer un retour', on_click=return_dialog)
        def cancel_return_dialog():
            options = {r.id: f'Retour #{r.id} — vente #{r.sale_id} — {r.total} FCFA' for r in returns if r.id not in cancelled_returns and r.sale_id not in cancelled}
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
                ui.label('Annuler un retour').classes('text-lg font-bold')
                ui.label('Les marchandises repartent du stock. Le client doit avoir rendu les remboursements sur leurs moyens d’origine. Une modification de stock ultérieure bloque cette opération.')
                chosen = ui.select(options, label='Retour à annuler').classes('w-full')
                reason = ui.input('Motif d’annulation du retour').classes('w-full')
                confirmed = ui.checkbox('Je confirme le départ des marchandises et la récupération effective des remboursements.')
                key = uuid4().hex
                def save():
                    def action():
                        ReturnCancellationService(db).cancel(chosen.value, session.id, reason.value, key, goods_and_refunds_recovered=confirmed.value)
                        dialog.close(); refresh_page(); ui.notify('Retour annulé et contre-écritures enregistrées.', type='positive')
                    run(action)
                ui.button('Confirmer annulation retour', on_click=save)
                ui.button('Fermer annulation retour', on_click=dialog.close)
            dialog.open()
        ui.button('Annuler un retour', on_click=cancel_return_dialog)

    ui.label('Créances clients — nouveau circuit').classes('text-xl font-semibold')
    debts = db.query(ManagedCreditSale).order_by(ManagedCreditSale.id.desc()).limit(100).all()
    debt_options = {}
    for debt in debts:
        client_record = db.get(Client, debt.client_id)
        label = f'{client_record.name} — vente #{debt.sale_id} — restant {debt.remaining_amount} FCFA'
        status = 'annulé' if debt.sale_id in cancelled else 'solde nul' if debt.remaining_amount == 0 else 'solde réduit ou partiellement réglé' if debt.remaining_amount < debt.initial_amount else 'non réglé'
        ui.label(label + f' — {status}')
        if debt.remaining_amount > 0 and debt.sale_id not in cancelled:
            debt_options[debt.id] = label
    if session:
        def payment_dialog():
            with ui.dialog() as dialog, ui.card():
                ui.label('Règlement de créance')
                debt = ui.select(debt_options, label='Créance à régler').classes('w-full')
                method = ui.select(METHODS, label='Moyen du règlement')
                amount = ui.input('Montant du règlement FCFA')
                note = ui.input('Observation du règlement (facultatif)')
                key = uuid4().hex
                def save():
                    def action():
                        credit_service.pay(debt.value, session.id, method.value, amount.value, key, note.value)
                        dialog.close(); refresh_page(); ui.notify('Règlement enregistré.', type='positive')
                    run(action)
                ui.button('Confirmer règlement', on_click=save)
                ui.button('Fermer règlement', on_click=dialog.close)
            dialog.open()
        ui.button('Régler une créance', on_click=payment_dialog)

    ui.label('Emballages consignés clients — nouveau circuit').classes('text-xl font-semibold')
    issues = db.query(ManagedDepositIssue).order_by(ManagedDepositIssue.id.desc()).limit(100).all()
    cancelled_deposit_returns = {r.return_id for r in db.query(ManagedDepositReturnCancellation).all()}
    issue_options = {}
    for issue in issues:
        item = db.get(ReturnablePackagingType, issue.returnable_id)
        customer = db.get(Client, issue.client_id)
        returned_count = sum((r.pieces for r in db.query(ManagedDepositReturn).filter_by(issue_id=issue.id) if r.id not in cancelled_deposit_returns), start=0)
        issue_line = db.get(ManagedSaleLine, issue.sale_line_id)
        remaining = 0 if issue_line.sale_id in cancelled else issue.pieces - returned_count
        label = f'{customer.name} — {item.code} — vente ligne #{issue.sale_line_id} — restant {remaining} pièce(s) à {issue.unit_value} FCFA'
        ui.label(label)
        if remaining > 0:
            issue_options[issue.id] = label
    if session:
        def deposit_return_dialog():
            from services.returnable_stock_service import _pieces
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
                ui.label('Retour de vides consignés').classes('text-lg font-bold')
                ui.label('Déclarez d’abord le stock initial des vides. Répartissez explicitement la valeur entre réduction de créance et remboursements liés aux encaissements de cette vente.')
                ui.label('Les remboursements manuels externes et soldes non espèces ne sont pas contrôlés automatiquement.')
                chosen = ui.select(issue_options, label='Emballage consigné à retourner').classes('w-full')
                content = ui.column().classes('w-full')
                count = ui.input('Pièces vides reçues')
                reason = ui.input('Motif du retour de vides')
                received = ui.checkbox('Je confirme la réception physique des vides et les remboursements indiqués.')
                data = {'reduction': None, 'refunds': {}}
                key = uuid4().hex
                def select_issue():
                    data.update(reduction=None, refunds={})
                    content.clear()
                    if chosen.value not in issue_options:
                        return
                    issue = db.get(ManagedDepositIssue, chosen.value)
                    sale_line = db.get(ManagedSaleLine, issue.sale_line_id)
                    sale = db.get(ManagedSale, sale_line.sale_id)
                    with content:
                        ui.label(f'{sale.reference} — valeur unitaire figée : {issue.unit_value} FCFA')
                        credit = db.query(ManagedCreditSale).filter_by(sale_id=sale.id).one_or_none()
                        if credit:
                            ui.label(f'Créance restante : {credit.remaining_amount} FCFA')
                            data['reduction'] = ui.input('Réduction de créance sur consigne FCFA', value='0')
                        links = db.query(ManagedSalePayment).filter_by(sale_id=sale.id).all()
                        if sale.payment_method in ALL_METHODS and not links:
                            originals = db.query(ManagedCashTransaction).filter_by(sale_id=sale.id, kind='sale').all()
                        else:
                            originals = [db.get(ManagedCashTransaction, link.transaction_id) for link in links]
                        for entry in originals:
                            if not entry:
                                continue
                            previous = sum((db.get(ManagedCashTransaction, r.refund_transaction_id).amount for r in db.query(ManagedDepositRefund).filter_by(original_transaction_id=entry.id) if r.deposit_return_id not in cancelled_deposit_returns), start=0)
                            previous += sum((db.get(ManagedCashTransaction, r.refund_transaction_id).amount for r in db.query(ManagedReturnRefund).filter_by(original_transaction_id=entry.id) if r.return_id not in cancelled_returns), start=0)
                            ui.label(f'Encaissement #{entry.id} — {ALL_METHODS.get(entry.method, entry.method)} : {entry.amount} FCFA — déjà remboursé {previous} FCFA')
                            data['refunds'][entry.id] = ui.input(f'Remboursement de consigne encaissement {entry.id} FCFA')
                chosen.on('update:model-value', lambda _: select_issue())
                def preview():
                    def action():
                        if chosen.value not in issue_options or not received.value:
                            raise ValueError('Sélectionnez un emballage et confirmez sa réception.')
                        issue = db.get(ManagedDepositIssue, chosen.value)
                        pieces = _pieces(count.value)
                        amount = fcfa(pieces * issue.unit_value, 'Montant consigne')
                        reduction = fcfa(data['reduction'].value or 0, 'Réduction de créance') if data['reduction'] else 0
                        refunds = [{'transaction_id': ident, 'amount': fcfa(widget.value, 'Remboursement')}
                                   for ident, widget in data['refunds'].items() if widget.value not in (None, '')]
                        if reduction < 0 or any(r['amount'] <= 0 for r in refunds) or reduction + sum(r['amount'] for r in refunds) != amount:
                            raise ValueError('La réduction et les remboursements doivent correspondre à la valeur des vides.')
                        issue_id, why = chosen.value, reason.value
                        with ui.dialog() as confirm, ui.card():
                            ui.label(f'{pieces} pièce(s) — consigne {amount} FCFA — réduction créance {reduction} FCFA')
                            for refund in refunds:
                                ui.label(f'Encaissement #{refund["transaction_id"]} — remboursement {refund["amount"]} FCFA')
                            def save():
                                def action():
                                    ManagedDepositService(db).return_empty(issue_id, session.id, pieces, reduction, refunds, why, key, received=True)
                                    confirm.close(); dialog.close(); refresh_page(); ui.notify('Retour de vides consignés enregistré.', type='positive')
                                run(action)
                            ui.button('Confirmer retour de vides', on_click=save)
                            ui.button('Revenir aux vides', on_click=confirm.close)
                        confirm.open()
                    run(action)
                ui.button('Vérifier retour de vides', on_click=preview)
                ui.button('Fermer retour de vides', on_click=dialog.close)
            dialog.open()
        ui.button('Retour de vides consignés', on_click=deposit_return_dialog)

    if session:
        active_empty_returns = db.query(ManagedDepositReturn).outerjoin(ManagedDepositReturnCancellation, ManagedDepositReturnCancellation.return_id == ManagedDepositReturn.id).filter(ManagedDepositReturnCancellation.id.is_(None)).order_by(ManagedDepositReturn.id.desc()).all()
        options_empty = {r.id: f'Retour #{r.id} — {r.pieces} pièce(s), {r.amount} FCFA — {r.reason}' for r in active_empty_returns}
        def cancel_empty_dialog():
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
                ui.label('Annuler un retour de vides').classes('text-lg font-bold')
                ui.label('Les vides doivent être remis au client et les remboursements récupérés sur leurs moyens d’origine. Un mouvement de stock ultérieur bloque la contrepassation.')
                choice = ui.select(options_empty, label='Retour de vides à annuler').classes('w-full')
                why = ui.input('Motif de l’annulation des vides')
                confirmed = ui.checkbox('Je confirme avoir remis les vides et récupéré tous les remboursements.')
                key = uuid4().hex
                def save():
                    def action():
                        DepositReturnCancellationService(db).cancel(choice.value, session.id, why.value, key, empties_and_refunds_recovered=confirmed.value)
                        dialog.close(); refresh_page(); ui.notify('Retour de vides annulé.', type='positive')
                    run(action)
                ui.button('Confirmer annulation de vides', on_click=save)
                ui.button('Fermer annulation de vides', on_click=dialog.close)
            dialog.open()
        ui.button('Annuler un retour de vides', on_click=cancel_empty_dialog)
