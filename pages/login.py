from nicegui import ui
from sqlalchemy.orm import Session
from services.auth_service import AuthService


def create_login_page(db: Session, on_login_success):
    auth_service = AuthService(db)
    
    pin_digits = ['', '', '', '']
    current_position = {'value': 0}
    error_message = {'value': ''}
    
    async def add_digit(digit: str):
        if current_position['value'] < 4:
            pin_digits[current_position['value']] = digit
            current_position['value'] += 1
            pin_display.text = '•' * current_position['value'] + '○' * (4 - current_position['value'])
            
            if current_position['value'] == 4:
                entered_pin = ''.join(pin_digits)
                user = auth_service.authenticate_by_pin(entered_pin)
                if user:
                    error_message['value'] = ""
                    await on_login_success(user)
                else:
                    error_message['value'] = "Code PIN incorrect"
                    error_label.text = error_message['value']
                    await clear_pin()
    
    async def clear_pin():
        for i in range(4):
            pin_digits[i] = ''
        current_position['value'] = 0
        pin_display.text = '○○○○'
    
    with ui.card().classes('w-80 p-8 shadow-xl'):
        with ui.column().classes('w-full gap-4 items-center'):
            ui.label('DEPOTPRO ERP').classes('text-3xl font-bold text-center text-gray-800 mb-2')
            ui.label('Entrez votre code PIN').classes('text-lg text-gray-600 mb-4')
            
            pin_display = ui.label('○○○○').classes('text-3xl font-mono text-center text-gray-800 mb-4')
            
            error_label = ui.label('').classes('text-red-600 text-sm text-center mb-2')
            
            with ui.grid(columns=3).classes('gap-2 w-full'):
                for i in range(1, 10):
                    ui.button(str(i), on_click=lambda d=str(i): add_digit(d)).classes('w-full h-14 text-xl font-semibold bg-gray-200 hover:bg-gray-300')
                ui.button('⌫', on_click=clear_pin).classes('w-full h-14 text-xl font-semibold bg-red-200 hover:bg-red-300')
                ui.button('0', on_click=lambda: add_digit('0')).classes('w-full h-14 text-xl font-semibold bg-gray-200 hover:bg-gray-300')
                ui.button('✓', on_click=lambda: add_digit('')).classes('w-full h-14 text-xl font-semibold bg-blue-600 hover:bg-blue-700 text-white')
            
            ui.label('Code PIN par défaut: 0000').classes('text-xs text-center text-gray-500 mt-4')