from enum import Enum


class SaleStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    CHECK = "check"
    CREDIT = "credit"
    CONSIGNATION = "consignment"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class PurchaseStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DebtType(str, Enum):
    CLIENT = "client"
    SUPPLIER = "supplier"


class ConsignationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    ADMIN = "admin"
    VENDEUR = "vendeur"
    COMPTABLE = "comptable"
    GERANT = "gerant"
    INVENTORIEUR = "inventorieur"


class ExpenseCategory(str, Enum):
    REPAIR = "réparation"
    MAINTENANCE = "maintenance"
    ADMINISTRATIVE = "administrative"
    DIVERS = "divers"


class ConsignationItemType(str, Enum):
    PRODUIT = "produit"
    EQUIPEMENT = "équipement"
    MATERIEL = "matériel"
    AUTRE = "autre"