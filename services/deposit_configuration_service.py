"""Déclaration explicite de la composition physique, sans supposition métier."""
from decimal import Decimal
from models.deposit_configuration import DepositPackagingProfile, DepositPackagingComponent
from models.packaging import ProductPackaging
from models.returnable_packaging import ReturnablePackagingType
from money import fcfa
from services.packaging_service import quantity
from services.returnable_stock_service import _pieces
from services.sqlite_transaction import locked_write


class DepositConfigurationService:
    def __init__(self, db):
        self.db = db

    @locked_write
    def configure(self, packaging_id, mode, components):
        pack = self.db.get(ProductPackaging, packaging_id)
        if not pack or not pack.is_active or not pack.product.is_active:
            raise ValueError('Conditionnement actif introuvable.')
        if mode not in ('none', 'deposit') or not isinstance(components, (list, tuple)):
            raise ValueError('Choisissez explicitement avec ou sans consigne.')
        if (mode == 'none' and components) or (mode == 'deposit' and not components):
            raise ValueError('Indiquez des emballages uniquement pour une consigne configurée.')
        validated, seen = [], set()
        for component in components:
            if not isinstance(component, dict) or not isinstance(component.get('returnable_id'), int) or isinstance(component.get('returnable_id'), bool):
                raise ValueError('Emballage invalide.')
            ident = component['returnable_id']
            if ident in seen:
                raise ValueError('Chaque emballage ne peut être renseigné qu’une fois.')
            seen.add(ident)
            item = self.db.get(ReturnablePackagingType, ident)
            if not item or not item.is_active or item.deposit_value is None or item.deposit_value < 0:
                raise ValueError('Emballage actif et valeur de consigne explicite obligatoires.')
            pieces = _pieces(component.get('pieces_per_pack'))
            validated.append((ident, pieces))
        profile = self.db.get(DepositPackagingProfile, packaging_id)
        if profile is None:
            profile = DepositPackagingProfile(packaging_id=packaging_id, mode=mode)
            self.db.add(profile)
            self.db.flush()
        else:
            profile.mode = mode
            self.db.query(DepositPackagingComponent).filter_by(packaging_id=packaging_id).delete(synchronize_session=False)
        for ident, pieces in validated:
            self.db.add(DepositPackagingComponent(packaging_id=packaging_id, returnable_id=ident, pieces_per_pack=pieces))
        self.db.commit()

    def quote(self, packaging_id, count):
        pack = self.db.get(ProductPackaging, packaging_id)
        if not pack or not pack.is_active or not pack.product.is_active:
            raise ValueError('Conditionnement actif introuvable.')
        count = quantity(count)
        if not pack.allow_fraction and count != count.to_integral_value():
            raise ValueError('Ce conditionnement exige une quantité entière.')
        profile = self.db.get(DepositPackagingProfile, packaging_id)
        if profile is None:
            raise ValueError('Configurez explicitement la consigne de ce conditionnement.')
        components = self.db.query(DepositPackagingComponent).filter_by(packaging_id=packaging_id).order_by(DepositPackagingComponent.returnable_id).all()
        if profile.mode == 'none':
            if components:
                raise ValueError('Configuration de consigne incohérente.')
            return []
        if profile.mode != 'deposit' or not components:
            raise ValueError('Configuration de consigne incomplète.')
        result = []
        for component in components:
            item = self.db.get(ReturnablePackagingType, component.returnable_id)
            if not item or not item.is_active or item.deposit_value is None or item.deposit_value < 0:
                raise ValueError('Emballage archivé ou valeur de consigne inconnue.')
            pieces = Decimal(component.pieces_per_pack) * count
            if pieces != pieces.to_integral_value():
                raise ValueError('Le nombre de pièces consignées doit être entier.')
            pieces = _pieces(pieces)
            result.append({'returnable_id': item.id, 'code': item.code, 'pieces': pieces,
                           'unit_value': fcfa(item.deposit_value, 'Valeur de consigne'),
                           'amount': fcfa(pieces * item.deposit_value, 'Montant de consigne')})
        fcfa(sum(component['amount'] for component in result), 'Total consigne')
        return result
