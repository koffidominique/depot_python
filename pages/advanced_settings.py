from nicegui import ui
from services.owner_auth_service import OwnerAuthService


def create_advanced_settings_page(auth: OwnerAuthService):
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
