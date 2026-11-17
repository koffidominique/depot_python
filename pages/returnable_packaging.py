"""Catalogue et journal manuel des vides, sans rapprochement de consigne."""
from uuid import uuid4
from nicegui import ui
from services.returnable_packaging_service import ReturnablePackagingService
from services.returnable_stock_service import ReturnableStockService


def create_returnable_packaging_page(db, refresh_page):
    service = ReturnablePackagingService(db)
    stock = ReturnableStockService(db)

    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    ui.label('Catalogue des emballages consignés').classes('text-2xl font-bold')
    ui.label('Journal manuel des vides présents au dépôt, séparé du stock de boissons. '
             'Les retours de vides des ventes consignées y sont ajoutés ; les achats et les mouvements manuels restent séparés. Les anciennes consignes ne sont pas rapprochées automatiquement.').classes('text-orange-800')
    ui.label('Ne créez que les emballages et montants confirmés avec vos fournisseurs.')

    def create_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
            ui.label('Nouvel emballage physique').classes('text-lg font-bold')
            code = ui.input('Code emballage')
            name = ui.input('Nom emballage')
            producer = ui.input('Brasseur ou propriétaire du circuit')
            kind = ui.select({'bottle': 'Bouteille', 'crate': 'Casier'}, label='Type physique')
            description = ui.input('Description ou format confirmé (facultatif)')
            value = ui.input('Valeur de consigne FCFA (facultatif)')
            ui.label('Laisser vide si la valeur est inconnue ; 0 indique une valeur explicitement nulle.')
            def save():
                def action():
                    service.create(code=code.value, name=name.value, producer=producer.value, kind=kind.value,
                                   description=description.value, deposit_value=value.value)
                    dialog.close()
                    refresh_page()
                    ui.notify('Emballage enregistré.', type='positive')
                run(action)
            ui.button('Enregistrer emballage', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    ui.button('Nouvel emballage', on_click=create_dialog)

    movement_names = {'initial': 'Comptage initial', 'entry': 'Entrée', 'exit': 'Sortie',
                      'breakage': 'Casse', 'loss': 'Perte', 'correction_in': 'Correction entrée',
                      'correction_out': 'Correction sortie'}

    def stock_dialog(item_id, initial):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
            ui.label('Déclarer le stock initial de vides' if initial else 'Enregistrer un mouvement de vides').classes('text-lg font-bold')
            ui.label('Comptage manuel : aucun lien automatique avec un client, fournisseur, achat, vente ou paiement.')
            kind = None if initial else ui.select({k: v for k, v in movement_names.items() if k != 'initial'}, label='Type de mouvement')
            count = ui.input('Nombre de pièces vides')
            reason = ui.input('Motif du mouvement')
            reference = ui.input('Référence de document (facultatif)')
            key = uuid4().hex
            def save():
                def action():
                    stock.record(item_id, 'initial' if initial else kind.value, count.value, reason.value, key, reference.value)
                    dialog.close()
                    refresh_page()
                    ui.notify('Mouvement de vides enregistré.', type='positive')
                run(action)
            ui.button('Confirmer mouvement', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    def history_dialog(item_id):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
            ui.label('Historique des vides — 100 derniers mouvements').classes('text-lg font-bold')
            movements = stock.history(item_id)
            if not movements:
                ui.label('Aucun mouvement.')
            for movement in movements:
                before = 'inconnu' if movement.stock_before is None else str(movement.stock_before)
                ui.label(f'{movement.date} — {movement_names.get(movement.movement_type, movement.movement_type)} : '
                         f'{movement.quantity} pièce(s), {before} → {movement.stock_after} — '
                         f'{movement.reason} — {movement.reference_document or "sans référence"}')
            ui.button('Fermer historique', on_click=dialog.close)
        dialog.open()
    items = service.list(include_archived=True)
    if not items:
        ui.label('Aucun emballage configuré.')
    for item in items:
        balance = stock.balance(item.id)
        with ui.row().classes('w-full items-center'):
            value = 'non renseignée' if item.deposit_value is None else f'{item.deposit_value} FCFA'
            ui.label(f'{item.code} — {item.name} — {item.producer} — '
                     f'{"Bouteille" if item.kind == "bottle" else "Casier"} — '
                     f'{item.description or "format non renseigné"} — consigne {value} — '
                     f'{"actif" if item.is_active else "archivé"} — '
                     f'stock de vides enregistré : {balance if balance is not None else "non déclaré"}')
            ui.button('Historique des vides', on_click=lambda ident=item.id: history_dialog(ident))
            if item.is_active:
                ui.button('Déclarer stock initial' if balance is None else 'Mouvement de vides',
                          on_click=lambda ident=item.id, initial=balance is None: stock_dialog(ident, initial))
            if item.is_active:
                def confirm(item_id=item.id):
                    with ui.dialog() as dialog, ui.card():
                        ui.label('Archiver cet emballage ? Il restera dans le catalogue historique.')
                        def archive():
                            def action():
                                service.archive(item_id)
                                dialog.close()
                                refresh_page()
                                ui.notify('Emballage archivé.', type='positive')
                            run(action)
                        ui.button('Confirmer archivage', on_click=archive)
                        ui.button('Retour', on_click=dialog.close)
                    dialog.open()
                ui.button('Archiver emballage', on_click=confirm)
