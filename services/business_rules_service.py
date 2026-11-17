from sqlalchemy.orm import Session
from models.product import Product
from models.client import Client
from models.settings import Settings
from decimal import Decimal
from typing import Tuple, List

class BusinessRulesService:
    def __init__(self, db: Session):
        self.db = db
    
    def check_stock_availability(self, product_id: int, quantity: Decimal) -> Tuple[bool, str]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False, "Produit non trouvé"
        
        allow_negative_stock = self._get_setting('allow_negative_stock', False)
        
        if product.stock_quantity < quantity and not allow_negative_stock:
            return False, f"Stock insuffisant : {product.stock_quantity} disponible, {quantity} demandé"
        
        return True, "Stock disponible"
    
    def check_credit_limit(self, client_id: int, amount: Decimal) -> Tuple[bool, str]:
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False, "Client non trouvé"
        
        if not client.credit_limit:
            return True, "Pas de plafond de crédit défini"
        
        if client.balance + amount > client.credit_limit:
            return False, f"Plafond de crédit dépassé : {client.balance} FCFA dû, plafond {client.credit_limit} FCFA"
        
        return True, "Crédit autorisé"
    
    def validate_sale_creation(self, sale_data: dict, sale_lines: List[dict]) -> Tuple[bool, List[str]]:
        errors = []
        
        for line in sale_lines:
            product_id = line.get('product_id')
            quantity = Decimal(str(line.get('quantity', 0)))
            
            if quantity <= 0:
                errors.append(f"Quantité invalide pour le produit {product_id}")
                continue
            
            stock_ok, stock_msg = self.check_stock_availability(product_id, quantity)
            if not stock_ok:
                errors.append(stock_msg)
        
        if sale_data.get('client_id') and sale_data.get('payment_status') == 'pending':
            client_id = sale_data['client_id']
            total_amount = sum(Decimal(str(line.get('line_total', 0))) for line in sale_lines)
            credit_ok, credit_msg = self.check_credit_limit(client_id, total_amount)
            if not credit_ok:
                errors.append(credit_msg)
        
        return len(errors) == 0, errors
    
    def validate_purchase_reception(self, order_id: int, received_lines: List[dict]) -> Tuple[bool, List[str]]:
        errors = []
        
        for line in received_lines:
            if line.get('received_quantity', 0) <= 0:
                errors.append(f"Quantité reçue invalide pour la ligne {line.get('line_id')}")
        
        return len(errors) == 0, errors
    
    def validate_cash_closure(self, session_id: int, theoretical_total: Decimal, physical_total: Decimal) -> Tuple[bool, List[str]]:
        errors = []
        
        if theoretical_total < 0:
            errors.append("Le montant théorique ne peut pas être négatif")
        
        if physical_total < 0:
            errors.append("Le montant physique ne peut pas être négatif")
        
        difference = abs(theoretical_total - physical_total)
        max_allowed_difference = self._get_setting('max_cash_difference', Decimal('1000'))
        
        if difference > max_allowed_difference:
            errors.append(f"Écart de caisse trop important : {difference} FCFA (max autorisé {max_allowed_difference} FCFA)")
        
        return len(errors) == 0, errors
    
    def get_product_price(self, product: Product, price_type: str = 'wholesale') -> Decimal:
        if price_type == 'wholesale':
            return product.wholesale_price
        elif price_type == 'semi_wholesale':
            return product.semi_wholesale_price
        elif price_type == 'retail':
            return product.retail_price
        return product.wholesale_price
    
    def generate_document_reference(self, prefix: str) -> str:
        from datetime import datetime
        year = datetime.now().year
        last_doc = self.db.query(Settings).filter(Settings.key == f"last_{prefix}_number").first()
        next_number = 1
        if last_doc:
            next_number = int(last_doc.value) + 1
            last_doc.value = str(next_number)
        else:
            new_setting = Settings(key=f"last_{prefix}_number", value=str(next_number))
            self.db.add(new_setting)
        
        self.db.commit()
        return f"{prefix}-{year}-{next_number:06d}"
    
    def _get_setting(self, key: str, default_value=None):
        setting = self.db.query(Settings).filter(Settings.key == key).first()
        if setting:
            return setting.value
        return default_value
    
    def is_transaction_editable(self, transaction_type: str, transaction_date: datetime) -> bool:
        from datetime import datetime, timedelta
        edit_window_days = self._get_setting('transaction_edit_window', 7)
        cutoff_date = datetime.now() - timedelta(days=int(edit_window_days))
        return transaction_date >= cutoff_date