"""Caisse transactionnelle, indépendante des anciennes sessions non rapprochées."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import func
from models.cash import CashSession
from models.managed_cash import ManagedCashEntry, ManagedCashSession
from models.managed_operations import ManagedCashTransaction
from services.cash_methods import METHODS
from money import fcfa
from validation import validate_price


def _key(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 100:
        raise ValueError('Une clé unique est obligatoire.')
    return value


class ManagedCashService:
    def __init__(self, db):
        self.db = db

    def get_open(self):
        return self.db.query(ManagedCashSession).filter_by(status='open').one_or_none()

    def cash_available(self, session):
        paid = self.db.query(func.coalesce(func.sum(ManagedCashEntry.amount), 0)).filter_by(session_id=session.id, method='cash').scalar()
        incoming = self.db.query(func.coalesce(func.sum(ManagedCashTransaction.amount), 0)).filter(
            ManagedCashTransaction.session_id == session.id, ManagedCashTransaction.method == 'cash',
            ManagedCashTransaction.kind.in_(('sale', 'income', 'correction_in'))).scalar()
        outgoing = self.db.query(func.coalesce(func.sum(ManagedCashTransaction.amount), 0)).filter(
            ManagedCashTransaction.session_id == session.id, ManagedCashTransaction.method == 'cash',
            ManagedCashTransaction.kind.in_(('expense', 'outflow', 'correction_out'))).scalar()
        result = fcfa(session.opening_cash + incoming - paid - outgoing, 'Espèces théoriques')
        if result < 0:
            raise ValueError('Solde espèces incohérent : contrôle manuel nécessaire.')
        return result

    def totals(self, session_id):
        rows = self.db.query(ManagedCashEntry.method, func.sum(ManagedCashEntry.amount)).filter_by(session_id=session_id).group_by(ManagedCashEntry.method).all()
        return {method: fcfa(total, 'Total par moyen') for method, total in rows}

    def flows(self, session_id):
        """Flux de session, pas soldes des comptes non espèces."""
        result = {}
        def add(method, direction, amount):
            totals = result.setdefault(method, {'in': 0, 'out': 0})
            totals[direction] = fcfa(totals[direction] + amount, 'Total de flux')
        for entry in self.db.query(ManagedCashEntry).filter_by(session_id=session_id):
            add(entry.method, 'out', entry.amount)
        for entry in self.db.query(ManagedCashTransaction).filter_by(session_id=session_id):
            add(entry.method, 'in' if entry.kind in ('sale', 'income', 'correction_in') else 'out', entry.amount)
        return result

    def record(self, session_id, kind, method, amount, description, request_key, category=None, beneficiary=None, reference=None):
        """Mouvement manuel ; les ventes et paiements fournisseurs ont leur propre transaction."""
        from services.purchase_service import lock_for_write
        if kind not in ('expense', 'income', 'outflow', 'correction_in', 'correction_out') or method not in METHODS:
            raise ValueError('Type ou moyen de mouvement invalide.')
        amount = validate_price(amount, 'Montant')
        if amount <= 0:
            raise ValueError('Le montant doit être positif.')
        if not isinstance(description, str) or not description.strip() or len(description.strip()) > 500:
            raise ValueError('Description obligatoire (500 caractères maximum).')
        description = description.strip()
        def optional(value, label):
            if value is not None and (not isinstance(value, str) or len(value.strip()) > 200):
                raise ValueError(f'{label} invalide.')
            return (value or '').strip() or None
        category, beneficiary, reference = optional(category, 'Catégorie'), optional(beneficiary, 'Bénéficiaire'), optional(reference, 'Référence')
        if kind == 'expense' and not category:
            raise ValueError('La catégorie de dépense est obligatoire.')
        key = _key(request_key)
        try:
            lock_for_write(self.db)
            previous = self.db.query(ManagedCashTransaction).filter_by(request_key=key).first()
            if previous:
                if (previous.session_id, previous.kind, previous.method, previous.amount, previous.description, previous.category, previous.beneficiary, previous.reference) == (session_id, kind, method, amount, description, category, beneficiary, reference):
                    ident = previous.id
                    self.db.rollback()
                    return self.db.get(ManagedCashTransaction, ident)
                raise ValueError('Cette clé de mouvement a déjà été utilisée.')
            session = self.db.get(ManagedCashSession, session_id)
            if not session or session.status != 'open':
                raise ValueError('Une caisse ouverte est obligatoire.')
            if method == 'cash' and kind in ('expense', 'outflow', 'correction_out') and amount > self.cash_available(session):
                raise ValueError('Espèces insuffisantes dans la caisse.')
            if method == 'cash' and kind in ('income', 'correction_in'):
                fcfa(self.cash_available(session) + amount, 'Espèces théoriques')
            entry = ManagedCashTransaction(session_id=session_id, request_key=key, kind=kind, method=method,
                                           amount=amount, description=description, category=category,
                                           beneficiary=beneficiary, reference=reference)
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception:
            self.db.rollback()
            raise

    def open(self, opening_cash, request_key):
        from services.purchase_service import lock_for_write
        amount = validate_price(opening_cash, 'Fonds initial')
        key = _key(request_key)
        try:
            lock_for_write(self.db)
            previous = self.db.query(ManagedCashSession).filter_by(opening_key=key).first()
            if previous:
                if previous.opening_cash == amount:
                    ident = previous.id
                    self.db.rollback()
                    return self.db.get(ManagedCashSession, ident)
                raise ValueError('Cette clé d’ouverture a déjà été utilisée.')
            if self.get_open():
                raise ValueError('Une caisse est déjà ouverte.')
            if self.db.query(CashSession.id).filter_by(status='open').first():
                raise ValueError('Une ancienne caisse est ouverte : rapprochement manuel nécessaire avant ouverture.')
            session = ManagedCashSession(reference=f'CAISSE-{uuid4().hex.upper()}', opening_key=key,
                                         opening_cash=amount, status='open')
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except Exception:
            self.db.rollback()
            raise

    def close(self, session_id, physical_cash, notes, request_key):
        from services.purchase_service import lock_for_write
        actual = validate_price(physical_cash, 'Espèces comptées')
        key = _key(request_key)
        if notes is not None and not isinstance(notes, str):
            raise ValueError('Commentaire invalide.')
        notes = (notes or '').strip() or None
        if notes and len(notes) > 1000:
            raise ValueError('Commentaire trop long.')
        try:
            lock_for_write(self.db)
            previous = self.db.query(ManagedCashSession).filter_by(closing_key=key).first()
            if previous:
                if previous.id == session_id and previous.physical_cash == actual and previous.closing_notes == notes:
                    self.db.rollback()
                    return True
                raise ValueError('Cette clé de clôture a déjà été utilisée.')
            session = self.db.get(ManagedCashSession, session_id)
            if not session or session.status != 'open':
                raise ValueError('Caisse ouverte introuvable.')
            theoretical = self.cash_available(session)
            difference = fcfa(actual - theoretical, 'Écart de caisse')
            if difference and not notes:
                raise ValueError('Un commentaire est obligatoire en cas d’écart.')
            session.status = 'closed'
            session.closing_key = key
            session.closed_at = datetime.utcnow()
            session.theoretical_cash = theoretical
            session.physical_cash = actual
            session.difference = difference
            session.closing_notes = notes
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise
