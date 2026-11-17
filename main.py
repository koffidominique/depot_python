"""Point d'entrée local ; l'interface métier reste en cours de reconstruction."""
import time
from nicegui import ui
from config import APP_NAME, APP_VERSION
from database import SessionLocal
from init_db import initialize_database
from theme import apply_theme
from components.sidebar import create_sidebar
from pages.login import create_login_page
from pages.advanced_settings import create_advanced_settings_page
from pages.products import create_products_page
from pages.stock import create_stock_page
from pages.managed_cash import create_managed_cash_page
from pages.managed_sales import create_managed_sales_page
from pages.returnable_packaging import create_returnable_packaging_page
from pages.purchases_phase3 import create_purchases_page
from services.owner_auth_service import OwnerAuthService


@ui.page('/')
async def main_page():
    # Chaque client possède son propre état. Les services d'authentification
    # ouvrent une session courte par opération et la ferment systématiquement.
    apply_theme()
    auth = OwnerAuthService(SessionLocal)
    state = {'authenticated': False, 'page': 'dashboard', 'last_activity': time.monotonic(), 'db': None}
    root = ui.column().classes('w-full h-screen p-0 m-0')
    root.on('click', lambda: state.update(last_activity=time.monotonic()), throttle=1.0)
    root.on('keydown', lambda: state.update(last_activity=time.monotonic()), throttle=1.0)
    root.on('mousemove', lambda: state.update(last_activity=time.monotonic()), throttle=5.0)

    def close_db():
        if state['db'] is not None:
            state['db'].close()
            state['db'] = None

    root.client.on_disconnect(close_db)

    def show_login():
        close_db()
        state['authenticated'] = False
        root.clear()
        with root:
            with ui.column().classes('w-full h-screen justify-center items-center bg-gray-100'):
                create_login_page(auth, login_success)

    async def login_success():
        state['authenticated'] = True
        state['last_activity'] = time.monotonic()
        show_main()

    def navigate(page):
        if state['authenticated'] and page in ('dashboard', 'products', 'stock', 'purchases', 'returnables', 'cash', 'sales', 'settings'):
            state['page'] = page
            show_main()

    def show_main():
        if not state['authenticated']:
            return
        close_db()
        root.clear()
        with root:
            with ui.row().classes('w-full h-screen gap-0'):
                create_sidebar(navigate, state['page'])
                with ui.column().classes('flex-1 bg-gray-100 h-full overflow-auto'):
                    with ui.row().classes('w-full bg-white p-4 justify-between items-center'):
                        ui.label(APP_NAME).classes('text-xl font-bold')
                        ui.button('Verrouiller', icon='lock', on_click=show_login)
                    if state['page'] == 'products':
                        state['db'] = SessionLocal()
                        create_products_page(state['db'], lambda: navigate('products'))
                    elif state['page'] == 'stock':
                        state['db'] = SessionLocal()
                        create_stock_page(state['db'], lambda: navigate('stock'))
                    elif state['page'] == 'returnables':
                        state['db'] = SessionLocal()
                        create_returnable_packaging_page(state['db'], lambda: navigate('returnables'))
                    elif state['page'] == 'purchases':
                        state['db'] = SessionLocal()
                        create_purchases_page(state['db'], lambda: navigate('purchases'))
                    elif state['page'] == 'sales':
                        state['db'] = SessionLocal()
                        create_managed_sales_page(state['db'], lambda: navigate('sales'))
                    elif state['page'] == 'cash':
                        state['db'] = SessionLocal()
                        create_managed_cash_page(state['db'], lambda: navigate('cash'))
                    elif state['page'] == 'settings':
                        create_advanced_settings_page(auth)
                    else:
                        with ui.column().classes('p-6 gap-3'):
                            ui.label('Tableau de bord').classes('text-2xl font-bold')
                            ui.label('Les modules commerciaux sont temporairement indisponibles pendant leur sécurisation.').classes('text-slate-700')
                            ui.label('Les données existantes sont conservées.').classes('text-slate-600')

    def check_inactivity():
        if state['authenticated'] and time.monotonic() - state['last_activity'] >= auth.get_inactivity_seconds():
            show_login()
            ui.notify('Application verrouillée après inactivité.', type='warning')

    ui.timer(5, check_inactivity)
    show_login()


def initialize_app():
    initialize_database()


if __name__ in {'__main__', '__mp_main__'}:
    initialize_app()
    ui.run(title=f'{APP_NAME} v{APP_VERSION}', host='127.0.0.1', port=8080,
           reload=False, language='fr')
