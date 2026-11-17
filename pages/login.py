from nicegui import ui
from services.owner_auth_service import OwnerAuthService, PinLocked


def create_login_page(auth: OwnerAuthService, on_login_success):
    setup = not auth.is_configured()
    first_pin = {'value': None}
    digits = []

    with ui.card().classes('w-80 p-8 shadow-xl'):
        with ui.column().classes('w-full gap-4 items-center'):
            ui.label('DEPOTPRO').classes('text-3xl font-bold text-slate-800')
            heading = ui.label('Créez votre PIN à 6 chiffres' if setup else 'Entrez votre PIN')
            display = ui.label('○○○○○○').classes('text-3xl font-mono')
            error = ui.label('').classes('text-red-600 text-sm')

            def clear():
                digits.clear()
                display.text = '○○○○○○'

            async def add(digit):
                if len(digits) >= 6:
                    return
                digits.append(digit)
                display.text = '•' * len(digits) + '○' * (6 - len(digits))
                if len(digits) != 6:
                    return
                pin = ''.join(digits)
                clear()
                try:
                    if setup and first_pin['value'] is None:
                        first_pin['value'] = pin
                        heading.text = 'Confirmez votre PIN'
                        error.text = ''
                        return
                    if setup:
                        auth.setup_pin(first_pin['value'], pin)
                    elif not auth.verify_pin(pin):
                        error.text = 'Code PIN incorrect.'
                        return
                    first_pin['value'] = None
                    await on_login_success()
                except (ValueError, PinLocked) as exc:
                    first_pin['value'] = None
                    if setup:
                        heading.text = 'Créez votre PIN à 6 chiffres'
                    error.text = str(exc)

            with ui.grid(columns=3).classes('gap-2 w-full'):
                for digit in '123456789':
                    ui.button(digit, on_click=lambda d=digit: add(d)).classes('w-full h-14 text-xl')
                ui.button('Effacer', on_click=clear).classes('w-full h-14')
                ui.button('0', on_click=lambda: add('0')).classes('w-full h-14 text-xl')
