"""Catalogue d'emballages physiques, sans mouvement ni consigne client."""
from sqlalchemy import func
from models.returnable_packaging import ReturnablePackagingType
from models.returnable_stock import ReturnableStockBalance
from money import fcfa
from services.purchase_service import lock_for_write


def _required(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError(f'{label} est obligatoire et limité à {maximum} caractères.')
    return value.strip()


class ReturnablePackagingService:
    def __init__(self, db):
        self.db = db

    def create(self, *, code, name, producer, kind, description=None, deposit_value=None):
        code = _required(code, 'Le code', 50)
        name = _required(name, 'Le nom', 150)
        producer = _required(producer, 'Le brasseur ou propriétaire du circuit', 150)
        if kind not in ('bottle', 'crate'):
            raise ValueError('Choisissez bouteille ou casier.')
        description = str(description or '').strip() or None
        if description and len(description) > 250:
            raise ValueError('La description est limitée à 250 caractères.')
        value = None if deposit_value is None or deposit_value == '' else fcfa(deposit_value, 'Valeur de consigne')
        if value is not None and value < 0:
            raise ValueError('La valeur de consigne ne peut pas être négative.')
        try:
            lock_for_write(self.db)
            if self.db.query(ReturnablePackagingType.id).filter(func.lower(ReturnablePackagingType.code) == code.lower()).first():
                raise ValueError('Ce code d’emballage existe déjà.')
            item = ReturnablePackagingType(code=code, name=name, producer=producer, kind=kind,
                                           description=description, deposit_value=value, is_active=True)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            return item
        except Exception:
            self.db.rollback()
            raise

    def archive(self, item_id):
        try:
            lock_for_write(self.db)
            item = self.db.get(ReturnablePackagingType, item_id)
            if not item or not item.is_active:
                raise ValueError('Emballage actif introuvable.')
            balance = self.db.get(ReturnableStockBalance, item_id)
            if balance is not None and balance.quantity != 0:
                raise ValueError('Impossible d’archiver un emballage dont le stock de vides est non nul.')
            item.is_active = False
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def list(self, include_archived=False):
        query = self.db.query(ReturnablePackagingType)
        if not include_archived:
            query = query.filter_by(is_active=True)
        return query.order_by(ReturnablePackagingType.producer, ReturnablePackagingType.name, ReturnablePackagingType.id).all()
