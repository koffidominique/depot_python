from sqlalchemy.orm import Session
from sqlalchemy import func
from models.sale import Sale
from models.product import Product
from models.client import Client
from models.supplier import Supplier
from models.stock import StockMovement
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

class ReportingService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_kpis(self) -> Dict:
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        daily_sales = self.db.query(func.sum(Sale.total_amount)).filter(
            Sale.date >= start_of_day,
            Sale.date <= end_of_day,
            Sale.is_cancelled == False
        ).scalar() or Decimal('0.0')
        
        daily_sales_count = self.db.query(func.count(Sale.id)).filter(
            Sale.date >= start_of_day,
            Sale.date <= end_of_day,
            Sale.is_cancelled == False
        ).scalar() or 0
        
        stock_value = self._get_total_stock_value()
        
        low_stock_count = self.db.query(func.count(Product.id)).filter(
            Product.is_active == True,
            Product.stock_quantity <= Product.min_stock
        ).scalar() or 0
        
        client_debts = self._get_total_client_debts()
        supplier_debts = self._get_total_supplier_debts()
        
        active_clients = self.db.query(func.count(Client.id)).filter(
            Client.is_active == True
        ).scalar() or 0
        
        consignment_balance = self._get_total_consignment_balance()
        
        return {
            'daily_sales': daily_sales,
            'daily_sales_count': daily_sales_count,
            'stock_value': stock_value,
            'low_stock_count': low_stock_count,
            'client_debts': client_debts,
            'supplier_debts': supplier_debts,
            'active_clients': active_clients,
            'consignment_balance': consignment_balance
        }
    
    def get_sales_trend(self, days: int = 7) -> Dict:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        sales_data = []
        dates = []
        
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            start_of_day = datetime.combine(current_date, datetime.min.time())
            end_of_day = datetime.combine(current_date, datetime.max.time())
            
            daily_total = self.db.query(func.sum(Sale.total_amount)).filter(
                Sale.date >= start_of_day,
                Sale.date <= end_of_day,
                Sale.is_cancelled == False
            ).scalar() or Decimal('0.0')
            
            dates.append(current_date.strftime('%Y-%m-%d'))
            sales_data.append(float(daily_total))
        
        return {'dates': dates, 'sales': sales_data}
    
    def get_top_selling_products(self, limit: int = 10) -> List[Dict]:
        from models.sale import SaleLine
        
        top_products = self.db.query(
            Product.name,
            func.sum(SaleLine.quantity).label('total_quantity'),
            func.sum(SaleLine.line_total).label('total_revenue')
        ).join(SaleLine).join(Sale).filter(
            Sale.is_cancelled == False
        ).group_by(Product.id).order_by(func.sum(SaleLine.line_total).desc()).limit(limit).all()
        
        return [
            {
                'name': p.name,
                'quantity': float(p.total_quantity),
                'revenue': float(p.total_revenue)
            } for p in top_products
        ]
    
    def _get_total_stock_value(self) -> Decimal:
        products = self.db.query(Product).filter(Product.is_active == True).all()
        total_value = Decimal('0.0')
        for product in products:
            total_value += product.stock_quantity * product.purchase_price
        return total_value
    
    def _get_total_client_debts(self) -> Decimal:
        clients = self.db.query(Client).filter(Client.is_active == True).all()
        total = sum(client.financial_balance for client in clients)
        return total
    
    def _get_total_supplier_debts(self) -> Decimal:
        suppliers = self.db.query(Supplier).filter(Supplier.is_active == True).all()
        total = sum(supplier.balance_due for supplier in suppliers)
        return total
    
    def _get_total_consignment_balance(self) -> Decimal:
        clients = self.db.query(Client).filter(Client.is_active == True).all()
        total = sum(client.consignment_balance for client in clients)
        return total