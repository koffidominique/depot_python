"""Moyens de paiement reconnus ; chacun reste distinct des espèces."""
METHODS = {'cash': 'Espèces', 'mobile_money': 'Mobile Money (non précisé)',
           'orange_money': 'Orange Money', 'wave': 'Wave', 'mtn_money': 'MTN Mobile Money',
           'transfer': 'Virement', 'card': 'Carte', 'check': 'Chèque', 'other': 'Autre'}


def labels(db, *, active_only=False):
    """Libellés conservés pour les transactions historiques, actifs pour la saisie."""
    from models.payment_method import PaymentMethod
    query = db.query(PaymentMethod)
    if active_only:
        query = query.filter_by(active=True)
    return {row.code: row.label for row in query.order_by(PaymentMethod.label, PaymentMethod.code)}


def require_active(db, code):
    from models.payment_method import PaymentMethod
    item = db.get(PaymentMethod, code) if isinstance(code, str) else None
    if not item or not item.active:
        raise ValueError('Moyen de paiement actif requis.')


class PaymentMethodService:
    def __init__(self, db):
        self.db = db

    def create(self, label):
        from uuid import uuid4
        from models.payment_method import PaymentMethod
        from services.sqlite_transaction import lock_for_write
        if not isinstance(label, str) or not label.strip() or len(label.strip()) > 100:
            raise ValueError('Libellé obligatoire (100 caractères maximum).')
        try:
            lock_for_write(self.db)
            name = label.strip()
            if any(row.label.casefold() == name.casefold() for row in self.db.query(PaymentMethod).filter_by(active=True)):
                raise ValueError('Ce libellé actif existe déjà.')
            item = PaymentMethod(code='custom_' + uuid4().hex, label=name, active=True)
            self.db.add(item)
            self.db.commit()
            return item.code
        except Exception:
            self.db.rollback()
            raise

    def deactivate(self, code):
        from models.payment_method import PaymentMethod
        from services.sqlite_transaction import lock_for_write
        try:
            lock_for_write(self.db)
            item = self.db.get(PaymentMethod, code)
            if not item or not item.active or code == 'cash':
                raise ValueError('Moyen introuvable, inactif ou espèces non désactivables.')
            item.active = False
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def rename(self, code, new_label):
        """Crée une nouvelle version ; l'ancien code conserve son libellé historique."""
        from uuid import uuid4
        from models.payment_method import PaymentMethod
        from services.sqlite_transaction import lock_for_write
        if not isinstance(new_label, str) or not new_label.strip() or len(new_label.strip()) > 100:
            raise ValueError('Libellé obligatoire (100 caractères maximum).')
        try:
            lock_for_write(self.db)
            old = self.db.get(PaymentMethod, code)
            if not old or not old.active or code == 'cash':
                raise ValueError('Moyen introuvable, inactif ou espèces non modifiables.')
            name = new_label.strip()
            if any(row.label.casefold() == name.casefold() for row in self.db.query(PaymentMethod).filter_by(active=True)):
                raise ValueError('Ce libellé actif existe déjà.')
            old.active = False
            new = PaymentMethod(code='custom_' + uuid4().hex, label=name, active=True)
            self.db.add(new)
            self.db.commit()
            return new.code
        except Exception:
            self.db.rollback()
            raise
