import pytest
from models.deposit_configuration import DepositPackagingComponent, DepositPackagingProfile
from models.managed_operations import ManagedSale
from services.deposit_configuration_service import DepositConfigurationService
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import PackagingService
from services.product_service import ProductService
from services.returnable_packaging_service import ReturnablePackagingService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Test')
    product = products.create_product({'name': 'Test', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 48})
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000})
    service = ReturnablePackagingService(db_session)
    crate = service.create(code='C', name='Casier', producer='Test', kind='crate', deposit_value=500)
    bottle = service.create(code='B', name='Bouteille', producer='Test', kind='bottle', deposit_value=50)
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    return product, pack, crate, bottle, cash, session


def test_declaration_et_calcul_sans_valeurs_inventees(db_session, scenario):
    _, pack, crate, bottle, _, _ = scenario
    service = DepositConfigurationService(db_session)
    with pytest.raises(ValueError, match='explicitement'):
        service.quote(pack.id, 1)
    service.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1},
                                           {'returnable_id': bottle.id, 'pieces_per_pack': 24}])
    result = service.quote(pack.id, 2)
    assert {(v['returnable_id'], v['pieces'], v['amount']) for v in result} == {(crate.id, 2, 1000), (bottle.id, 48, 2400)}
    service.configure(pack.id, 'none', [])
    assert service.quote(pack.id, 1) == []
    assert db_session.query(DepositPackagingComponent).count() == 0


def test_configuration_invalide_rollback(db_session, scenario):
    _, pack, crate, bottle, _, _ = scenario
    service = DepositConfigurationService(db_session)
    service.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1}])
    for bad in ([], [{'returnable_id': bottle.id, 'pieces_per_pack': 0}],
                [{'returnable_id': bottle.id, 'pieces_per_pack': '1.5'}],
                [{'returnable_id': bottle.id, 'pieces_per_pack': 1}, {'returnable_id': bottle.id, 'pieces_per_pack': 1}]):
        with pytest.raises(ValueError):
            service.configure(pack.id, 'deposit', bad)
    assert service.quote(pack.id, 1)[0]['returnable_id'] == crate.id


def test_vente_bloquee_si_inconnue_ou_consignee_sans_ecritures(db_session, scenario):
    product, pack, crate, _, cash, session = scenario
    service = DepositConfigurationService(db_session)
    sales = ManagedSaleService(db_session)
    lines = [{'packaging_id': pack.id, 'quantity': 1}]
    with pytest.raises(ValueError, match='explicitement'):
        sales.sell(session.id, 'retail', 'cash', lines, 'unknown')
    service.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1}])
    with pytest.raises(ValueError, match='aperçu'):
        sales.sell(session.id, 'retail', 'cash', lines, 'blocked')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0
    service.configure(pack.id, 'none', [])
    assert sales.sell(session.id, 'retail', 'cash', lines, 'allowed').total == 3000


def test_valeur_manquante_ou_archivage_empeche_la_configuration(db_session, scenario):
    _, pack, crate, _, _, _ = scenario
    service = DepositConfigurationService(db_session)
    unknown = ReturnablePackagingService(db_session).create(code='U', name='Inconnu', producer='Test', kind='crate')
    with pytest.raises(ValueError, match='valeur de consigne'):
        service.configure(pack.id, 'deposit', [{'returnable_id': unknown.id, 'pieces_per_pack': 1}])
    service.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1}])
    ReturnablePackagingService(db_session).archive(crate.id)
    with pytest.raises(ValueError, match='archivé'):
        service.quote(pack.id, 1)


def test_fraction_conditionnement_exige_pieces_entieres(db_session, scenario):
    product, pack, crate, bottle, _, _ = scenario
    PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000,
                                                   'allow_fraction': True}, pack.id)
    service = DepositConfigurationService(db_session)
    service.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1},
                                           {'returnable_id': bottle.id, 'pieces_per_pack': 24}])
    with pytest.raises(ValueError, match='pièces consignées doit être entier'):
        service.quote(pack.id, '0.5')
    service.configure(pack.id, 'deposit', [{'returnable_id': bottle.id, 'pieces_per_pack': 24}])
    assert service.quote(pack.id, '0.5')[0]['pieces'] == 12


def test_vente_credit_consignes_figees_caisse_et_stock(db_session, scenario):
    from models.managed_credit import ManagedCreditSale
    from models.managed_deposit import ManagedDepositIssue
    from services.managed_credit_service import ManagedCreditService
    product, pack, crate, bottle, cash, session = scenario
    deposit = DepositConfigurationService(db_session)
    deposit.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1},
                                           {'returnable_id': bottle.id, 'pieces_per_pack': 24}])
    client = ManagedCreditService(db_session).create_client('Client test', client_type='professionnel', credit_limit=5000)
    quote = deposit.quote(pack.id, 1)
    lines = [{'packaging_id': pack.id, 'quantity': 1, 'expected_unit_price': 3000, 'expected_deposits': quote}]
    payments = [{'method': 'cash', 'amount': 500}, {'method': 'wave', 'amount': 1000}]
    sales = ManagedSaleService(db_session)
    sale = sales.sell(session.id, 'retail', 'credit', lines, 'vente', payments=payments, client_id=client.id)
    assert sales.sell(session.id, 'retail', 'credit', lines, 'vente', payments=payments, client_id=client.id).id == sale.id
    assert sale.total == 4700 and product.stock_quantity == 24
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3200
    assert cash.cash_available(session) == 1500
    issues = db_session.query(ManagedDepositIssue).all()
    assert {(r.returnable_id, r.pieces, r.unit_value, r.amount, r.client_id) for r in issues} == {
        (crate.id, 1, 500, 500, client.id), (bottle.id, 24, 50, 1200, client.id)}
    assert db_session.query(ManagedSale).count() == 1


def test_refuse_consigne_sans_client_ou_apercu_perime(db_session, scenario):
    from services.managed_credit_service import ManagedCreditService
    product, pack, crate, _, cash, session = scenario
    deposit = DepositConfigurationService(db_session)
    deposit.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1}])
    quote = deposit.quote(pack.id, 1)
    line = {'packaging_id': pack.id, 'quantity': 1, 'expected_deposits': quote}
    sales = ManagedSaleService(db_session)
    with pytest.raises(ValueError, match='client actif'):
        sales.sell(session.id, 'retail', 'cash', [line], 'sans-client')
    client = ManagedCreditService(db_session).create_client('Client test', client_type='particulier', no_limit=True)
    crate.deposit_value = 600
    db_session.commit()
    with pytest.raises(ValueError, match='consigne a changé'):
        sales.sell(session.id, 'retail', 'cash', [line], 'perime', client_id=client.id)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0
