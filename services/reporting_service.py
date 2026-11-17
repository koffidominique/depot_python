from sqlalchemy.orm import Session
from models.sale import Sale
from models.expense import Expense
from models.product import Product
from models.client import Client
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict

class ReportingService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_sales_report(self, date: datetime) -> Dict:
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        sales = self.db.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date < end_date,
            Sale.status == 'completed'
        ).all()
        
        total_sales = sum(s.total_amount for s in sales)
        total_transactions = len(sales)
        average_transaction = total_sales / total_transactions if total_transactions > 0 else Decimal('0')
        
        return {
            'date': date,
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'average_transaction': average_transaction,
            'sales': sales
        }
    
    def get_daily_expenses_report(self, date: datetime) -> Dict:
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        expenses = self.db.query(Expense).filter(
            Expense.expense_date >= start_date,
            Expense.expense_date < end_date
        ).all()
        
        total_expenses = sum(e.amount for e in expenses)
        
        return {
            'date': date,
            'total_expenses': total_expenses,
            'expenses': expenses
        }
    
    def get_sales_summary_report(self, start_date: datetime, end_date: datetime) -> Dict:
        sales = self.db.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.status == 'completed'
        ).all()
        
        total_sales = sum(s.total_amount for s in sales)
        total_paid = sum(s.total_amount for s in sales if s.payment_status == 'paid')
        total_pending = sum(s.total_amount for s in sales if s.payment_status == 'pending')
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': total_sales,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'sales_count': len(sales)
        }
    
    def get_top_selling_products(self, start_date: datetime, end_date: datetime, limit: int = 10) -> List[Dict]:
        from models.sale import SaleLine
        results = self.db.query(
            Product.id,
            Product.name,
            Product.sku,
            SaleLine.quantity,
            SaleLine.line_total
        ).join(SaleLine).join(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.status == 'completed'
        ).all()
        
        product_sales = {}
        for product_id, name, sku, quantity, line_total in results:
            if product_id not in product_sales:
                product_sales[product_id] = {
                    'id': product_id,
                    'name': name,
                    'sku': sku,
                    'total_quantity': Decimal('0'),
                    'total_sales': Decimal('0')
                }
            product_sales[product_id]['total_quantity'] += quantity
            product_sales[product_id]['total_sales'] += line_total
        
        sorted_products = sorted(product_sales.values(), key=lambda x: x['total_sales'], reverse=True)
        return sorted_products[:limit]
    
    def get_client_balance_report(self) -> List[Dict]:
        clients = self.db.query(Client).all()
        return [
            {
                'id': c.id,
                'name': c.name,
                'phone': c.phone,
                'balance': c.balance,
                'credit_limit': c.credit_limit
            } for c in clients
        ]
    
    def get_stock_valuation_report(self) -> Dict:
        products = self.db.query(Product).all()
        total_wholesale = sum(p.stock_quantity * p.wholesale_price for p in products)
        total_retail = sum(p.stock_quantity * p.retail_price for p in products)
        
        return {
            'products_count': len(products),
            'total_wholesale_value': total_wholesale,
            'total_retail_value': total_retail,
            'products': products
        }