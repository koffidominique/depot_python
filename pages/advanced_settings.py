from nicegui import ui
from services.owner_auth_service import OwnerAuthService


def create_advanced_settings_page(auth: OwnerAuthService, db, refresh_page):
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Sécurité et paramètres').classes('text-2xl font-bold')
        with ui.card().classes('w-full max-w-xl p-5'):
            ui.label('Modifier le PIN').classes('text-lg font-semibold')
            current = ui.input('PIN actuel', password=True, password_toggle_button=True).props('maxlength=6 inputmode=numeric')
            new = ui.input('Nouveau PIN à 6 chiffres', password=True, password_toggle_button=True).props('maxlength=6 inputmode=numeric')
            confirmation = ui.input('Confirmer le nouveau PIN', password=True, password_toggle_button=True).props('maxlength=6 inputmode=numeric')
            def change():
                try:
                    auth.change_pin(current.value, new.value, confirmation.value)
                    ui.notify('PIN modifié.', type='positive')
                except ValueError as exc:
                    ui.notify(str(exc), type='negative')
                finally:
                    current.value = new.value = confirmation.value = ''
            ui.button('Modifier le PIN', on_click=change)
        with ui.card().classes('w-full max-w-xl p-5'):
            ui.label('Verrouillage automatique').classes('text-lg font-semibold')
            minutes = ui.number('Délai en minutes', value=auth.get_inactivity_seconds() // 60, min=1, max=1440, step=1)
            def save_timeout():
                try:
                    if minutes.value is None or int(minutes.value) != minutes.value:
                        raise ValueError('Indiquez un nombre entier de minutes.')
                    auth.set_inactivity_seconds(int(minutes.value) * 60)
                    ui.notify('Délai enregistré.', type='positive')
                except (ValueError, TypeError, OverflowError) as exc:
                    ui.notify(str(exc), type='negative')
            ui.button('Enregistrer le délai', on_click=save_timeout)
        ui.label('Le PIN protège l’accès à l’application, mais ne chiffre pas la base de données.').classes('text-sm text-slate-600')

        from models.payment_method import PaymentMethod
        from services.cash_methods import PaymentMethodService
        with ui.card().classes('w-full max-w-xl p-5'):
            ui.label('Moyens de paiement').classes('text-lg font-semibold')
            ui.label('Les libellés précédents restent associés aux anciennes opérations. Espèces reste toujours disponible.')
            methods = db.query(PaymentMethod).filter_by(active=True).order_by(PaymentMethod.label).all()
            for method in methods:
                ui.label(f'{method.label}' + (' — non modifiable' if method.code == 'cash' else ''))
            name = ui.input('Nom du nouveau moyen de paiement')
            def create_method():
                try:
                    PaymentMethodService(db).create(name.value)
                    refresh_page()
                    ui.notify('Moyen de paiement créé.', type='positive')
                except ValueError as exc:
                    db.rollback()
                    ui.notify(str(exc), type='negative')
            ui.button('Créer moyen de paiement', on_click=create_method)
            choices = {m.code: m.label for m in methods if m.code != 'cash'}
            choice = ui.select(choices, label='Moyen à modifier ou désactiver').classes('w-full')
            renamed = ui.input('Nouveau libellé du moyen')
            def rename_method():
                try:
                    PaymentMethodService(db).rename(choice.value, renamed.value)
                    refresh_page()
                    ui.notify('Moyen de paiement modifié.', type='positive')
                except ValueError as exc:
                    db.rollback()
                    ui.notify(str(exc), type='negative')
            def deactivate_method():
                try:
                    PaymentMethodService(db).deactivate(choice.value)
                    refresh_page()
                    ui.notify('Moyen de paiement désactivé.', type='positive')
                except ValueError as exc:
                    db.rollback()
                    ui.notify(str(exc), type='negative')
            ui.button('Modifier moyen de paiement', on_click=rename_method)
            ui.button('Désactiver moyen de paiement', on_click=deactivate_method)
