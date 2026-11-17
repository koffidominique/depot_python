"""Retour de vides consignés : écritures de stock et contreparties atomiques."""
import json
from sqlalchemy import func
from models.managed_cash import ManagedCashSession
from models.managed_credit import ManagedCreditSale
from models.managed_deposit import ManagedDepositIssue, ManagedDepositReturn, ManagedDepositRefund, ManagedDepositReturnCancellation
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedSalePayment, ManagedSaleCancellation, ManagedCashTransaction
from models.managed_returns import ManagedReturn, ManagedReturnRefund, ManagedReturnCancellation
from models.returnable_stock import ReturnableStockBalance, ReturnableStockMovement
from money import fcfa
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService, _key
from services.returnable_stock_service import _pieces, MAX_QUANTITY
from services.sqlite_transaction import locked_write


class ManagedDepositService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def return_empty(self, issue_id, session_id, pieces, credit_reduction, refunds, reason, request_key, *, received=False):
        METHODS = labels(self.db)
        key = _key(request_key)
        if received is not True:
            raise ValueError('Confirmez la réception physique des vides.')
        count = _pieces(pieces)
        reduction = fcfa(credit_reduction, 'Réduction de créance')
        if reduction < 0:
            raise ValueError('Réduction de créance invalide.')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        if not isinstance(refunds, (list, tuple)):
            raise ValueError('Remboursements invalides.')
        normalized, seen = [], set()
        for refund in refunds:
            if not isinstance(refund, dict) or not isinstance(refund.get('transaction_id'), int) or isinstance(refund.get('transaction_id'), bool):
                raise ValueError('Encaissement invalide.')
            ident = refund['transaction_id']
            if ident in seen:
                raise ValueError('Chaque encaissement ne doit apparaître qu’une fois.')
            seen.add(ident)
            amount = fcfa(refund.get('amount'), 'Remboursement')
            if amount <= 0:
                raise ValueError('Le remboursement doit être positif.')
            normalized.append((ident, amount))
        normalized.sort()
        fingerprint = json.dumps([issue_id, session_id, count, reduction, normalized, reason], ensure_ascii=False, separators=(',', ':'))
        previous = self.db.query(ManagedDepositReturn).filter_by(request_key=key).first()
        if previous:
            if previous.fingerprint != fingerprint:
                raise ValueError('Cette clé de retour de consigne a déjà été utilisée.')
            ident = previous.id
            self.db.rollback()
            return self.db.get(ManagedDepositReturn, ident)
        issue = self.db.get(ManagedDepositIssue, issue_id)
        session = self.db.get(ManagedCashSession, session_id)
        if not issue or not session or session.status != 'open':
            raise ValueError('Emballage consigné et caisse ouverte obligatoires.')
        line = self.db.get(ManagedSaleLine, issue.sale_line_id)
        sale = self.db.get(ManagedSale, line.sale_id) if line else None
        if not sale or self.db.query(ManagedSaleCancellation.id).filter_by(sale_id=sale.id).first():
            raise ValueError('Vente introuvable ou annulée.')
        lines = self.db.query(ManagedSaleLine).filter_by(sale_id=sale.id).all()
        issues = self.db.query(ManagedDepositIssue).join(ManagedSaleLine, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).filter(ManagedSaleLine.sale_id == sale.id).all()
        if (not lines or not issues or any(i.client_id != issue.client_id or i.pieces <= 0 or i.unit_value < 0 or
                i.amount != fcfa(i.pieces * i.unit_value, 'Consigne initiale') for i in issues) or
                fcfa(sum(l.amount for l in lines) + sum(i.amount for i in issues), 'Total vente') != sale.total):
            raise ValueError('Historique de vente ou de consigne incohérent.')
        active_deposit_returns = self.db.query(ManagedDepositReturn.id).outerjoin(ManagedDepositReturnCancellation, ManagedDepositReturnCancellation.return_id == ManagedDepositReturn.id).filter(ManagedDepositReturnCancellation.id.is_(None))
        previous_pieces = self.db.query(func.coalesce(func.sum(ManagedDepositReturn.pieces), 0)).filter(ManagedDepositReturn.issue_id == issue.id, ManagedDepositReturn.id.in_(active_deposit_returns)).scalar()
        if count + previous_pieces > issue.pieces:
            raise ValueError('Nombre de vides supérieur au solde restant pour cette vente.')
        if issue.unit_value < 0 or issue.amount != fcfa(issue.pieces * issue.unit_value, 'Consigne initiale'):
            raise ValueError('Consigne historique incohérente.')
        amount = fcfa(count * issue.unit_value, 'Valeur des vides')
        credit = self.db.query(ManagedCreditSale).filter_by(sale_id=sale.id).one_or_none()
        if reduction and (not credit or reduction > credit.remaining_amount):
            raise ValueError('Réduction de créance supérieure au solde ou indisponible.')
        links = self.db.query(ManagedSalePayment).filter_by(sale_id=sale.id).all()
        if sale.payment_method in METHODS and not links and credit is None:
            originals = self.db.query(ManagedCashTransaction).filter_by(sale_id=sale.id, kind='sale').all()
            if len(originals) != 1 or originals[0].method != sale.payment_method:
                raise ValueError('Encaissement de vente incohérent.')
        elif sale.payment_method == 'credit' and credit is not None:
            originals = [self.db.get(ManagedCashTransaction, link.transaction_id) for link in links]
        elif sale.payment_method == 'mixed' and credit is None and len(links) >= 2:
            originals = [self.db.get(ManagedCashTransaction, link.transaction_id) for link in links]
        else:
            raise ValueError('Type de vente ou encaissements incohérents.')
        if any(not entry or entry.method not in METHODS or entry.amount <= 0 or (entry.kind, entry.sale_id) not in (('sale', sale.id), ('income', None)) for entry in originals):
            raise ValueError('Encaissements incohérents.')
        original_map = {entry.id: entry for entry in originals}
        if len(original_map) != len(originals):
            raise ValueError('Encaissements dupliqués : diagnostic requis.')
        if any(entry.id not in original_map for entry in self.db.query(ManagedCashTransaction).filter_by(sale_id=sale.id)):
            raise ValueError('Encaissements incohérents.')
        returns = self.db.query(ManagedDepositReturn).join(ManagedDepositIssue, ManagedDepositReturn.issue_id == ManagedDepositIssue.id).join(
            ManagedSaleLine, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).filter(ManagedSaleLine.sale_id == sale.id, ManagedDepositReturn.id.in_(active_deposit_returns)).all()
        prior_return_total = fcfa(sum(item.amount for item in returns), 'Retours de consigne')
        returned_ids = [item.id for item in returns]
        refunded_before = {}
        for ident, paid in self.db.query(ManagedDepositRefund.original_transaction_id, func.sum(ManagedCashTransaction.amount)).join(
                ManagedCashTransaction, ManagedDepositRefund.refund_transaction_id == ManagedCashTransaction.id).filter(
                ManagedDepositRefund.deposit_return_id.in_(returned_ids)).group_by(ManagedDepositRefund.original_transaction_id):
            refunded_before[ident] = fcfa(paid, 'Remboursements précédents')
        active_returns = self.db.query(ManagedReturn.id).outerjoin(ManagedReturnCancellation, ManagedReturnCancellation.return_id == ManagedReturn.id).filter(
            ManagedReturn.sale_id == sale.id, ManagedReturnCancellation.id.is_(None))
        goods_returns = self.db.query(ManagedReturn).filter(ManagedReturn.id.in_(active_returns)).all()
        prior_return_total = fcfa(prior_return_total + sum(item.total for item in goods_returns), 'Retours précédents')
        for ident, paid in self.db.query(ManagedReturnRefund.original_transaction_id, func.sum(ManagedCashTransaction.amount)).join(
                ManagedCashTransaction, ManagedReturnRefund.refund_transaction_id == ManagedCashTransaction.id).filter(
                ManagedReturnRefund.return_id.in_(active_returns)).group_by(ManagedReturnRefund.original_transaction_id):
            refunded_before[ident] = fcfa(refunded_before.get(ident, 0) + paid, 'Remboursements précédents')
        paid_total = fcfa(sum(entry.amount for entry in originals), 'Total encaissé')
        net_paid = fcfa(paid_total - sum(refunded_before.values()), 'Encaissement net')
        due = credit.remaining_amount if credit else 0
        if prior_return_total > sale.total or net_paid < 0 or net_paid + due != sale.total - prior_return_total:
            raise ValueError('Solde de vente incohérent : diagnostic requis.')
        refund_total = fcfa(sum(value for _, value in normalized), 'Total remboursé')
        if fcfa(reduction + refund_total, 'Contreparties') != amount:
            raise ValueError('La réduction de créance et les remboursements doivent correspondre à la valeur des vides.')
        for ident, value in normalized:
            if ident not in original_map or value + refunded_before.get(ident, 0) > original_map[ident].amount:
                raise ValueError('Remboursement supérieur à l’encaissement restant ou sans lien avec la vente.')
        cash_amount = sum(value for ident, value in normalized if original_map[ident].method == 'cash')
        if cash_amount > ManagedCashService(self.db).cash_available(session):
            raise ValueError('Espèces insuffisantes pour le remboursement.')
        balance = self.db.get(ReturnableStockBalance, issue.returnable_id)
        if balance is None:
            raise ValueError('Déclarez d’abord le stock initial de cet emballage vide.')
        if balance.quantity < 0 or balance.quantity + count > MAX_QUANTITY:
            raise ValueError('Stock de vides incohérent ou supérieur à la limite SQLite.')
        before = balance.quantity
        balance.quantity += count
        movement = ReturnableStockMovement(request_key=f'retour-consigne:{key}', packaging_id=issue.returnable_id,
            movement_type='entry', quantity=count, stock_before=before, stock_after=balance.quantity,
            reason=reason, reference_document=sale.reference)
        self.db.add(movement)
        if credit:
            credit.remaining_amount -= reduction
        self.db.flush()
        record = ManagedDepositReturn(issue_id=issue.id, session_id=session.id, stock_movement_id=movement.id,
            request_key=key, fingerprint=fingerprint, pieces=count, amount=amount, credit_reduction=reduction, reason=reason)
        self.db.add(record)
        self.db.flush()
        for ident, value in normalized:
            original = original_map[ident]
            refund = ManagedCashTransaction(session_id=session.id, request_key=f'consigne-remboursement:{record.id}:{ident}',
                kind='outflow', method=original.method, amount=value,
                description=f'Retour consigne {sale.reference} — {reason}', reference=f'RETOUR-VIDES-{record.id}')
            self.db.add(refund)
            self.db.flush()
            self.db.add(ManagedDepositRefund(deposit_return_id=record.id, original_transaction_id=ident, refund_transaction_id=refund.id))
        self.db.commit()
        self.db.refresh(record)
        return record
