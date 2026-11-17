"""Retours de marchandises en unités de base, avec contreparties explicites."""
import json
from fractions import Fraction
from sqlalchemy import func
from models.managed_cash import ManagedCashSession
from models.managed_credit import ManagedCreditSale
from models.managed_operations import ManagedSale, ManagedSaleLine, ManagedSalePayment, ManagedCashTransaction, ManagedSaleCancellation
from models.managed_returns import ManagedReturn, ManagedReturnLine, ManagedReturnRefund, ManagedReturnCancellation
from models.product import Product
from models.managed_deposit import ManagedDepositIssue, ManagedDepositReturn, ManagedDepositRefund, ManagedDepositReturnCancellation
from money import fcfa
from services.cash_methods import labels
from services.managed_cash_service import ManagedCashService, _key
from services.packaging_service import quantity
from services.sqlite_transaction import locked_write
from services.stock_service import StockService


class SaleReturnService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def record(self, sale_id, session_id, lines, credit_reduction, refunds, reason, request_key, *, goods_recovered=False, cancel_sale=False):
        METHODS = labels(self.db)
        key = _key(request_key)
        if cancel_sale is not True and cancel_sale is not False:
            raise ValueError('Confirmation d’annulation invalide.')
        if goods_recovered is not True:
            raise ValueError('Confirmez la récupération physique des marchandises.')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        if not isinstance(lines, (list, tuple)) or not lines or not isinstance(refunds, (list, tuple)):
            raise ValueError('Précisez les lignes et remboursements du retour.')
        amounts = []
        seen = set()
        for line in lines:
            if not isinstance(line, dict) or not isinstance(line.get('sale_line_id'), int) or isinstance(line.get('sale_line_id'), bool):
                raise ValueError('Ligne de vente invalide.')
            ident = line['sale_line_id']
            if ident in seen:
                raise ValueError('Chaque ligne ne doit apparaître qu’une fois.')
            seen.add(ident)
            amounts.append((ident, str(quantity(line.get('base_quantity'), 'Quantité retournée').normalize())))
        amounts.sort()
        reduction = fcfa(credit_reduction, 'Réduction de créance')
        if reduction < 0:
            raise ValueError('La réduction de créance ne peut pas être négative.')
        refunds_normalized, seen = [], set()
        for item in refunds:
            if not isinstance(item, dict) or not isinstance(item.get('transaction_id'), int) or isinstance(item.get('transaction_id'), bool):
                raise ValueError('Encaissement d’origine invalide.')
            ident = item['transaction_id']
            if ident in seen:
                raise ValueError('Chaque encaissement ne doit apparaître qu’une fois.')
            seen.add(ident)
            amount = fcfa(item.get('amount'), 'Remboursement')
            if amount <= 0:
                raise ValueError('Le remboursement doit être positif.')
            refunds_normalized.append((ident, amount))
        refunds_normalized.sort()
        identity = [sale_id, session_id, amounts, reduction, refunds_normalized, reason]
        if cancel_sale:
            identity.append('annulation-totale')
        fingerprint = json.dumps(identity, ensure_ascii=False, separators=(',', ':'))
        previous = self.db.query(ManagedReturn).filter_by(request_key=key).first()
        if previous:
            if previous.fingerprint != fingerprint:
                raise ValueError('Cette clé de retour a déjà été utilisée.')
            ident = previous.id
            self.db.rollback()
            return self.db.get(ManagedReturn, ident)
        sale = self.db.get(ManagedSale, sale_id)
        session = self.db.get(ManagedCashSession, session_id)
        if not sale or not session or session.status != 'open':
            raise ValueError('Vente et caisse ouverte obligatoires.')
        if self.db.query(ManagedSaleCancellation.id).filter_by(sale_id=sale_id).first():
            raise ValueError('Cette vente est déjà annulée.')
        if cancel_sale and self.db.query(ManagedDepositIssue.id).join(ManagedSaleLine, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).filter(ManagedSaleLine.sale_id == sale_id).first():
            raise ValueError('Annulation de vente consignée indisponible : procédure spécifique requise.')
        credit = self.db.query(ManagedCreditSale).filter_by(sale_id=sale_id).one_or_none()
        links = self.db.query(ManagedSalePayment).filter_by(sale_id=sale_id).all()
        if sale.payment_method == 'credit':
            if not credit or reduction > credit.remaining_amount:
                raise ValueError('Réduction de créance supérieure au solde ou créance incohérente.')
            originals = [self.db.get(ManagedCashTransaction, link.transaction_id) for link in links]
        elif sale.payment_method == 'mixed' and credit is None:
            if len(links) < 2:
                raise ValueError('Encaissements mixtes incomplets.')
            originals = [self.db.get(ManagedCashTransaction, link.transaction_id) for link in links]
        elif sale.payment_method in METHODS and not links and credit is None:
            originals = self.db.query(ManagedCashTransaction).filter_by(sale_id=sale_id, kind='sale').all()
            if len(originals) != 1 or originals[0].method != sale.payment_method:
                raise ValueError('Encaissement d’origine incohérent.')
        else:
            raise ValueError('Type de vente non pris en charge pour un retour.')
        if credit is None and reduction:
            raise ValueError('Aucune créance à réduire.')
        if any(not p or p.method not in METHODS or p.amount <= 0 or (p.kind, p.sale_id) not in (('sale', sale_id), ('income', None)) for p in originals):
            raise ValueError('Encaissements incohérents.')
        original_map = {p.id: p for p in originals}
        direct = self.db.query(ManagedCashTransaction).filter_by(sale_id=sale_id).all()
        if any(p.id not in original_map for p in direct):
            raise ValueError('Encaissements incohérents.')
        active_returns = self.db.query(ManagedReturn.id).outerjoin(ManagedReturnCancellation, ManagedReturnCancellation.return_id == ManagedReturn.id).filter(ManagedReturn.sale_id == sale_id, ManagedReturnCancellation.id.is_(None))
        prior_returns = self.db.query(ManagedReturn).filter(ManagedReturn.id.in_(active_returns)).all()
        returned_total = fcfa(sum(r.total for r in prior_returns), 'Retours précédents')
        refunded_before = {}
        for ident, paid in self.db.query(ManagedReturnRefund.original_transaction_id, func.sum(ManagedCashTransaction.amount)).join(
                ManagedCashTransaction, ManagedReturnRefund.refund_transaction_id == ManagedCashTransaction.id).join(
                ManagedReturn, ManagedReturnRefund.return_id == ManagedReturn.id).filter(ManagedReturn.id.in_(active_returns)).group_by(ManagedReturnRefund.original_transaction_id):
            refunded_before[ident] = fcfa(paid, 'Remboursements précédents')
        deposit_returns = self.db.query(ManagedDepositReturn).join(ManagedDepositIssue, ManagedDepositReturn.issue_id == ManagedDepositIssue.id).join(
            ManagedSaleLine, ManagedDepositIssue.sale_line_id == ManagedSaleLine.id).outerjoin(ManagedDepositReturnCancellation, ManagedDepositReturnCancellation.return_id == ManagedDepositReturn.id).filter(ManagedSaleLine.sale_id == sale_id, ManagedDepositReturnCancellation.id.is_(None)).all()
        returned_total = fcfa(returned_total + sum(r.amount for r in deposit_returns), 'Retours précédents')
        for ident, paid in self.db.query(ManagedDepositRefund.original_transaction_id, func.sum(ManagedCashTransaction.amount)).join(
                ManagedCashTransaction, ManagedDepositRefund.refund_transaction_id == ManagedCashTransaction.id).filter(
                ManagedDepositRefund.deposit_return_id.in_([r.id for r in deposit_returns])).group_by(ManagedDepositRefund.original_transaction_id):
            refunded_before[ident] = fcfa(refunded_before.get(ident, 0) + paid, 'Remboursements précédents')
        paid_total = fcfa(sum(p.amount for p in originals), 'Total encaissé')
        net_paid = fcfa(paid_total - sum(refunded_before.values()), 'Encaissement net')
        due = credit.remaining_amount if credit else 0
        if returned_total > sale.total or net_paid < 0 or net_paid + due != sale.total - returned_total:
            raise ValueError('Solde de vente incohérent : diagnostic requis.')
        validated, total = [], 0
        for ident, count_text in amounts:
            line = self.db.get(ManagedSaleLine, ident)
            if not line or line.sale_id != sale_id or line.base_quantity <= 0 or line.amount < 0:
                raise ValueError('Ligne de vente incohérente.')
            before = self.db.query(func.coalesce(func.sum(ManagedReturnLine.base_quantity), 0)).filter(ManagedReturnLine.sale_line_id == ident, ManagedReturnLine.return_id.in_(active_returns)).scalar()
            count = quantity(count_text, 'Quantité retournée')
            if before + count > line.base_quantity:
                raise ValueError('Quantité retournée supérieure à la quantité vendue restante.')
            value = Fraction(count) * Fraction(line.amount) / Fraction(line.base_quantity)
            if value.denominator != 1:
                raise ValueError('Le montant du retour doit être un nombre entier de FCFA.')
            amount = fcfa(value.numerator, 'Montant du retour')
            total = fcfa(total + amount, 'Total du retour')
            validated.append((line, count, amount))
        refund_total = fcfa(sum(amount for _, amount in refunds_normalized), 'Total des remboursements')
        if fcfa(reduction + refund_total, 'Contrepartie du retour') != total:
            raise ValueError('La réduction de créance et les remboursements doivent correspondre au montant du retour.')
        for ident, amount in refunds_normalized:
            if ident not in original_map or amount + refunded_before.get(ident, 0) > original_map[ident].amount:
                raise ValueError('Remboursement supérieur à l’encaissement restant ou non lié à cette vente.')
        if cancel_sale:
            all_lines = self.db.query(ManagedSaleLine).filter_by(sale_id=sale_id).all()
            current = {line.id: count for line, count, _ in validated}
            for line in all_lines:
                prior = self.db.query(func.coalesce(func.sum(ManagedReturnLine.base_quantity), 0)).filter(
                    ManagedReturnLine.sale_line_id == line.id, ManagedReturnLine.return_id.in_(active_returns)).scalar()
                if prior + current.get(line.id, 0) != line.base_quantity:
                    raise ValueError('L’annulation totale exige le retour de toutes les quantités restantes.')
            if not all_lines or returned_total + total != sale.total or due - reduction != 0 or net_paid - refund_total != 0:
                raise ValueError('L’annulation totale exige l’extinction complète de la créance et des encaissements nets.')
        cash_amount = sum(amount for ident, amount in refunds_normalized if original_map[ident].method == 'cash')
        if cash_amount > ManagedCashService(self.db).cash_available(session):
            raise ValueError('Espèces insuffisantes pour le remboursement.')
        record = ManagedReturn(sale_id=sale_id, session_id=session_id, request_key=key, fingerprint=fingerprint,
                               reason=reason, total=total, credit_reduction=reduction)
        self.db.add(record)
        if credit:
            credit.remaining_amount -= reduction
        self.db.flush()
        reference = f'RETOUR-{record.id}'
        for line, count, amount in validated:
            product = self.db.get(Product, line.product_id)
            if not product or product.unit != line.base_unit or product.stock_quantity is None or product.stock_quantity < 0:
                raise ValueError('Stock ou unité incohérent : diagnostic requis.')
            before = product.stock_quantity
            quantity(before + count, 'Stock résultant', allow_zero=True)
            current_cost = product.average_cost if before else None
            if line.cost_numerator is None and line.cost_denominator is None:
                original_cost = None
            elif line.cost_numerator is None or line.cost_denominator is None:
                raise ValueError('Coût historique incomplet.')
            else:
                numerator, denominator = int(line.cost_numerator), int(line.cost_denominator)
                if numerator < 0 or denominator <= 0:
                    raise ValueError('Coût historique invalide.')
                original_cost = Fraction(numerator, denominator)
            if original_cost is None or (before and current_cost is None):
                product.average_cost_numerator = product.average_cost_denominator = None
            else:
                value = (Fraction(before) * (current_cost or 0) + Fraction(count) * original_cost) / Fraction(before + count)
                product.average_cost_numerator, product.average_cost_denominator = str(value.numerator), str(value.denominator)
            if not StockService(self.db).update_stock(product.id, count, 'sale_return', unit=product.unit,
                    reason=reason, reference_document=reference, commit=False):
                raise ValueError('Rétablissement du stock impossible.')
            self.db.add(ManagedReturnLine(return_id=record.id, sale_line_id=line.id, base_quantity=count, amount=amount))
        for ident, amount in refunds_normalized:
            original = original_map[ident]
            movement = ManagedCashTransaction(session_id=session_id, request_key=f'retour:{record.id}:{ident}', kind='outflow',
                method=original.method, amount=amount, description=f'Retour {sale.reference} — {reason}', reference=reference)
            self.db.add(movement)
            self.db.flush()
            self.db.add(ManagedReturnRefund(return_id=record.id, original_transaction_id=ident, refund_transaction_id=movement.id))
        if cancel_sale:
            self.db.add(ManagedSaleCancellation(sale_id=sale_id, session_id=session_id,
                                                request_key=f'retours:{key}', reason=reason))
        self.db.commit()
        self.db.refresh(record)
        return record
