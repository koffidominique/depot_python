"""Contrepassation d'un retour, sous conditions strictes et avec piste d'audit."""
from collections import defaultdict
from fractions import Fraction
from models.managed_cash import ManagedCashSession
from models.managed_credit import ManagedCreditSale
from models.managed_operations import ManagedSaleLine, ManagedSaleCancellation, ManagedCashTransaction
from models.managed_returns import (ManagedReturn, ManagedReturnLine, ManagedReturnRefund,
                                    ManagedReturnCancellation, ManagedReturnRecapture)
from models.product import Product
from models.stock import StockMovement
from money import fcfa
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService, _key
from services.sqlite_transaction import locked_write
from services.stock_service import StockService


class ReturnCancellationService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def cancel(self, return_id, session_id, reason, request_key, *, goods_and_refunds_recovered=False):
        METHODS = labels(self.db)
        key = _key(request_key)
        if goods_and_refunds_recovered is not True:
            raise ValueError('Confirmez le départ des marchandises et la récupération des remboursements.')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        previous = self.db.query(ManagedReturnCancellation).filter_by(request_key=key).first()
        if previous:
            if (previous.return_id, previous.session_id, previous.reason) != (return_id, session_id, reason):
                raise ValueError('Cette clé d’annulation a déjà été utilisée.')
            ident = previous.id
            self.db.rollback()
            return self.db.get(ManagedReturnCancellation, ident)
        returned = self.db.get(ManagedReturn, return_id)
        session = self.db.get(ManagedCashSession, session_id)
        if not returned or not session or session.status != 'open':
            raise ValueError('Retour existant et caisse ouverte obligatoires.')
        if self.db.query(ManagedReturnCancellation.id).filter_by(return_id=return_id).first():
            raise ValueError('Ce retour est déjà annulé.')
        if self.db.query(ManagedSaleCancellation.id).filter_by(sale_id=returned.sale_id).first():
            raise ValueError('La vente est déjà annulée.')
        credit = self.db.query(ManagedCreditSale).filter_by(sale_id=returned.sale_id).one_or_none()
        if returned.credit_reduction and (not credit or credit.remaining_amount + returned.credit_reduction > credit.initial_amount):
            raise ValueError('Créance incohérente : diagnostic requis.')
        lines = self.db.query(ManagedReturnLine).filter_by(return_id=return_id).all()
        refunds = self.db.query(ManagedReturnRefund).filter_by(return_id=return_id).all()
        if not lines or fcfa(sum(line.amount for line in lines), 'Lignes du retour') != returned.total:
            raise ValueError('Lignes de retour incohérentes.')
        movements = []
        for refund in refunds:
            entry = self.db.get(ManagedCashTransaction, refund.refund_transaction_id)
            original = self.db.get(ManagedCashTransaction, refund.original_transaction_id)
            if not entry or not original or entry.kind != 'outflow' or entry.method != original.method or entry.method not in METHODS or entry.amount <= 0:
                raise ValueError('Remboursement incohérent : diagnostic requis.')
            movements.append((refund, entry))
        if fcfa(sum(entry.amount for _, entry in movements) + returned.credit_reduction, 'Contreparties') != returned.total:
            raise ValueError('Contreparties du retour incohérentes.')
        cash_in = fcfa(sum(entry.amount for _, entry in movements if entry.method == 'cash'), 'Espèces récupérées')
        if cash_in:
            fcfa(ManagedCashService(self.db).cash_available(session) + cash_in, 'Espèces théoriques')
        groups = defaultdict(list)
        for line in lines:
            original_line = self.db.get(ManagedSaleLine, line.sale_line_id)
            if not original_line or original_line.sale_id != returned.sale_id or line.base_quantity <= 0:
                raise ValueError('Ligne de retour incohérente.')
            groups[original_line.product_id].append((line, original_line))
        for product_id, entries in groups.items():
            product = self.db.get(Product, product_id)
            if not product or product.stock_quantity is None or product.stock_quantity < 0 or any(original.base_unit != product.unit for _, original in entries):
                raise ValueError('Stock ou unité incohérent.')
            original_moves = self.db.query(StockMovement).filter_by(product_id=product_id, movement_type='sale_return', reference_document=f'RETOUR-{return_id}').all()
            total_qty = sum(line.base_quantity for line, _ in entries)
            if len(original_moves) != len(entries) or sum(m.quantity for m in original_moves) != total_qty:
                raise ValueError('Mouvements de stock du retour incohérents.')
            last_id = max(m.id for m in original_moves)
            if self.db.query(StockMovement.id).filter(StockMovement.product_id == product_id, StockMovement.id > last_id).first():
                raise ValueError('Un mouvement de stock ultérieur existe : diagnostic requis avant annulation.')
            if product.stock_quantity < total_qty:
                raise ValueError('Stock insuffisant pour annuler le retour.')
        cancellation = ManagedReturnCancellation(return_id=return_id, session_id=session_id, request_key=key, reason=reason)
        self.db.add(cancellation)
        if credit:
            credit.remaining_amount += returned.credit_reduction
        self.db.flush()
        reference = f'ANNULATION-RETOUR-{cancellation.id}'
        for product_id, entries in groups.items():
            product = self.db.get(Product, product_id)
            total_qty = sum(line.base_quantity for line, _ in entries)
            stock_after = product.stock_quantity - total_qty
            cost = product.average_cost
            returned_cost = Fraction(0)
            unknown = cost is None
            for line, original in entries:
                if original.cost_numerator is None and original.cost_denominator is None:
                    unknown = True
                elif original.cost_numerator is None or original.cost_denominator is None:
                    raise ValueError('Coût historique incomplet.')
                else:
                    numerator, denominator = int(original.cost_numerator), int(original.cost_denominator)
                    if numerator < 0 or denominator <= 0:
                        raise ValueError('Coût historique invalide.')
                    returned_cost += Fraction(line.base_quantity) * Fraction(numerator, denominator)
            if not stock_after or unknown:
                product.average_cost_numerator = product.average_cost_denominator = None
            else:
                original_value = Fraction(product.stock_quantity) * cost - returned_cost
                if original_value < 0:
                    raise ValueError('Coût résultant incohérent : diagnostic requis.')
                result = original_value / Fraction(stock_after)
                product.average_cost_numerator, product.average_cost_denominator = str(result.numerator), str(result.denominator)
            if not StockService(self.db).update_stock(product.id, -total_qty, 'return_cancellation', unit=product.unit,
                    reason=reason, reference_document=reference, commit=False):
                raise ValueError('Mise à jour de stock impossible.')
        for refund, entry in movements:
            recapture = ManagedCashTransaction(session_id=session_id, request_key=f'reprise-retour:{cancellation.id}:{refund.id}',
                kind='income', method=entry.method, amount=entry.amount,
                description=f'Annulation retour #{return_id} — {reason}', reference=reference)
            self.db.add(recapture)
            self.db.flush()
            self.db.add(ManagedReturnRecapture(cancellation_id=cancellation.id, refund_id=refund.id, transaction_id=recapture.id))
        self.db.commit()
        self.db.refresh(cancellation)
        return cancellation
