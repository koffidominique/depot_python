"""Contrepassation traçable d'un retour de vides, sans suppression de l'original."""
from models.managed_cash import ManagedCashSession
from models.managed_credit import ManagedCreditSale
from models.managed_deposit import (ManagedDepositIssue, ManagedDepositReturn, ManagedDepositRefund,
    ManagedDepositReturnCancellation, ManagedDepositReturnRecapture)
from models.managed_operations import ManagedSaleLine, ManagedSaleCancellation, ManagedCashTransaction, ManagedSalePayment
from models.returnable_stock import ReturnableStockBalance, ReturnableStockMovement
from money import fcfa
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService, _key
from services.sqlite_transaction import locked_write


class DepositReturnCancellationService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def cancel(self, return_id, session_id, reason, request_key, *, empties_and_refunds_recovered=False):
        key = _key(request_key)
        if empties_and_refunds_recovered is not True:
            raise ValueError('Confirmez la restitution des vides au client et la récupération des remboursements.')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        previous = self.db.query(ManagedDepositReturnCancellation).filter_by(request_key=key).first()
        if previous:
            if (previous.return_id, previous.session_id, previous.reason) != (return_id, session_id, reason):
                raise ValueError('Cette clé d’annulation a déjà été utilisée.')
            ident = previous.id
            self.db.rollback()
            return self.db.get(ManagedDepositReturnCancellation, ident)
        returned = self.db.get(ManagedDepositReturn, return_id)
        session = self.db.get(ManagedCashSession, session_id)
        if not returned or not session or session.status != 'open':
            raise ValueError('Retour existant et caisse ouverte obligatoires.')
        if self.db.query(ManagedDepositReturnCancellation.id).filter_by(return_id=return_id).first():
            raise ValueError('Ce retour de vides est déjà annulé.')
        issue = self.db.get(ManagedDepositIssue, returned.issue_id)
        line = self.db.get(ManagedSaleLine, issue.sale_line_id) if issue else None
        if not line or self.db.query(ManagedSaleCancellation.id).filter_by(sale_id=line.sale_id).first():
            raise ValueError('Vente introuvable ou annulée.')
        credit = self.db.query(ManagedCreditSale).filter_by(sale_id=line.sale_id).one_or_none()
        if returned.credit_reduction and (not credit or credit.remaining_amount + returned.credit_reduction > credit.initial_amount):
            raise ValueError('Créance incohérente : diagnostic requis.')
        movement = self.db.get(ReturnableStockMovement, returned.stock_movement_id)
        balance = self.db.get(ReturnableStockBalance, issue.returnable_id)
        if (not movement or not balance or movement.packaging_id != issue.returnable_id or movement.movement_type != 'entry'
                or movement.quantity != returned.pieces or returned.pieces <= 0 or returned.amount != fcfa(returned.pieces * issue.unit_value)):
            raise ValueError('Mouvement ou valeur de consigne incohérent.')
        if self.db.query(ReturnableStockMovement.id).filter(ReturnableStockMovement.packaging_id == issue.returnable_id,
                ReturnableStockMovement.id > movement.id).first():
            raise ValueError('Un mouvement de stock de vides ultérieur existe : diagnostic requis.')
        if balance.quantity != movement.stock_after or balance.quantity < returned.pieces:
            raise ValueError('Stock de vides insuffisant ou incohérent.')
        refunds = self.db.query(ManagedDepositRefund).filter_by(deposit_return_id=return_id).all()
        entries = []
        methods = labels(self.db)
        linked = {p.transaction_id for p in self.db.query(ManagedSalePayment).filter_by(sale_id=line.sale_id)}
        direct = {p.id for p in self.db.query(ManagedCashTransaction).filter_by(sale_id=line.sale_id, kind='sale')}
        for refund in refunds:
            paid = self.db.get(ManagedCashTransaction, refund.refund_transaction_id)
            original = self.db.get(ManagedCashTransaction, refund.original_transaction_id)
            if (not paid or not original or original.id not in linked | direct or paid.kind != 'outflow'
                    or paid.method != original.method or paid.method not in methods or paid.amount <= 0):
                raise ValueError('Remboursement incohérent : diagnostic requis.')
            entries.append((refund, paid))
        if fcfa(sum(entry.amount for _, entry in entries) + returned.credit_reduction) != returned.amount:
            raise ValueError('Contreparties du retour incohérentes.')
        cash_in = sum(entry.amount for _, entry in entries if entry.method == 'cash')
        if cash_in:
            fcfa(ManagedCashService(self.db).cash_available(session) + cash_in, 'Espèces théoriques')
        before = balance.quantity
        balance.quantity -= returned.pieces
        undo = ReturnableStockMovement(request_key=f'annulation-retour-vides:{key}', packaging_id=issue.returnable_id,
            movement_type='exit', quantity=returned.pieces, stock_before=before, stock_after=balance.quantity,
            reason=reason, reference_document=f'ANNULATION-RETOUR-VIDES-{returned.id}')
        self.db.add(undo)
        if credit:
            credit.remaining_amount += returned.credit_reduction
        self.db.flush()
        cancellation = ManagedDepositReturnCancellation(return_id=return_id, session_id=session_id,
            stock_movement_id=undo.id, request_key=key, reason=reason)
        self.db.add(cancellation)
        self.db.flush()
        for refund, entry in entries:
            recapture = ManagedCashTransaction(session_id=session_id, request_key=f'reprise-consigne:{cancellation.id}:{refund.id}',
                kind='income', method=entry.method, amount=entry.amount,
                description=f'Annulation retour de vides #{return_id} — {reason}', reference=f'ANNULATION-RETOUR-VIDES-{cancellation.id}')
            self.db.add(recapture)
            self.db.flush()
            self.db.add(ManagedDepositReturnRecapture(cancellation_id=cancellation.id, refund_id=refund.id, transaction_id=recapture.id))
        self.db.commit()
        self.db.refresh(cancellation)
        return cancellation
