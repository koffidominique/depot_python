from nicegui import ui, app
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from config import APP_NAME, APP_VERSION
from theme import apply_theme
from components.sidebar import create_sidebar
from components.header import create_header
from pages.dashboard import create_dashboard_page
from pages.products import create_products_page
from pages.stock import create_stock_page
from pages.sales import create_sales_page
from pages.clients import create_clients_page
from pages.suppliers import create_suppliers_page
from pages.purchases import create_purchases_page
from pages.cash import create_cash_page
from pages.reports import create_reports_page
from pages.settings import create_settings_page
from pages.advanced_settings import create_advanced_settings_page
from pages.login import create_login_page
from pages.new_sale import create_new_sale_page
from pages.deliveries import create_deliveries_page
from pages.debts import create_debts_page
from pages.consignations import create_consignations_page
from pages.expenses import create_expenses_page
from pages.inventory import create_inventory_page
from pages.users import create_users_page
from services.auth_service import AuthService


db: Session = None
current_user = None
current_page = {'value': 'dashboard'}
page_content = None


def get_db():
    global db
    if not db:
        db = SessionLocal()
    return db


def navigate_to(page_name: str):
    global current_page, page_content
    current_page['value'] = page_name
    if page_content:
        page_content.clear()
    render_page()


def render_page():
    global page_content
    db = get_db()
    page_content.clear()
    
    with page_content:
        if current_page['value'] == 'dashboard':
            create_dashboard_page(db)
        elif current_page['value'] == 'products':
            create_products_page(db)
        elif current_page['value'] == 'stock':
            create_stock_page(db)
        elif current_page['value'] == 'sales':
            create_sales_page(db)
        elif current_page['value'] == 'clients':
            create_clients_page(db)
        elif current_page['value'] == 'suppliers':
            create_suppliers_page(db)
        elif current_page['value'] == 'purchases':
            create_purchases_page(db)
        elif current_page['value'] == 'cash':
            create_cash_page(db)
        elif current_page['value'] == 'reports':
            create_reports_page(db)
        elif current_page['value'] == 'settings':
            create_settings_page(db)
        elif current_page['value'] == 'advanced_settings':
            create_advanced_settings_page(db, current_user)
        elif current_page['value'] == 'new_sale':
            create_new_sale_page(db)
        elif current_page['value'] == 'deliveries':
            create_deliveries_page(db)
        elif current_page['value'] == 'debts':
            create_debts_page(db)
        elif current_page['value'] == 'consignations':
            create_consignations_page(db)
        elif current_page['value'] == 'expenses':
            create_expenses_page(db)
        elif current_page['value'] == 'inventory':
            create_inventory_page(db)
        elif current_page['value'] == 'users':
            create_users_page(db)


async def on_login_success(user):
    global current_user
    current_user = user
    await render_main_app()


async def render_main_app():
    global page_content
    page_content.clear()
    
    with ui.row().classes('w-full h-screen gap-0 p-0 m-0'):
        with ui.column().classes('w-64 h-full bg-gray-800 text-white p-0 m-0'):
            create_sidebar(navigate_to, current_page)
        
        with ui.column().classes('flex-1 h-full bg-gray-100 p-0 m-0 overflow-auto'):
            create_header(current_user)
            page_content = ui.column().classes('w-full flex-1 overflow-auto')
            render_page()


async def render_login_page():
    global page_content
    page_content.clear()
    db = get_db()
    
    with ui.column().classes('w-full h-screen justify-center items-center bg-gray-200'):
        create_login_page(db, on_login_success)


@ui.page('/')
async def main_page():
    global page_content
    apply_theme()
    
    with ui.column().classes('w-full h-screen p-0 m-0'):
        page_content = ui.column().classes('w-full h-full p-0 m-0')
    
    await render_login_page()


def initialize_app():
    init_db()
    from init_db import initialize_database
    initialize_database()


if __name__ in {'__main__', '__mp_main__'}:
    initialize_app()
    ui.run(
        title=f"{APP_NAME} v{APP_VERSION}",
        port=8080,
        reload=False
    )