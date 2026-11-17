"""Ventes au comptant avec prix et conversion par conditionnement."""
from uuid import uuid4
from nicegui import ui
from models.packaging import ProductPackaging
from models.managed_operations import ManagedSale
from services.cash_methods import METHODS
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import quantity
from money import fcfa

MODES = {'retail': 'Détail', 'wholesale': 'Gros', 'semi_wholesale': 'Semi-gros'}


def create_managed_sales_page(db, refresh_page):
    cash = ManagedCashService(db)
    sales = ManagedSaleService(db)
    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    ui.label('Ventes au comptant').classes('text-2xl font-bold')
    ui.label('Vente intégralement réglée en un moyen ; crédits, paiements mixtes, consignes, annulations et retours ne sont pas encore intégrés. '
             'Les ventes historiques ne figurent pas dans cette liste.').classes('text-orange-800')
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
                method = ui.select(METHODS, label='Moyen de paiement')
                pack = ui.select(options, label='Conditionnement à vendre').classes('w-full')
                count = ui.input('Quantité vendue')
                lines = []
                line_list = ui.column()
                key = uuid4().hex
                def redraw():
                    line_list.clear()
                    with line_list:
                        for index, line in enumerate(lines):
                            with ui.row():
                                ui.label(f'{options[line["packaging_id"]]} — quantité {line["quantity"]}')
                                ui.button('Retirer', on_click=lambda i=index: remove(i))
                def remove(index):
                    lines.pop(index); redraw()
                def add():
                    def action():
                        if pack.value not in options:
                            raise ValueError('Sélectionnez un conditionnement.')
                        number = quantity(count.value, 'Quantité vendue')
                        lines.append({'packaging_id': pack.value, 'quantity': str(number)})
                        redraw()
                    run(action)
                def preview():
                    def action():
                        if mode.value not in MODES or method.value not in METHODS or not lines:
                            raise ValueError('Sélectionnez un tarif, un moyen et au moins une ligne.')
                        verified = []
                        total = 0
                        for line in lines:
                            package = db.get(ProductPackaging, line['packaging_id'])
                            if not package or not package.is_active or not package.product.is_active:
                                raise ValueError('Conditionnement indisponible.')
                            price = getattr(package, ManagedSaleService.PRICE_FIELDS[mode.value])
                            if price is None:
                                raise ValueError(f'Tarif non configuré pour {package.product.name}.')
                            amount = fcfa(quantity(line['quantity']) * price, 'Total de ligne')
                            total = fcfa(total + amount, 'Total vente')
                            verified.append({**line, 'expected_unit_price': price})
                        with ui.dialog() as confirm, ui.card():
                            ui.label(f'Vente au comptant — {MODES[mode.value]} — {METHODS[method.value]}')
                            for line in verified:
                                ui.label(f'{options[line["packaging_id"]]} × {line["quantity"]} au prix {line["expected_unit_price"]} FCFA')
                            ui.label(f'Total à encaisser : {total} FCFA').classes('text-lg font-bold')
                            chosen_mode, chosen_method = mode.value, method.value
                            def save():
                                def do_save():
                                    sale = sales.sell(session.id, chosen_mode, chosen_method, verified, key)
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
    for sale in db.query(ManagedSale).order_by(ManagedSale.id.desc()).limit(100):
        ui.label(f'{sale.reference} — {sale.created_at} — {MODES.get(sale.mode, sale.mode)} — {sale.total} FCFA — {METHODS.get(sale.payment_method, sale.payment_method)}')
