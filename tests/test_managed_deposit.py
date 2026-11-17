import pytest
from sqlalchemy import event
from models.managed_credit import ManagedCreditSale
from models.managed_deposit import ManagedDepositIssue, ManagedDepositReturn, ManagedDepositRefund
from models.managed_operations import ManagedCashTransaction, ManagedSale, ManagedSaleLine
from models.returnable_stock import ReturnableStockBalance, ReturnableStockMovement
from services.deposit_configuration_service import DepositConfigurationService
from services.managed_cash_service import ManagedCashService
from services.managed_credit_service import ManagedCreditService
from services.managed_deposit_service import ManagedDepositService
from services.managed_sale_service import ManagedSaleService
from services.packaging_service import PackagingService
from services.product_service import ProductService
from services.returnable_packaging_service import ReturnablePackagingService
from services.returnable_stock_service import ReturnableStockService
from services.sale_return_service import SaleReturnService
from services.sale_cancellation_service import SaleCancellationService


@pytest.fixture
def scenario(db_session):
    products = ProductService(db_session)
    category = products.create_category('Test')
    product = products.create_product({'name': 'Boisson', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 48})
    pack = PackagingService(db_session).save(product.id, {'name': 'casier', 'coefficient': 24, 'retail_price': 3000})
    catalogue = ReturnablePackagingService(db_session)
    crate = catalogue.create(code='CAS', name='Casier', producer='Test', kind='crate', deposit_value=500)
    bottle = catalogue.create(code='BOT', name='Bouteille', producer='Test', kind='bottle', deposit_value=50)
    deposit = DepositConfigurationService(db_session)
    deposit.configure(pack.id, 'deposit', [{'returnable_id': crate.id, 'pieces_per_pack': 1}, {'returnable_id': bottle.id, 'pieces_per_pack': 24}])
    client = ManagedCreditService(db_session).create_client('Client', client_type='professionnel', credit_limit=5000)
    cash = ManagedCashService(db_session)
    session = cash.open(1000, 'open')
    return product, pack, crate, bottle, client, cash, session


def create_credit(db, scenario):
    product, pack, crate, bottle, client, cash, session = scenario
    quote = DepositConfigurationService(db).quote(pack.id, 1)
    sale = ManagedSaleService(db).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1,
        'expected_unit_price': 3000, 'expected_deposits': quote}], 'vente', client_id=client.id,
        payments=[{'method': 'cash', 'amount': 500}, {'method': 'wave', 'amount': 1000}])
    return sale


def test_retour_vides_credit_mixte_et_soldes_separes(db_session, scenario):
    product, pack, crate, bottle, client, cash, session = scenario
    sale = create_credit(db_session, scenario)
    assert sale.total == 4700 and product.stock_quantity == 24
    assert db_session.get(ReturnableStockBalance, crate.id) is None
    stock = ReturnableStockService(db_session)
    stock.record(crate.id, 'initial', 0, 'Comptage', 'init-c')
    stock.record(bottle.id, 'initial', 0, 'Comptage', 'init-b')
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    credit = db_session.query(ManagedCreditSale).one()
    service = ManagedDepositService(db_session)
    args = (issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Casier récupéré', 'r-c')
    returned = service.return_empty(*args, received=True)
    assert service.return_empty(*args, received=True).id == returned.id
    assert stock.balance(crate.id) == 1 and product.stock_quantity == 24
    assert credit.remaining_amount == 3000 and cash.cash_available(session) == 1500
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 300}
    assert db_session.get(ReturnableStockMovement, returned.stock_movement_id).quantity == 1
    assert db_session.query(ManagedDepositRefund).count() == 1
    with pytest.raises(ValueError, match='supérieur'):
        service.return_empty(issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Encore', 'r2', received=True)
    bottle_issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=bottle.id).one()
    service.return_empty(bottle_issue.id, session.id, 10, 500, [], 'Bouteilles récupérées', 'r-b', received=True)
    assert stock.balance(bottle.id) == 10 and credit.remaining_amount == 2500
    assert db_session.query(ManagedDepositReturn).count() == 2
    with pytest.raises(ValueError, match='retour de vides actif'):
        SaleCancellationService(db_session).cancel(sale.id, session.id, 'Tout', 'ann', goods_recovered=True, empties_recovered=True)


def test_retour_vides_invalide_refuse_sans_ecriture(db_session, scenario):
    product, pack, crate, _, client, cash, session = scenario
    sale = create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    service = ManagedDepositService(db_session)
    with pytest.raises(ValueError, match='stock initial'):
        service.return_empty(issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Test', 'r', received=True)
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    with pytest.raises(ValueError, match='correspondre'):
        service.return_empty(issue.id, session.id, 1, 200, [], 'Test', 'r', received=True)
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3200
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 0
    assert db_session.query(ManagedDepositReturn).count() == 0
    assert product.stock_quantity == 24


def test_retour_vides_rollback_caisse(db_session, scenario):
    product, pack, crate, _, client, cash, session = scenario
    create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    def fail(_mapper, _connection, target):
        if target.kind == 'outflow':
            raise RuntimeError('échec caisse')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échec caisse'):
            ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Test', 'r', received=True)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3200
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 0
    assert db_session.query(ManagedDepositReturn).count() == db_session.query(ManagedDepositRefund).count() == 0
    assert db_session.query(ReturnableStockMovement).filter_by(movement_type='entry').count() == 0


def test_vente_comptant_et_remboursement_especes(db_session, scenario):
    product, pack, crate, bottle, client, cash, session = scenario
    quote = DepositConfigurationService(db_session).quote(pack.id, 1)
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1,
        'expected_deposits': quote}], 'comptant', client_id=client.id)
    assert sale.total == 4700 and cash.cash_available(session) == 5700
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    payment = db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).one()
    ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 0,
        [{'transaction_id': payment.id, 'amount': 500}], 'Retour casier', 'retour', received=True)
    assert cash.cash_available(session) == 5200 and db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    assert product.stock_quantity == 24


def test_retour_valeur_historique_figee_et_interdit_trop_rembourser(db_session, scenario):
    product, pack, crate, _, client, cash, session = scenario
    create_credit(db_session, scenario)
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    crate.deposit_value = 900
    db_session.commit()
    with pytest.raises(ValueError, match='correspondre'):
        ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 0,
            [{'transaction_id': wave.id, 'amount': 900}], 'Test', 'trop', received=True)
    returned = ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 0,
        [{'transaction_id': wave.id, 'amount': 500}], 'Retour', 'ok', received=True)
    assert returned.amount == 500
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1


def test_echec_creation_consigne_annule_vente_caisse_et_stock(db_session, scenario):
    product, pack, crate, bottle, client, cash, session = scenario
    quote = DepositConfigurationService(db_session).quote(pack.id, 1)
    def fail(_mapper, _connection, _target):
        raise RuntimeError('échec écriture consigne')
    event.listen(ManagedDepositIssue, 'before_insert', fail)
    try:
        with pytest.raises((ValueError, RuntimeError)):
            ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1,
                'expected_deposits': quote}], 'vente', client_id=client.id)
    finally:
        event.remove(ManagedDepositIssue, 'before_insert', fail)
    assert product.stock_quantity == 48 and cash.cash_available(session) == 1000
    assert db_session.query(ManagedSale).count() == db_session.query(ManagedDepositIssue).count() == 0
    assert db_session.query(ManagedCashTransaction).count() == 0


def test_retours_concurrents_ne_rendent_pas_deux_fois_le_meme_vide(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    engine = create_engine(f'sqlite:///{tmp_path / "depot.db"}', connect_args={'timeout': 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    from models.payment_method import PaymentMethod
    from services.cash_methods import METHODS
    with factory() as seed:
        seed.add_all(PaymentMethod(code=k, label=v, active=True) for k, v in METHODS.items())
        seed.commit()
    with factory() as db:
        product_service = ProductService(db)
        category = product_service.create_category('Test')
        product = product_service.create_product({'name': 'Test', 'category_id': category.id, 'unit': 'bouteille', 'stock_quantity': 1})
        pack = PackagingService(db).save(product.id, {'name': 'bouteille', 'coefficient': 1, 'retail_price': 1000})
        empty = ReturnablePackagingService(db).create(code='B', name='Bouteille', producer='Test', kind='bottle', deposit_value=500)
        DepositConfigurationService(db).configure(pack.id, 'deposit', [{'returnable_id': empty.id, 'pieces_per_pack': 1}])
        ReturnableStockService(db).record(empty.id, 'initial', 0, 'Comptage', 'init')
        client = ManagedCreditService(db).create_client('Client', client_type='professionnel', no_limit=True)
        session = ManagedCashService(db).open(0, 'open')
        quote = DepositConfigurationService(db).quote(pack.id, 1)
        sale = ManagedSaleService(db).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1, 'expected_deposits': quote}], 'sale', client_id=client.id)
        issue_id = db.query(ManagedDepositIssue).one().id
        txn_id = db.query(ManagedCashTransaction).filter_by(sale_id=sale.id).one().id
        session_id, empty_id = session.id, empty.id
    barrier = Barrier(2)
    def returning(key):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                ManagedDepositService(db).return_empty(issue_id, session_id, 1, 0, [{'transaction_id': txn_id, 'amount': 500}], 'Retour', key, received=True)
                return True
            except ValueError as exc:
                assert 'supérieur' in str(exc)
                return False
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(returning, ('r1', 'r2'))) == [False, True]
        with factory() as db:
            assert db.get(ReturnableStockBalance, empty_id).quantity == 1
            assert db.query(ManagedDepositReturn).count() == db.query(ManagedDepositRefund).count() == 1
            assert ManagedCashService(db).cash_available(db.get(type(session), session_id)) == 1000
    finally:
        engine.dispose()


def test_retour_vides_apres_reglement_credit(db_session, scenario):
    _, _, crate, _, _, _, session = scenario
    create_credit(db_session, scenario)
    credit = db_session.query(ManagedCreditSale).one()
    payment = ManagedCreditService(db_session).pay(credit.id, session.id, 'wave', 3200, 'reglement')
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    result = ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 0,
        [{'transaction_id': payment.transaction_id, 'amount': 500}], 'Casier récupéré', 'retour', received=True)
    assert result.amount == 500 and credit.remaining_amount == 0
    assert db_session.query(ManagedDepositRefund).filter_by(original_transaction_id=payment.transaction_id).count() == 1


def test_retours_marchandise_et_vides_separes_sans_double_remboursement(db_session, scenario):
    product, pack, crate, _, client, cash, session = scenario
    quote = DepositConfigurationService(db_session).quote(pack.id, 1)
    sale = ManagedSaleService(db_session).sell(session.id, 'retail', 'cash', [{'packaging_id': pack.id, 'quantity': 1,
        'expected_deposits': quote}], 'vente', client_id=client.id)
    payment = db_session.query(ManagedCashTransaction).filter_by(sale_id=sale.id).one()
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': issue.sale_line_id, 'base_quantity': 24}], 0,
        [{'transaction_id': payment.id, 'amount': 3000}], 'Marchandise', 'goods', goods_recovered=True)
    assert product.stock_quantity == 48
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 0
    ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 0,
        [{'transaction_id': payment.id, 'amount': 500}], 'Casier', 'empty', received=True)
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    assert cash.cash_available(session) == 2200


def test_vides_puis_marchandise_et_annulation_retour_marchandise(db_session, scenario):
    from services.return_cancellation_service import ReturnCancellationService
    product, _, crate, _, _, _, session = scenario
    sale = create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 200,
        [{'transaction_id': wave.id, 'amount': 300}], 'Casier', 'empty', received=True)
    returned = SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': issue.sale_line_id, 'base_quantity': 8}], 300,
        [{'transaction_id': wave.id, 'amount': 700}], 'Marchandise', 'goods', goods_recovered=True)
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 2700
    ReturnCancellationService(db_session).cancel(returned.id, session.id, 'Erreur', 'undo', goods_and_refunds_recovered=True)
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3000
    assert product.stock_quantity == 24
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    # Les montants du retour annulé ne sont plus comptés comme remboursés.
    SaleReturnService(db_session).record(sale.id, session.id, [{'sale_line_id': issue.sale_line_id, 'base_quantity': 8}], 300,
        [{'transaction_id': wave.id, 'amount': 700}], 'Marchandise', 'goods2', goods_recovered=True)


def test_annulation_retour_vides_contreparties_et_nouveau_retour(db_session, scenario):
    from services.deposit_return_cancellation_service import DepositReturnCancellationService
    from models.managed_deposit import ManagedDepositReturnRecapture
    _, _, crate, _, _, cash, session = scenario
    create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    service = ManagedDepositService(db_session)
    args = (issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Casier', 'retour')
    returned = service.return_empty(*args, received=True)
    undo = DepositReturnCancellationService(db_session)
    cancellation = undo.cancel(returned.id, session.id, 'Erreur', 'undo', empties_and_refunds_recovered=True)
    assert undo.cancel(returned.id, session.id, 'Erreur', 'undo', empties_and_refunds_recovered=True).id == cancellation.id
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3200
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 0
    assert cash.flows(session.id)['wave'] == {'in': 1300, 'out': 300}
    assert db_session.query(ManagedDepositReturnRecapture).count() == 1
    with pytest.raises(ValueError, match='déjà annulé'):
        undo.cancel(returned.id, session.id, 'Erreur', 'different', empties_and_refunds_recovered=True)
    service.return_empty(issue.id, session.id, 1, 200, [{'transaction_id': wave.id, 'amount': 300}], 'Casier', 'retour2', received=True)
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3000


def test_annulation_vides_bloquee_si_mouvement_suivant_et_rollback(db_session, scenario):
    from services.deposit_return_cancellation_service import DepositReturnCancellationService
    from models.managed_deposit import ManagedDepositReturnCancellation
    _, _, crate, _, _, _, session = scenario
    create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    returned = ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 500, [], 'Casier', 'retour', received=True)
    ReturnableStockService(db_session).record(crate.id, 'entry', 1, 'Mouvement suivant', 'autre')
    with pytest.raises(ValueError, match='ultérieur'):
        DepositReturnCancellationService(db_session).cancel(returned.id, session.id, 'Erreur', 'undo', empties_and_refunds_recovered=True)
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 2
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 2700
    assert db_session.query(ManagedDepositReturnCancellation).count() == 0


def test_annulation_vides_echec_reprise_annule_toutes_ecritures(db_session, scenario):
    from services.deposit_return_cancellation_service import DepositReturnCancellationService
    from models.managed_deposit import ManagedDepositReturnCancellation
    _, _, crate, _, _, _, session = scenario
    create_credit(db_session, scenario)
    issue = db_session.query(ManagedDepositIssue).filter_by(returnable_id=crate.id).one()
    wave = db_session.query(ManagedCashTransaction).filter_by(method='wave').one()
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init')
    returned = ManagedDepositService(db_session).return_empty(issue.id, session.id, 1, 200,
        [{'transaction_id': wave.id, 'amount': 300}], 'Casier', 'retour', received=True)
    def fail(_mapper, _connection, target):
        if target.kind == 'income' and target.reference and target.reference.startswith('ANNULATION-RETOUR-VIDES'):
            raise RuntimeError('échec reprise')
    event.listen(ManagedCashTransaction, 'before_insert', fail)
    try:
        with pytest.raises(RuntimeError, match='échec reprise'):
            DepositReturnCancellationService(db_session).cancel(returned.id, session.id, 'Erreur', 'undo', empties_and_refunds_recovered=True)
    finally:
        event.remove(ManagedCashTransaction, 'before_insert', fail)
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3000
    assert db_session.query(ManagedDepositReturnCancellation).count() == 0


def test_annulation_vente_consignee_sans_retour_precedent(db_session, scenario):
    product, _, crate, bottle, _, cash, session = scenario
    sale = create_credit(db_session, scenario)
    ReturnableStockService(db_session).record(crate.id, 'initial', 0, 'Comptage', 'init-c')
    ReturnableStockService(db_session).record(bottle.id, 'initial', 0, 'Comptage', 'init-b')
    service = SaleCancellationService(db_session)
    with pytest.raises(ValueError, match='emballages consignés'):
        service.cancel(sale.id, session.id, 'Erreur', 'annulation', goods_recovered=True)
    result = service.cancel(sale.id, session.id, 'Erreur', 'annulation', goods_recovered=True, empties_recovered=True)
    assert service.cancel(sale.id, session.id, 'Erreur', 'annulation', goods_recovered=True, empties_recovered=True).id == result.id
    assert product.stock_quantity == 48
    assert db_session.get(ReturnableStockBalance, crate.id).quantity == 1
    assert db_session.get(ReturnableStockBalance, bottle.id).quantity == 24
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 0
    assert cash.flows(session.id)['wave'] == {'in': 1000, 'out': 1000}
    assert cash.cash_available(session) == 1000


def test_annulation_vente_consignee_refuse_stock_initial_manquant(db_session, scenario):
    product, _, crate, _, _, _, session = scenario
    sale = create_credit(db_session, scenario)
    with pytest.raises(ValueError, match='Stock initial'):
        SaleCancellationService(db_session).cancel(sale.id, session.id, 'Erreur', 'annulation', goods_recovered=True, empties_recovered=True)
    assert product.stock_quantity == 24
    assert db_session.query(ManagedCreditSale).one().remaining_amount == 3200
    assert db_session.get(ReturnableStockBalance, crate.id) is None


def test_annulation_retour_vides_concurrente(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base
    from models.payment_method import PaymentMethod
    from models.managed_deposit import ManagedDepositReturnCancellation
    from services.cash_methods import METHODS
    from services.deposit_return_cancellation_service import DepositReturnCancellationService
    engine = create_engine(f'sqlite:///{tmp_path / "undo.db"}', connect_args={'timeout': 20})
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)
    with factory() as db:
        db.add_all(PaymentMethod(code=k, label=v, active=True) for k, v in METHODS.items())
        db.commit()
        p = ProductService(db)
        cat = p.create_category('Test')
        product = p.create_product({'name': 'Boisson', 'category_id': cat.id, 'unit': 'bouteille', 'stock_quantity': 1})
        pack = PackagingService(db).save(product.id, {'name': 'bouteille', 'coefficient': 1, 'retail_price': 1000})
        empty = ReturnablePackagingService(db).create(code='B', name='Bouteille', producer='Test', kind='bottle', deposit_value=500)
        DepositConfigurationService(db).configure(pack.id, 'deposit', [{'returnable_id': empty.id, 'pieces_per_pack': 1}])
        ReturnableStockService(db).record(empty.id, 'initial', 0, 'Comptage', 'initial')
        client = ManagedCreditService(db).create_client('Client', client_type='particulier', no_limit=True)
        session = ManagedCashService(db).open(0, 'open')
        quote = DepositConfigurationService(db).quote(pack.id, 1)
        ManagedSaleService(db).sell(session.id, 'retail', 'credit', [{'packaging_id': pack.id, 'quantity': 1, 'expected_deposits': quote}], 'sale', payments=[], client_id=client.id)
        issue = db.query(ManagedDepositIssue).one()
        returned = ManagedDepositService(db).return_empty(issue.id, session.id, 1, 500, [], 'Retour', 'retour', received=True)
        returned_id, session_id = returned.id, session.id
    barrier = Barrier(2)
    def undo(key):
        with factory() as db:
            barrier.wait(timeout=10)
            try:
                DepositReturnCancellationService(db).cancel(returned_id, session_id, 'Erreur', key, empties_and_refunds_recovered=True)
                return True
            except ValueError as exc:
                assert 'déjà annulé' in str(exc)
                return False
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(undo, ('u1', 'u2'))) == [False, True]
        with factory() as db:
            assert db.query(ManagedDepositReturnCancellation).count() == 1
            assert db.query(ManagedCreditSale).one().remaining_amount == 1500
    finally:
        engine.dispose()
