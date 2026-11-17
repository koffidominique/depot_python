"""Journal manuel des emballages vides présents au dépôt.

Ne calcule ni propriété, ni dette client/fournisseur, ni mouvement financier.
"""
from decimal import Decimal, InvalidOperation
from models.returnable_packaging import ReturnablePackagingType
from models.returnable_stock import ReturnableStockBalance, ReturnableStockMovement
from services.purchase_service import lock_for_write

MAX_QUANTITY = 2**63 - 1
MOVEMENT_SIGN = {'entry': 1, 'exit': -1, 'breakage': -1, 'loss': -1,
                 'correction_in': 1, 'correction_out': -1}


def _pieces(value, *, zero_allowed=False):
    if isinstance(value, bool) or value is None:
        raise ValueError('La quantité doit être un nombre entier de pièces.')
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number != number.to_integral_value() or number < (0 if zero_allowed else 1) or number > MAX_QUANTITY:
            raise ValueError
        return int(number)
    except (InvalidOperation, ValueError, TypeError, OverflowError):
        raise ValueError('La quantité doit être un nombre entier valide de pièces.') from None


class ReturnableStockService:
    def __init__(self, db):
        self.db = db

    def record(self, packaging_id, movement_type, quantity, reason, request_key, reference_document=None):
        if movement_type not in ('initial', *MOVEMENT_SIGN):
            raise ValueError('Type de mouvement inconnu.')
        amount = _pieces(quantity, zero_allowed=movement_type == 'initial')
        if not isinstance(reason, str) or not reason.strip() or len(reason.strip()) > 500:
            raise ValueError('Un motif est obligatoire (500 caractères maximum).')
        reason = reason.strip()
        if not isinstance(request_key, str) or not request_key.strip() or len(request_key) > 100:
            raise ValueError('Une clé unique de mouvement est obligatoire.')
        if reference_document is not None and not isinstance(reference_document, str):
            raise ValueError('Référence de document invalide.')
        reference = (reference_document or '').strip() or None
        if reference and len(reference) > 100:
            raise ValueError('Référence de document trop longue.')
        delta = amount if movement_type == 'initial' else amount * MOVEMENT_SIGN[movement_type]
        try:
            lock_for_write(self.db)
            previous = self.db.query(ReturnableStockMovement).filter_by(request_key=request_key).first()
            if previous:
                if (previous.packaging_id, previous.movement_type, previous.quantity, previous.reason, previous.reference_document) == (packaging_id, movement_type, delta, reason, reference):
                    previous_id = previous.id
                    self.db.rollback()
                    return self.db.get(ReturnableStockMovement, previous_id)
                raise ValueError('Cette clé de mouvement a déjà été utilisée.')
            item = self.db.get(ReturnablePackagingType, packaging_id)
            if not item or not item.is_active:
                raise ValueError('Emballage actif introuvable.')
            balance = self.db.get(ReturnableStockBalance, packaging_id)
            if movement_type == 'initial':
                if balance is not None:
                    raise ValueError('Le stock initial a déjà été déclaré.')
                before, after = None, amount
                balance = ReturnableStockBalance(packaging_id=packaging_id, quantity=after)
                self.db.add(balance)
            else:
                if balance is None:
                    raise ValueError('Déclarez d’abord le stock initial de vides.')
                before, after = balance.quantity, balance.quantity + delta
                if not 0 <= after <= MAX_QUANTITY:
                    raise ValueError('La quantité résultante doit rester entre zéro et la limite SQLite.')
                balance.quantity = after
            movement = ReturnableStockMovement(packaging_id=packaging_id, request_key=request_key,
                movement_type=movement_type, quantity=delta, stock_before=before, stock_after=after,
                reason=reason, reference_document=reference)
            self.db.add(movement)
            self.db.commit()
            self.db.refresh(movement)
            return movement
        except Exception:
            self.db.rollback()
            raise

    def balance(self, packaging_id):
        item = self.db.get(ReturnableStockBalance, packaging_id)
        return item.quantity if item else None

    def history(self, packaging_id, limit=100):
        return self.db.query(ReturnableStockMovement).filter_by(packaging_id=packaging_id).order_by(
            ReturnableStockMovement.id.desc()).limit(limit).all()
