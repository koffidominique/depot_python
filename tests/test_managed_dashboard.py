from services.dashboard_service import DashboardService
from services.managed_cash_service import ManagedCashService
from services.managed_credit_service import ManagedCreditService
from services.product_service import ProductService


def test_tableau_de_bord_sans_donnees_puis_actualise(db_session):
    service = DashboardService(db_session)
    initial = service.snapshot()
    assert (initial['active_products'], initial['low_stock'], initial['active_clients'], initial['managed_sales'], initial['managed_credit']) == (0, 0, 0, 0, 0)
    assert initial['cash_reference'] is None and initial['cash_theoretical'] is None
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Boisson', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 2})
    product.min_stock = 3
    db_session.commit()
    ManagedCreditService(db_session).create_client('Client réel', client_type='particulier', no_limit=True)
    session = ManagedCashService(db_session).open(1000, 'caisse')
    snapshot = service.snapshot()
    assert (snapshot['active_products'], snapshot['low_stock'], snapshot['active_clients']) == (1, 1, 1)
    assert snapshot['cash_reference'] == session.reference and snapshot['cash_theoretical'] == 1000
    ManagedCashService(db_session).record(session.id, 'income', 'cash', 500, 'Entrée', 'entree')
    assert service.snapshot()['cash_theoretical'] == 1500
    product.is_active = False
    db_session.commit()
    assert service.snapshot()['active_products'] == service.snapshot()['low_stock'] == 0


def test_ventes_creances_et_annulation_refluent_sur_tableau(db_session):
    from services.deposit_configuration_service import DepositConfigurationService
    from services.managed_sale_service import ManagedSaleService
    from services.packaging_service import PackagingService
    from services.sale_cancellation_service import SaleCancellationService
    service = DashboardService(db_session)
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 10})
    pack = PackagingService(db_session).save(product.id, {'name': 'bouteille', 'coefficient': 1, 'retail_price': 500})
    DepositConfigurationService(db_session).configure(pack.id, 'none', [])
    client = ManagedCreditService(db_session).create_client('Client', client_type='particulier', no_limit=True)
    session = ManagedCashService(db_session).open(0, 'open')
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}], 'sale', client_id=client.id, payments=[])
    assert service.snapshot()['managed_sales'] == 1
    assert service.snapshot()['managed_credit'] == 500
    SaleCancellationService(db_session).cancel(sale.id, session.id, 'Erreur', 'cancel', goods_recovered=True)
    assert service.snapshot()['managed_sales'] == 0
    assert service.snapshot()['managed_credit'] == 0
