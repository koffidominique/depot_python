"""Créances isolées des historiques non rapprochés, règlements en caisse."""
from uuid import uuid4
from sqlalchemy import func
from models.client import Client
from models.debt import ClientDebt
from models.sale import Sale
from models.managed_credit import ManagedCreditProfile, ManagedCreditSale, ManagedCreditPayment
from models.managed_cash import ManagedCashSession
from models.managed_operations import ManagedCashTransaction, ManagedSalePayment, ManagedSaleCancellation
from money import fcfa
from services.cash_methods import require_active
from services.managed_cash_service import ManagedCashService, _key
from services.sqlite_transaction import locked_write


def eligible_client(db, client_id):
    client = db.get(Client, client_id)
    if not client or not client.is_active:
        raise ValueError('Client actif introuvable.')
    if (client.financial_balance is None or fcfa(client.financial_balance) != 0 or
        db.query(ClientDebt.id).filter_by(client_id=client.id).first() or
        db.query(Sale.id).filter_by(client_id=client.id).first()):
        raise ValueError('Historique client non rapproché : crédit indisponible sans diagnostic.')
    profile = db.get(ManagedCreditProfile, client_id)
    if not profile:
        raise ValueError('Configurez explicitement le plafond de crédit de ce client.')
    return client, profile


class ManagedCreditService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def create_client(self, name, *, client_type, credit_limit=None, no_limit=False):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
            raise ValueError('Nom client obligatoire (200 caractères maximum).')
        if client_type not in ('particulier', 'professionnel'):
            raise ValueError('Sélectionnez le type de client.')
        if no_limit is not True:
            limit = fcfa(credit_limit, 'Plafond de crédit')
            if limit < 0:
                raise ValueError('Le plafond ne peut pas être négatif.')
        else:
            if credit_limit not in (None, ''):
                raise ValueError('Choisissez un plafond ou sans plafond, pas les deux.')
            limit = None
        client = Client(code=f'CLI-{uuid4().hex.upper()}', name=name.strip(), type=client_type,
                        credit_limit=0, financial_balance=0, consignment_balance=0, payment_terms=0, is_active=True)
        self.db.add(client)
        self.db.flush()
        self.db.add(ManagedCreditProfile(client_id=client.id, credit_limit=limit))
        self.db.commit()
        self.db.refresh(client)
        return client

    @locked_write
    def pay(self, credit_id, session_id, method, amount, request_key, note=None):
        key = _key(request_key)
        amount = fcfa(amount, 'Montant du règlement')
        if amount <= 0:
            raise ValueError('Le règlement doit être positif.')
        if note is not None and (not isinstance(note, str) or len(note.strip()) > 500):
            raise ValueError('Observation invalide.')
        note = (note or '').strip() or None
        previous = self.db.query(ManagedCreditPayment).filter_by(request_key=key).first()
        if previous:
            movement = self.db.get(ManagedCashTransaction, previous.transaction_id)
            if (previous.credit_sale_id, movement.session_id, movement.method, movement.amount, previous.note) == (credit_id, session_id, method, amount, note):
                ident = previous.id
                self.db.rollback()
                return self.db.get(ManagedCreditPayment, ident)
            raise ValueError('Cette clé de règlement a déjà été utilisée.')
        require_active(self.db, method)
        credit = self.db.get(ManagedCreditSale, credit_id)
        session = self.db.get(ManagedCashSession, session_id)
        if not credit:
            raise ValueError('Créance introuvable.')
        if not session or session.status != 'open':
            raise ValueError('Une caisse ouverte est obligatoire.')
        if self.db.query(ManagedSaleCancellation.id).filter_by(sale_id=credit.sale_id).first():
            raise ValueError('Cette créance est annulée.')
        if amount > credit.remaining_amount:
            raise ValueError('Le règlement dépasse le solde restant.')
        if method == 'cash':
            fcfa(ManagedCashService(self.db).cash_available(session) + amount, 'Espèces théoriques')
        movement = ManagedCashTransaction(session_id=session.id, request_key=f'reglement-credit:{key}', kind='income',
            method=method, amount=amount, description=f'Règlement créance #{credit.id}', reference=f'CREDIT-{credit.id}')
        self.db.add(movement)
        self.db.flush()
        payment = ManagedCreditPayment(credit_sale_id=credit.id, transaction_id=movement.id, request_key=key, note=note)
        self.db.add(payment)
        self.db.add(ManagedSalePayment(sale_id=credit.sale_id, transaction_id=movement.id))
        credit.remaining_amount -= amount
        self.db.commit()
        self.db.refresh(payment)
        return payment
