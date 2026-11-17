from nicegui import ui
from sqlalchemy.orm import Session
from services.auth_service import AuthService


def create_advanced_settings_page(db: Session, current_user):
    auth_service = AuthService(db)
    
    new_pin_digits = ['', '', '', '']
    confirm_pin_digits = ['', '', '', '']
    new_pin_position = {'value': 0}
    confirm_pin_position = {'value': 0}
    success_message = {'value': ''}
    error_message = {'value': ''}
    
    async def add_new_pin_digit(digit: str):
        if new_pin_position['value'] < 4:
            new_pin_digits[new_pin_position['value']] = digit
            new_pin_position['value'] += 1
            new_pin_display.text = '•' * new_pin_position['value'] + '○' * (4 - new_pin_position['value'])
    
    async def clear_new_pin():
        for i in range(4):
            new_pin_digits[i] = ''
        new_pin_position['value'] = 0
        new_pin_display.text = '○○○○'
    
    async def add_confirm_pin_digit(digit: str):
        if confirm_pin_position['value'] < 4:
            confirm_pin_digits[confirm_pin_position['value']] = digit
            confirm_pin_position['value'] += 1
            confirm_pin_display.text = '•' * confirm_pin_position['value'] + '○' * (4 - confirm_pin_position['value'])
    
    async def clear_confirm_pin():
        for i in range(4):
            confirm_pin_digits[i] = ''
        confirm_pin_position['value'] = 0
        confirm_pin_display.text = '○○○○'
    
    async def save_new_pin():
        success_message['value'] = ""
        error_message['value'] = ""
        
        if new_pin_position['value'] != 4 or confirm_pin_position['value'] != 4:
            error_message['value'] = "Veuillez entrer un code PIN de 4 chiffres dans les deux champs"
            error_label.text = error_message['value']
            return
        
        new_pin = ''.join(new_pin_digits)
        confirm_pin = ''.join(confirm_pin_digits)
        
        if new_pin != confirm_pin:
            error_message['value'] = "Les codes PIN ne correspondent pas"
            error_label.text = error_message['value']
            await clear_new_pin()
            await clear_confirm_pin()
            return
        
        if len(new_pin) != 4 or not new_pin.isdigit():
            error_message['value'] = "Le code PIN doit être composé de 4 chiffres"
            error_label.text = error_message['value']
            await clear_new_pin()
            await clear_confirm_pin()
            return
        
        try:
            auth_service.update_pin_code(current_user.id, new_pin)
            success_message['value'] = "Code PIN modifié avec succès!"
            success_label.text = success_message['value']
            await clear_new_pin()
            await clear_confirm_pin()
        except Exception as e:
            error_message['value'] = f"Erreur lors de la modification: {str(e)}"
            error_label.text = error_message['value']
    
    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Paramètres avancés').classes('text-2xl font-bold text-gray-800')
        
        with ui.card().classes('w-full p-6 mb-4'):
            ui.label('Modifier votre code PIN').classes('text-xl font-semibold text-gray-700 mb-4')
            
            with ui.row().classes('w-full gap-8 mb-4'):
                with ui.column().classes('flex-1 items-center'):
                    ui.label('Nouveau code PIN').classes('text-lg text-gray-600 mb-2')
                    new_pin_display = ui.label('○○○○').classes('text-3xl font-mono text-center text-gray-800 mb-3')
                    with ui.grid(columns=3).classes('gap-2 w-48'):
                        for i in range(1, 10):
                            ui.button(str(i), on_click=lambda d=str(i): add_new_pin_digit(d)).classes('w-full h-12 text-lg font-semibold bg-gray-200 hover:bg-gray-300')
                        ui.button('⌫', on_click=clear_new_pin).classes('w-full h-12 text-lg font-semibold bg-red-200 hover:bg-red-300')
                        ui.button('0', on_click=lambda: add_new_pin_digit('0')).classes('w-full h-12 text-lg font-semibold bg-gray-200 hover:bg-gray-300')
                        ui.button('', on_click=lambda: add_new_pin_digit('')).classes('w-full h-12 text-lg font-semibold bg-gray-100')
                
                with ui.column().classes('flex-1 items-center'):
                    ui.label('Confirmer le code PIN').classes('text-lg text-gray-600 mb-2')
                    confirm_pin_display = ui.label('○○○○').classes('text-3xl font-mono text-center text-gray-800 mb-3')
                    with ui.grid(columns=3).classes('gap-2 w-48'):
                        for i in range(1, 10):
                            ui.button(str(i), on_click=lambda d=str(i): add_confirm_pin_digit(d)).classes('w-full h-12 text-lg font-semibold bg-gray-200 hover:bg-gray-300')
                        ui.button('⌫', on_click=clear_confirm_pin).classes('w-full h-12 text-lg font-semibold bg-red-200 hover:bg-red-300')
                        ui.button('0', on_click=lambda: add_confirm_pin_digit('0')).classes('w-full h-12 text-lg font-semibold bg-gray-200 hover:bg-gray-300')
                        ui.button('', on_click=lambda: add_confirm_pin_digit('')).classes('w-full h-12 text-lg font-semibold bg-gray-100')
            
            error_label = ui.label('').classes('text-red-600 text-sm text-center mb-2')
            success_label = ui.label('').classes('text-green-600 text-sm text-center mb-4')
            
            ui.button('Enregistrer le nouveau code PIN', on_click=save_new_pin, color='blue').classes('bg-blue-600 hover:bg-blue-700')
        
        with ui.card().classes('w-full p-4'):
            ui.label('Informations sur le compte').classes('text-lg font-semibold text-gray-700 mb-3')
            with ui.column().classes('gap-2 text-sm text-gray-600'):
                ui.label(f'Nom d\'utilisateur: {current_user.username}')
                ui.label(f'Nom complet: {current_user.full_name}')
                ui.label(f'Rôle: {current_user.role.value}')
                ui.label(f'Dernière connexion: {current_user.last_login.strftime("%d/%m/%Y %H:%M") if current_user.last_login else "Jamais"}')