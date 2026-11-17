"""Tableau de bord local : uniquement les données présentes dans la base."""
from nicegui import ui
from services.dashboard_service import DashboardService


def create_managed_dashboard_page(db, refresh_page):
    data = DashboardService(db).snapshot()
    with ui.column().classes('p-6 gap-3 w-full'):
        ui.label('Tableau de bord').classes('text-2xl font-bold')
        ui.label('Données locales actuelles. Ventes, créances et caisse : nouveau circuit uniquement ; historiques non rapprochés exclus.')
        ui.button('Actualiser le tableau de bord', on_click=refresh_page)
        with ui.row().classes('w-full gap-4'):
            for title, value in (
                ('Produits actifs', data['active_products']),
                ('Produits au seuil minimum', data['low_stock']),
                ('Clients actifs', data['active_clients']),
                ('Ventes non annulées — nouveau circuit', data['managed_sales']),
                ('Créances restantes — nouveau circuit', f"{data['managed_credit']} FCFA"),
            ):
                with ui.card():
                    ui.label(title)
                    ui.label(str(value)).classes('text-xl font-bold')
        ui.label('Alertes stock : produits actifs dont le seuil minimum est renseigné et supérieur à zéro.')
        if data['cash_reference']:
            ui.label(f"Caisse ouverte {data['cash_reference']} — espèces théoriques : {data['cash_theoretical']} FCFA")
            ui.label('Espèces théoriques calculées, non comptage physique ; soldes non espèces non vérifiés.')
        else:
            ui.label('Aucune caisse du nouveau circuit ouverte.')
