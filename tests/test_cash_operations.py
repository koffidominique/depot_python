from services.deposit_configuration_service import DepositConfigurationService
import pytest
from sqlalchemy import event
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedCashTransaction
from models.stock import StockMovement
from services.managed_cash_service import ManagedCashService
from services.managed_sale_service import ManagedSaleService
from services.product_service import ProductService
from services.packaging_service import PackagingService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Eau', 'unit': 'bouteille', 'category_id': category.id, 'stock_quantity': 48})
    packaging = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000, 'wholesale_price': 2400})
    DepositConfigurationService(db_session).configure(packaging.id, 'none', [])
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    return product, packaging, cash, session


def test_vente_comptant_et_flux_distincts(db_session, scenario):
    product, packaging, cash, session = scenario
    sale_service = ManagedSaleService(db_session)
    args = dict(session_id=session.id, mode='wholesale', method='cash', lines=[{'packaging_id': packaging.id, 'quantity': 1}], request_key='sale')
    sale = sale_service.sell(**args)
    assert sale_service.sell(**args).id == sale.id
    assert sale.total == 2400 and product.stock_quantity == 24
    assert db_session.query(StockMovement).filter_by(reference_document=sale.reference).one().quantity == -24
    assert db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).count() == 1
    assert cash.cash_available(session) == 3400
    cash.record(session.id, 'expense', 'cash', 600, 'Carburant tricycle', 'exp', category='Carburant')
    cash.record(session.id, 'income', 'wave', 200, 'Recette diverse', 'income')
    assert cash.cash_available(session) == 2800
    assert cash.flows(session.id) == {'cash': {'in': 2400, 'out': 600}, 'wave': {'in': 200, 'out': 0}}
    cash.close(session.id, 2800, '', 'close')
    assert session.theoretical_cash == 2800 and session.difference == 0


def test_vente_rollback_si_caisse_echoue(db_session, scenario):
    product, packaging, _, session = scenario
    def fail(_mapper, _connection, target):
        if target.kind == 'sale':
            raise RuntimeError('erreur de caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='erreur'):
            ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': packaging.id, 'quantity': 1}], 's1')
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 48
    assert db_session.query(ManagedSale).count() == db_session.query(ManagedSaleLine).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 0
    assert db_session.query(StockMovement).filter_by(movement_type='sale').count() == 0


def test_ventes_et_depenses_invalides(db_session, scenario):
    product, pack, cash, session = scenario
    sell = ManagedSaleService(db_session)
    with pytest.raises(ValueError, match='Stock insuffisant'):
        sell.sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 3}], 'trop')
    with pytest.raises(ValueError, match='Tarif non configuré'):
        sell.sell(session.id, 'semi_wholesale', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'tarif')
    with pytest.raises(ValueError, match='catégorie'):
        cash.record(session.id, 'expense', 'cash', 10, 'test', 'x')
    with pytest.raises(ValueError, match='insuffisantes'):
        cash.record(session.id, 'expense', 'cash', 1001, 'test', 'y', category='Test')
    with pytest.raises(ValueError, match='entier'):
        cash.record(session.id, 'income', 'cash', '1.5', 'test', 'z')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000


def test_mouvement_idempotent_et_cloture(db_session, scenario):
    _, _, cash, session = scenario
    entry = cash.record(session.id, 'expense', 'cash', 200, 'Transport', 'cle', category='Transport')
    assert cash.record(session.id, 'expense', 'cash', 200, 'Transport', 'cle', category='Transport').id == entry.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        cash.record(session.id, 'expense', 'cash', 300, 'Transport', 'cle', category='Transport')
    cash.close(session.id, 800, '', 'close')
    with pytest.raises(ValueError, match='ouverte'):
        cash.record(session.id, 'income', 'cash', 100, 'Autre', 'nouveau')
    assert db_session.query(ManagedCashTransaction).count() == 1


def test_prix_modifie_depuis_apercu_refuse_et_rollback(db_session, scenario):
    product, pack, cash, session = scenario
    lines = [{'packaging_id': pack.id, 'quantity': 1, 'expected_unit_price': 2000}]
    with pytest.raises(ValueError, match='tarif a changé'):
        ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', lines, 'prix')
    assert product.stock_quantity == 48
    assert cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0


def test_vente_produit_a_consigne_non_prise_en_charge_refusee(db_session, scenario):
    product, pack, cash, session = scenario
    product.consignment_value = 100
    db_session.commit()
    with pytest.raises(ValueError, match='consigne'):
        ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'consigne')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000


def test_vente_prix_ajuste_persiste_et_idempotent(db_session, scenario):
    product, pack, cash, session = scenario
    service = ManagedSaleService(db_session)
    line = {'packaging_id': pack.id, 'quantity': 1, 'expected_unit_price': 3000, 'unit_price': 2750}
    sale = service.sell(session.id, 'retail', 'cash', [line], 'prix-ajuste')
    assert sale.total == 2750 and cash.cash_available(session) == 3750
    assert product.stock_quantity == 24
    assert db_session.query(ManagedSaleLine).filter_by(sale_id=sale.id).one().unit_price == 2750
    assert service.sell(session.id, 'retail', 'cash', [line], 'prix-ajuste').id == sale.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        service.sell(session.id, 'retail', 'cash', [{**line, 'unit_price': 2700}], 'prix-ajuste')
    PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 4000}, pack.id)
    assert db_session.query(ManagedSaleLine).filter_by(sale_id=sale.id).one().unit_price == 2750


def test_prix_ajuste_invalide_tarif_perime_et_fraction_refuses(db_session, scenario):
    product, pack, cash, session = scenario
    service = ManagedSaleService(db_session)
    base = {'packaging_id': pack.id, 'quantity': 1, 'expected_unit_price': 3000}
    for value in (-1, '2.5'):
        with pytest.raises(ValueError):
            service.sell(session.id, 'retail', 'cash', [{**base, 'unit_price': value}], f'invalide-{value}')
    with pytest.raises(ValueError, match='tarif configuré'):
        service.sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1, 'unit_price': 100}], 'sans-apercu')
    with pytest.raises(ValueError, match='tarif a changé'):
        service.sell(session.id, 'retail', 'cash', [{**base, 'expected_unit_price': 2999, 'unit_price': 2500}], 'perime')
    PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000,
                                                  'allow_fraction': True}, pack.id)
    with pytest.raises(ValueError, match='entier'):
        service.sell(session.id, 'retail', 'cash', [{**base, 'quantity': '0.5', 'unit_price': 3}], 'fraction')
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 0


def test_vente_paiements_mixtes_flux_liens_et_idempotence(db_session, scenario):
    from models.managed_operations import ManagedSalePayment
    product, pack, cash, session = scenario
    service = ManagedSaleService(db_session)
    lines = [{'packaging_id': pack.id, 'quantity': 1}]
    payments = [{'method': 'wave', 'amount': 2000}, {'method': 'cash', 'amount': 1000}]
    sale = service.sell(session.id, 'retail', 'mixed', lines, 'split', payments=payments)
    assert sale.total == 3000 and sale.payment_method == 'mixed' and product.stock_quantity == 24
    assert cash.cash_available(session) == 2000
    assert cash.flows(session.id) == {'cash': {'in': 1000, 'out': 0}, 'wave': {'in': 2000, 'out': 0}}
    links = db_session.query(ManagedSalePayment).filter_by(sale_id=sale.id).all()
    assert len(links) == 2
    movements = [db_session.get(ManagedCashTransaction, link.transaction_id) for link in links]
    assert {(m.method, m.amount) for m in movements} == {('cash', 1000), ('wave', 2000)}
    assert service.sell(session.id, 'retail', 'mixed', lines, 'split', payments=list(reversed(payments))).id == sale.id
    with pytest.raises(ValueError, match='déjà été utilisée'):
        service.sell(session.id, 'retail', 'mixed', lines, 'split', payments=[{'method': 'cash', 'amount': 2000}, {'method': 'wave', 'amount': 1000}])
    assert db_session.query(ManagedCashTransaction).count() == 2


@pytest.mark.parametrize('payments', [
    [{'method': 'cash', 'amount': 1000}, {'method': 'wave', 'amount': 1999}],
    [{'method': 'cash', 'amount': 1000}, {'method': 'wave', 'amount': 2001}],
    [{'method': 'cash', 'amount': 0}, {'method': 'wave', 'amount': 3000}],
    [{'method': 'cash', 'amount': '0.5'}, {'method': 'wave', 'amount': 3000}],
    [{'method': 'cash', 'amount': 1000}, {'method': 'cash', 'amount': 2000}],
    [{'method': 'cash', 'amount': 3000}],
])
def test_vente_mixte_invalide_rollback(db_session, scenario, payments):
    product, pack, cash, session = scenario
    with pytest.raises(ValueError):
        ManagedSaleService(db_session).sell(session.id, 'retail', 'mixed', [{'packaging_id': pack.id, 'quantity': 1}], 'invalide', payments=payments)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 0


def test_vente_mixte_rollback_erreur_deuxieme_mouvement(db_session, scenario):
    from models.managed_operations import ManagedSalePayment
    product, pack, cash, session = scenario
    def fail(_mapper, _connection, target):
        if target.method == 'wave':
            raise RuntimeError('erreur caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='erreur caisse'):
            ManagedSaleService(db_session).sell(session.id, 'retail', 'mixed', [{'packaging_id': pack.id, 'quantity': 1}],
                'split-fail', payments=[{'method': 'cash', 'amount': 1000}, {'method': 'wave', 'amount': 2000}])
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == db_session.query(ManagedSalePayment).count() == db_session.query(ManagedCashTransaction).count() == 0


def test_annulation_vente_mixte_rembourse_et_restaure_stock(db_session, scenario):
    from models.managed_operations import ManagedSaleCancellation, ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'mixed', [{'packaging_id': pack.id, 'quantity': 1}],
        'vente-annulable', payments=[{'method': 'cash', 'amount': 1000}, {'method': 'wave', 'amount': 2000}])
    service = SaleCancellationService(db_session)
    cancellation = service.cancel(sale.id, session.id, 'Marchandise récupérée', 'annulation', goods_recovered=True)
    assert service.cancel(sale.id, session.id, 'Marchandise récupérée', 'annulation', goods_recovered=True).id == cancellation.id
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert cash.flows(session.id) == {'cash': {'in': 1000, 'out': 1000}, 'wave': {'in': 2000, 'out': 2000}}
    assert db_session.get(ManagedSale, sale.id).total == 3000
    assert db_session.query(ManagedSaleCancellation).count() == 1
    assert db_session.query(ManagedSaleRefund).count() == 2
    assert db_session.query(StockMovement).filter_by(reference_document=f'ANNULATION-{cancellation.id}').one().quantity == 24
    with pytest.raises(ValueError, match='déjà annulée'):
        service.cancel(sale.id, session.id, 'autre motif', 'autre-cle', goods_recovered=True)


def test_annulation_refuse_sans_stock_recupere_ou_especes(db_session, scenario):
    from models.managed_operations import ManagedSaleCancellation, ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'vente')
    service = SaleCancellationService(db_session)
    with pytest.raises(ValueError, match='récupérés'):
        service.cancel(sale.id, session.id, 'erreur', 'sans-stock')
    cash.record(session.id, 'outflow', 'cash', 4000, 'Dépôt bancaire', 'sortie')
    with pytest.raises(ValueError, match='insuffisantes'):
        service.cancel(sale.id, session.id, 'erreur', 'sans-cash', goods_recovered=True)
    assert product.stock_quantity == 24 and cash.cash_available(session) == 0
    assert db_session.query(ManagedSaleCancellation).count() == db_session.query(ManagedSaleRefund).count() == 0


def test_annulation_rollback_si_remboursement_echoue(db_session, scenario):
    from models.managed_operations import ManagedSaleCancellation, ManagedSaleRefund
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'mixed', [{'packaging_id': pack.id, 'quantity': 1}],
        'vente', payments=[{'method': 'cash', 'amount': 1000}, {'method': 'wave', 'amount': 2000}])
    def fail(_mapper, _connection, target):
        if target.kind == 'outflow' and target.method == 'wave':
            raise RuntimeError('remboursement échoué')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échoué'):
            SaleCancellationService(db_session).cancel(sale.id, session.id, 'Test', 'annulation', goods_recovered=True)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 24 and cash.cash_available(session) == 2000
    assert db_session.query(ManagedSaleCancellation).count() == db_session.query(ManagedSaleRefund).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 2


def test_annulation_revalorise_retour_cout_historique(db_session, scenario):
    from fractions import Fraction
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session = scenario
    product.average_cost_numerator, product.average_cost_denominator = '100', '1'
    db_session.commit()
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'vente')
    product.average_cost_numerator = '200'  # coût du stock encore présent après une réception
    db_session.commit()
    SaleCancellationService(db_session).cancel(sale.id, session.id, 'Retour intégral', 'annulation', goods_recovered=True)
    assert product.stock_quantity == 48 and product.average_cost == Fraction(150)


def test_annulation_dans_session_suivante_sans_modifier_cloture(db_session, scenario):
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, first = scenario
    sale = ManagedSaleService(db_session).sell(first.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 's')
    cash.close(first.id, 4000, '', 'close')
    second = cash.open(4000, 'open-next')
    SaleCancellationService(db_session).cancel(sale.id, second.id, 'Retour confirmé', 'ann', goods_recovered=True)
    assert first.theoretical_cash == 4000 and first.physical_cash == 4000
    assert cash.cash_available(second) == 1000 and product.stock_quantity == 48


def test_annulation_refuse_historique_incoherent(db_session, scenario):
    from services.sale_cancellation_service import SaleCancellationService
    product, pack, cash, session = scenario
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 's')
    db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).one().amount = 2999
    db_session.commit()
    with pytest.raises(ValueError, match='incohérents'):
        SaleCancellationService(db_session).cancel(sale.id, session.id, 'Retour confirmé', 'ann', goods_recovered=True)
    assert product.stock_quantity == 24
    assert db_session.query(ManagedSale).count() == 1
