"""Montants en francs CFA (XOF), sans fraction de franc."""
from decimal import Decimal, InvalidOperation

from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator


def fcfa(value, field_name="Montant") -> int:
    """Convertit un montant entier sans arrondir ni tronquer."""
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} doit être un nombre entier de FCFA")
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number != number.to_integral_value():
            raise ValueError(f"{field_name} doit être un nombre entier de FCFA")
        result = int(number)
        if not -(2**63) <= result < 2**63:
            raise ValueError(f"{field_name} dépasse la limite de stockage SQLite")
        return result
    except (InvalidOperation, TypeError, OverflowError):
        raise ValueError(f"{field_name} doit être un nombre entier de FCFA") from None


class CFAAmount(TypeDecorator):
    """Stockage INTEGER et contrôle des écritures et lectures historiques."""
    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else fcfa(value)

    def process_result_value(self, value, dialect):
        return None if value is None else fcfa(value, "Montant existant")
