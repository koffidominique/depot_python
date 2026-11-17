from services.deposit_configuration_service import DepositConfigurationService
import pytest
from sqlalchemy import event
from models.managed_credit import ManagedCreditSale
from models.managed_operations import ManagedCashTransaction, ManagedSaleLine, ManagedSalePayment, ManagedSaleCancellation
from models.managed_returns import ManagedReturn, ManagedReturnLine, ManagedReturnRefund
from services.managed_cash_service import ManagedCashService
from services.managed_credit_service import ManagedCreditService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import PackagingService
from services.product_service import ProductService
from services.sale_cancellation_service import SaleCancellationService
from services.sale_return_service import SaleReturnService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Test')
    product = products.create_product({'name': 'Eau', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 48})
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000})
    DepositConfigurationService(db_session).configure(pack.id, 'none', [])
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    client = ManagedCreditService(db_session).create_client('Test', client_type='professionnel', credit_limit=5000)
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1}], 'vente',
        payments=[{'method': 'cash', 'amount': 500}, {'method': 'wave', 'amount': 1000}], client_id=client.id)
    return product, cash, session, sale, db_session.query(ManagedCreditSale).one()


def test_retours_partiels_credit_et_paiement_mixte(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = SaleReturnService(db_session)
    args = (sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
            [{'transaction_id': wave.id, 'amount': 500}], 'Retour confirmé', 'retour-1')
    result = service.record(*args, goods_recovered=True)
    assert service.record(*args, goods_recovered=True).id == result.id
    assert result.total == 1000 and credit.remaining_amount == 1000
    assert product.stock_quantity == 32 and cash.cash_available(session) == 1500
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 500}
    assert db_session.query(ManagedReturnRefund).count() == 1
    assert db_session.query(ManagedReturnLine).one().amount == 1000
    ManagedCreditService(db_session).pay(credit.id, session.id, 'cash', 1000, 'remboursement-credit')
    assert credit.remaining_amount == 0
    with pytest.raises(ValueError, match='retour partiel'):
        SaleCancellationService(db_session).cancel(sale.id, session.id, 'tout', 'ann', goods_recovered=True)
    assert db_session.query(ManagedSaleCancellation).count() == 0
    assert db_session.query(ManagedReturn).count() == 1


def test_refuse_retour_excessif_remboursement_incoherent_et_fraction(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = SaleReturnService(db_session)
    with pytest.raises(ValueError, match='entier'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': '0.5'}], 0, [], 'Test', 'fraction', goods_recovered=True)
    with pytest.raises(ValueError, match='supérieure'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 25}], 0, [], 'Test', 'exces', goods_recovered=True)
    with pytest.raises(ValueError, match='correspondre'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500, [], 'Test', 'incoherent', goods_recovered=True)
    with pytest.raises(ValueError, match='supérieur'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 12}], 0, [{'transaction_id': wave.id, 'amount': 1500}], 'Test', 'surplus', goods_recovered=True)
    assert product.stock_quantity == 24 and credit.remaining_amount == 1500 and cash.cash_available(session) == 1500
    assert db_session.query(ManagedReturn).count() == 0


def test_rollback_retour_si_remboursement_echoue(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    def fail(_mapper, _connection, target):
        if target.kind == 'outflow':
            raise RuntimeError('échec remboursement')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échec'):
            SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
                [{'transaction_id': wave.id, 'amount': 500}], 'Test', 'retour', goods_recovered=True)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 24 and credit.remaining_amount == 1500
    assert db_session.query(ManagedReturn).count() == db_session.query(ManagedReturnRefund).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 2


def test_retours_successifs_ne_peuvent_surrembourser_ou_surretourner(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = SaleReturnService(db_session)
    service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
                   [{'transaction_id': wave.id, 'amount': 500}], 'Premier', 'r1', goods_recovered=True)
    with pytest.raises(ValueError, match='supérieure'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 17}], 0, [], 'Trop', 'r2', goods_recovered=True)
    with pytest.raises(ValueError, match='supérieur'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 0,
                       [{'transaction_id': wave.id, 'amount': 1000}], 'Trop', 'r3', goods_recovered=True)
    service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
                   [{'transaction_id': wave.id, 'amount': 500}], 'Second', 'r4', goods_recovered=True)
    assert credit.remaining_amount == 500 and product.stock_quantity == 40
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 1000}
    assert db_session.query(ManagedReturn).count() == 2


def test_retour_caisse_espèces_et_interdiction_retour_vente_annulee(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    cash_entry = db_session.query(ManagedCashTransaction).filter_by(method='cash').one()
    service = SaleReturnService(db_session)
    service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 4}], 0,
                   [{'transaction_id': cash_entry.id, 'amount': 500}], 'Retour espèces', 'r1', goods_recovered=True)
    assert product.stock_quantity == 28 and cash.cash_available(session) == 1000
    assert credit.remaining_amount == 1500
    # Une vente intégralement annulée ne peut pas être retournée à nouveau.
    pack_id = line.packaging_id
    sale2 = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack_id, 'quantity': 1}], 'vente2')
    line2 = db_session.query(ManagedSaleLine).filter_by(sale_id=sale2.id).one()
    SaleCancellationService(db_session).cancel(sale2.id, session.id, 'Retour complet', 'ann2', goods_recovered=True)
    with pytest.raises(ValueError, match='déjà annulée'):
        service.record(sale2.id, session.id, [{'sale_line_id': line2.id, 'base_quantity': 1}], 0, [], 'Test', 'r2', goods_recovered=True)


def test_annulation_retour_credit_mixte_puis_annulation_totale(db_session, scenario):
    from models.managed_returns import ManagedReturnCancellation, ManagedReturnRecapture
    from services.return_cancellation_service import ReturnCancellationService
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    returned = SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
        [{'transaction_id': wave.id, 'amount': 500}], 'Retour', 'r1', goods_recovered=True)
    service = ReturnCancellationService(db_session)
    cancellation = service.cancel(returned.id, session.id, 'Erreur de retour', 'ar1', goods_and_refunds_recovered=True)
    assert service.cancel(returned.id, session.id, 'Erreur de retour', 'ar1', goods_and_refunds_recovered=True).id == cancellation.id
    assert product.stock_quantity == 24 and credit.remaining_amount == 1500
    assert cash.flows(session.id)['wave'] == {'in': 1500, 'out': 500}
    assert db_session.query(ManagedReturnCancellation).count() == db_session.query(ManagedReturnRecapture).count() == 1
    with pytest.raises(ValueError, match='déjà annulé'):
        service.cancel(returned.id, session.id, 'Autre', 'ar2', goods_and_refunds_recovered=True)
    SaleCancellationService(db_session).cancel(sale.id, session.id, 'Annulation vente', 'as', goods_recovered=True)
    assert product.stock_quantity == 48 and credit.remaining_amount == 0
    assert cash.flows(session.id)['wave'] == {'in': 1500, 'out': 1500}
    assert cash.cash_available(session) == 1000


def test_annulation_retour_puis_nouveau_retour_utilise_solde_disponible(db_session, scenario):
    from services.return_cancellation_service import ReturnCancellationService
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = SaleReturnService(db_session)
    args = (sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
            [{'transaction_id': wave.id, 'amount': 500}], 'Retour', 'r1')
    returned = service.record(*args, goods_recovered=True)
    ReturnCancellationService(db_session).cancel(returned.id, session.id, 'Correction', 'ar1', goods_and_refunds_recovered=True)
    second = service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
        [{'transaction_id': wave.id, 'amount': 500}], 'Nouveau retour', 'r2', goods_recovered=True)
    assert second.total == 1000 and product.stock_quantity == 32 and credit.remaining_amount == 1000
    assert cash.flows(session.id)['wave'] == {'in': 1500, 'out': 1000}


def test_annulation_retour_refuse_stock_ulterieur_et_manque_confirmation(db_session, scenario):
    from services.return_cancellation_service import ReturnCancellationService
    from services.stock_service import StockService
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    returned = SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
        [{'transaction_id': wave.id, 'amount': 500}], 'Retour', 'r1', goods_recovered=True)
    service = ReturnCancellationService(db_session)
    with pytest.raises(ValueError, match='Confirmez'):
        service.cancel(returned.id, session.id, 'Erreur', 'ar')
    assert StockService(db_session).update_stock(product.id, 1, 'test', unit='bouteille')
    with pytest.raises(ValueError, match='ultérieur'):
        service.cancel(returned.id, session.id, 'Erreur', 'ar', goods_and_refunds_recovered=True)
    assert product.stock_quantity == 33 and credit.remaining_amount == 1000
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 500}


def test_annulation_retour_rollback_si_reecriture_caisse_echoue(db_session, scenario):
    from models.managed_returns import ManagedReturnCancellation, ManagedReturnRecapture
    from services.return_cancellation_service import ReturnCancellationService
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    returned = SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
        [{'transaction_id': wave.id, 'amount': 500}], 'Retour', 'r1', goods_recovered=True)
    def fail(_mapper, _connection, target):
        if target.kind == 'income' and target.reference and target.reference.startswith('ANNULATION-RETOUR-'):
            raise RuntimeError('échec de caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échec'):
            ReturnCancellationService(db_session).cancel(returned.id, session.id, 'Erreur', 'ar', goods_and_refunds_recovered=True)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert product.stock_quantity == 32 and credit.remaining_amount == 1000
    assert db_session.query(ManagedReturnCancellation).count() == db_session.query(ManagedReturnRecapture).count() == 0


def test_annulation_totale_apres_retour_sans_double_restitution(db_session, scenario):
    product, cash, session, sale, credit = scenario
    line = db_session.query(ManagedSaleLine).one()
    cash_payment = db_session.query(ManagedCashTransaction).filter_by(method='cash').one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = SaleReturnService(db_session)
    service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
                   [{'transaction_id': wave.id, 'amount': 500}], 'Premier retour', 'r1', goods_recovered=True)
    remaining = [{'sale_line_id': line.id, 'base_quantity': 16}]
    refunds = [{'transaction_id': wave.id, 'amount': 500}, {'transaction_id': cash_payment.id, 'amount': 500}]
    with pytest.raises(ValueError, match='toutes les quantités'):
        service.record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 500,
                       [{'transaction_id': wave.id, 'amount': 500}], 'Incomplet', 'r2', goods_recovered=True, cancel_sale=True)
    result = service.record(sale.id, session.id, remaining, 1000, refunds, 'Annulation complète', 'r3', goods_recovered=True, cancel_sale=True)
    assert service.record(sale.id, session.id, remaining, 1000, refunds, 'Annulation complète', 'r3', goods_recovered=True, cancel_sale=True).id == result.id
    assert product.stock_quantity == 48 and credit.remaining_amount == 0
    assert cash.cash_available(session) == 1000
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 1000}
    assert db_session.query(ManagedReturn).count() == 2 and db_session.query(ManagedSaleCancellation).count() == 1
    with pytest.raises(ValueError, match='déjà annulée'):
        service.record(sale.id, session.id, remaining, 1000, refunds, 'Reprise', 'r4', goods_recovered=True)


def test_annulation_retour_retablit_cout_moyen_exact(db_session):
    from fractions import Fraction
    from services.return_cancellation_service import ReturnCancellationService
    products = ProductService(db_session)
    category = products.create_category('Boissons')
    product = products.create_product({'name': 'Test', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 48})
    product.average_cost_numerator, product.average_cost_denominator = '100', '1'
    db_session.commit()
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000})
    DepositConfigurationService(db_session).configure(pack.id, 'none', [])
    session = ManagedCashService(db_session).open(0, 'open')
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1}], 'vente')
    product.average_cost_numerator = '200'
    db_session.commit()
    line = db_session.query(ManagedSaleLine).one()
    payment = db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).one()
    returned = SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': line.id, 'base_quantity': 8}], 0,
        [{'transaction_id': payment.id, 'amount': 1000}], 'Retour', 'r', goods_recovered=True)
    assert product.average_cost == Fraction(175)
    ReturnCancellationService(db_session).cancel(returned.id, session.id, 'Erreur', 'ar', goods_and_refunds_recovered=True)
    assert product.stock_quantity == 24 and product.average_cost == Fraction(200)
