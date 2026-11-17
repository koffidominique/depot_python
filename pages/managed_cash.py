"""Caisse : règlements fournisseurs, ventes au comptant et mouvements saisis."""
from uuid import uuid4
from nicegui import ui
from models.managed_cash import ManagedCashSession
from models.managed_operations import ManagedCashTransaction
from services.cash_methods import METHODS
from services.managed_cash_service import ManagedCashService

KINDS = {'sale': 'Vente au comptant', 'expense': 'Dépense', 'income': 'Autre recette',
         'outflow': 'Autre sortie', 'correction_in': 'Correction entrée', 'correction_out': 'Correction sortie'}
CATEGORIES = ['Transport', 'Carburant', 'Chargement', 'Déchargement', 'Manutention',
              'Réparation', 'Maintenance', 'Électricité', 'Frais administratifs', 'Divers']


def create_managed_cash_page(db, refresh_page):
    service = ManagedCashService(db)
    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    ui.label('Caisse et trésorerie').classes('text-2xl font-bold')
    ui.label('Les ventes au comptant et mouvements saisis ici, ainsi que les règlements fournisseurs liés, alimentent la caisse. '
             'Ventes historiques, crédits, retours et paiements antérieurs hors caisse ne sont pas rapprochés automatiquement.').classes('text-orange-800')
    ui.label('Les soldes des comptes non espèces ne sont pas calculés : seuls leurs flux de session sont affichés.')
    session = service.get_open()
    if not session:
        ui.label('Aucune caisse ouverte.')
        def opening():
            with ui.dialog() as dialog, ui.card():
                ui.label('Ouverture de caisse')
                initial = ui.input('Fonds initial espèces FCFA')
                key = uuid4().hex
                def save():
                    def action():
                        service.open(initial.value, key)
                        dialog.close(); refresh_page(); ui.notify('Caisse ouverte.', type='positive')
                    run(action)
                ui.button('Confirmer ouverture', on_click=save)
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        ui.button('Ouvrir caisse', on_click=opening)
    else:
        ui.label(f'{session.reference} — ouverte le {session.opened_at}')
        ui.label(f'Fonds initial : {session.opening_cash} FCFA — espèces théoriques : {service.cash_available(session)} FCFA')
        for method, totals in service.flows(session.id).items():
            ui.label(f'{METHODS.get(method, method)} — entrées : {totals["in"]} FCFA — sorties : {totals["out"]} FCFA')
        def movement_dialog():
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-xl'):
                ui.label('Mouvement de trésorerie').classes('text-lg font-bold')
                ui.label('Ne saisissez pas ici une vente ou un règlement fournisseur déjà enregistré : cela créerait un doublon.')
                kind = ui.select({key: value for key, value in KINDS.items() if key != 'sale'}, label='Type de mouvement')
                method = ui.select(METHODS, label='Moyen de paiement')
                amount = ui.input('Montant FCFA')
                description = ui.input('Description obligatoire')
                category = ui.select(CATEGORIES, label='Catégorie de dépense (obligatoire pour dépense)')
                beneficiary = ui.input('Bénéficiaire facultatif')
                reference = ui.input('Référence de justificatif facultative')
                key = uuid4().hex
                def save():
                    def action():
                        service.record(session.id, kind.value, method.value, amount.value, description.value, key,
                                       category.value, beneficiary.value, reference.value)
                        dialog.close(); refresh_page(); ui.notify('Mouvement de trésorerie enregistré.', type='positive')
                    run(action)
                ui.button('Enregistrer mouvement', on_click=save)
                ui.button('Fermer mouvement', on_click=dialog.close)
            dialog.open()
        ui.button('Nouvelle dépense ou autre mouvement', on_click=movement_dialog)
        with ui.expansion('Mouvements de la session', icon='receipt').classes('w-full'):
            for entry in sorted(session.entries, key=lambda e: e.id, reverse=True):
                ui.label(f'{entry.date} — Règlement fournisseur — {METHODS.get(entry.method, entry.method)} : {entry.amount} FCFA — paiement #{entry.supplier_payment_id}')
            for entry in db.query(ManagedCashTransaction).filter_by(session_id=session.id).order_by(ManagedCashTransaction.id.desc()).all():
                ui.label(f'{entry.date} — {KINDS.get(entry.kind, entry.kind)} — {METHODS.get(entry.method, entry.method)} : {entry.amount} FCFA — '
                         f'{entry.description} — {entry.category or ""} {entry.beneficiary or ""} {entry.reference or ""}')
        def closing():
            with ui.dialog() as dialog, ui.card():
                ui.label('Clôture de caisse')
                ui.label(f'Espèces théoriques : {service.cash_available(session)} FCFA')
                actual = ui.input('Espèces comptées FCFA')
                notes = ui.input('Commentaire, obligatoire en cas d’écart')
                key = uuid4().hex
                def save():
                    def action():
                        service.close(session.id, actual.value, notes.value, key)
                        dialog.close(); refresh_page(); ui.notify('Caisse clôturée.', type='positive')
                    run(action)
                ui.button('Confirmer clôture', on_click=save)
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        ui.button('Clôturer caisse', on_click=closing)
    ui.label('Dernières clôtures').classes('text-xl font-semibold')
    for item in db.query(ManagedCashSession).filter_by(status='closed').order_by(ManagedCashSession.id.desc()).limit(20):
        ui.label(f'{item.reference} — {item.closed_at} — théorique {item.theoretical_cash} FCFA — '
                 f'compté {item.physical_cash} FCFA — écart {item.difference} FCFA — {item.closing_notes or "sans commentaire"}')
        for method, totals in service.flows(item.id).items():
            ui.label(f'{METHODS.get(method, method)} — entrées : {totals["in"]} FCFA — sorties : {totals["out"]} FCFA')
