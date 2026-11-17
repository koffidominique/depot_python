from enum import Enum

class PermissionEnum(Enum):
    # Dashboard
    VIEW_DASHBOARD = "view_dashboard"
    
    # Products
    VIEW_PRODUCTS = "view_products"
    CREATE_PRODUCT = "create_product"
    EDIT_PRODUCT = "edit_product"
    DELETE_PRODUCT = "delete_product"
    
    # Stock
    VIEW_STOCK = "view_stock"
    UPDATE_STOCK = "update_stock"
    VIEW_STOCK_MOVEMENTS = "view_stock_movements"
    MANAGE_INVENTORY = "manage_inventory"
    
    # Sales
    VIEW_SALES = "view_sales"
    CREATE_SALE = "create_sale"
    EDIT_SALE = "edit_sale"
    CANCEL_SALE = "cancel_sale"
    VIEW_SALE_DETAILS = "view_sale_details"
    
    # Purchases
    VIEW_PURCHASES = "view_purchases"
    CREATE_PURCHASE = "create_purchase"
    EDIT_PURCHASE = "edit_purchase"
    RECEIVE_PURCHASE = "receive_purchase"
    CANCEL_PURCHASE = "cancel_purchase"
    
    # Clients
    VIEW_CLIENTS = "view_clients"
    CREATE_CLIENT = "create_client"
    EDIT_CLIENT = "edit_client"
    DELETE_CLIENT = "delete_client"
    VIEW_CLIENT_DEBTS = "view_client_debts"
    
    # Suppliers
    VIEW_SUPPLIERS = "view_suppliers"
    CREATE_SUPPLIER = "create_supplier"
    EDIT_SUPPLIER = "edit_supplier"
    DELETE_SUPPLIER = "delete_supplier"
    VIEW_SUPPLIER_DEBTS = "view_supplier_debts"
    
    # Payments
    VIEW_PAYMENTS = "view_payments"
    RECORD_PAYMENT = "record_payment"
    EDIT_PAYMENT = "edit_payment"
    
    # Deliveries
    VIEW_DELIVERIES = "view_deliveries"
    CREATE_DELIVERY = "create_delivery"
    UPDATE_DELIVERY_STATUS = "update_delivery_status"
    
    # Consignations
    VIEW_CONSIGNATIONS = "view_consignations"
    MANAGE_CONSIGNATIONS = "manage_consignations"
    
    # Expenses
    VIEW_EXPENSES = "view_expenses"
    CREATE_EXPENSE = "create_expense"
    EDIT_EXPENSE = "edit_expense"
    
    # Cash
    VIEW_CASH = "view_cash"
    OPEN_CASH_SESSION = "open_cash_session"
    CLOSE_CASH_SESSION = "close_cash_session"
    VIEW_CASH_REPORTS = "view_cash_reports"
    
    # Reports
    VIEW_REPORTS = "view_reports"
    VIEW_FINANCIAL_REPORTS = "view_financial_reports"
    EXPORT_REPORTS = "export_reports"
    
    # Users
    VIEW_USERS = "view_users"
    CREATE_USER = "create_user"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    MANAGE_ROLES = "manage_roles"
    
    # Settings
    VIEW_SETTINGS = "view_settings"
    EDIT_SETTINGS = "edit_settings"
    MANAGE_BACKUPS = "manage_backups"
    RESTORE_BACKUP = "restore_backup"
    
    # Advanced
    PRINT_DOCUMENTS = "print_documents"
    GENERATE_DOCUMENTS = "generate_documents"

ROLE_PERMISSIONS = {
    "Administrateur": [p.value for p in PermissionEnum],
    
    "Gérant": [
        PermissionEnum.VIEW_DASHBOARD.value,
        PermissionEnum.VIEW_PRODUCTS.value,
        PermissionEnum.CREATE_PRODUCT.value,
        PermissionEnum.EDIT_PRODUCT.value,
        PermissionEnum.VIEW_STOCK.value,
        PermissionEnum.UPDATE_STOCK.value,
        PermissionEnum.VIEW_STOCK_MOVEMENTS.value,
        PermissionEnum.MANAGE_INVENTORY.value,
        PermissionEnum.VIEW_SALES.value,
        PermissionEnum.CREATE_SALE.value,
        PermissionEnum.EDIT_SALE.value,
        PermissionEnum.CANCEL_SALE.value,
        PermissionEnum.VIEW_PURCHASES.value,
        PermissionEnum.CREATE_PURCHASE.value,
        PermissionEnum.EDIT_PURCHASE.value,
        PermissionEnum.RECEIVE_PURCHASE.value,
        PermissionEnum.VIEW_CLIENTS.value,
        PermissionEnum.CREATE_CLIENT.value,
        PermissionEnum.EDIT_CLIENT.value,
        PermissionEnum.VIEW_CLIENT_DEBTS.value,
        PermissionEnum.VIEW_SUPPLIERS.value,
        PermissionEnum.CREATE_SUPPLIER.value,
        PermissionEnum.EDIT_SUPPLIER.value,
        PermissionEnum.VIEW_SUPPLIER_DEBTS.value,
        PermissionEnum.VIEW_PAYMENTS.value,
        PermissionEnum.RECORD_PAYMENT.value,
        PermissionEnum.VIEW_DELIVERIES.value,
        PermissionEnum.CREATE_DELIVERY.value,
        PermissionEnum.UPDATE_DELIVERY_STATUS.value,
        PermissionEnum.VIEW_CONSIGNATIONS.value,
        PermissionEnum.MANAGE_CONSIGNATIONS.value,
        PermissionEnum.VIEW_EXPENSES.value,
        PermissionEnum.CREATE_EXPENSE.value,
        PermissionEnum.VIEW_CASH.value,
        PermissionEnum.OPEN_CASH_SESSION.value,
        PermissionEnum.CLOSE_CASH_SESSION.value,
        PermissionEnum.VIEW_CASH_REPORTS.value,
        PermissionEnum.VIEW_REPORTS.value,
        PermissionEnum.VIEW_FINANCIAL_REPORTS.value,
        PermissionEnum.EXPORT_REPORTS.value,
        PermissionEnum.PRINT_DOCUMENTS.value,
        PermissionEnum.GENERATE_DOCUMENTS.value
    ],
    
    "Caissier": [
        PermissionEnum.VIEW_DASHBOARD.value,
        PermissionEnum.VIEW_SALES.value,
        PermissionEnum.CREATE_SALE.value,
        PermissionEnum.VIEW_PAYMENTS.value,
        PermissionEnum.RECORD_PAYMENT.value,
        PermissionEnum.VIEW_CLIENTS.value,
        PermissionEnum.VIEW_CONSIGNATIONS.value,
        PermissionEnum.MANAGE_CONSIGNATIONS.value,
        PermissionEnum.VIEW_CASH.value,
        PermissionEnum.OPEN_CASH_SESSION.value,
        PermissionEnum.VIEW_CASH_REPORTS.value,
        PermissionEnum.PRINT_DOCUMENTS.value,
        PermissionEnum.GENERATE_DOCUMENTS.value
    ],
    
    "Magasinier": [
        PermissionEnum.VIEW_DASHBOARD.value,
        PermissionEnum.VIEW_PRODUCTS.value,
        PermissionEnum.VIEW_STOCK.value,
        PermissionEnum.UPDATE_STOCK.value,
        PermissionEnum.VIEW_STOCK_MOVEMENTS.value,
        PermissionEnum.MANAGE_INVENTORY.value,
        PermissionEnum.VIEW_PURCHASES.value,
        PermissionEnum.RECEIVE_PURCHASE.value
    ],
    
    "Commercial": [
        PermissionEnum.VIEW_DASHBOARD.value,
        PermissionEnum.VIEW_SALES.value,
        PermissionEnum.CREATE_SALE.value,
        PermissionEnum.VIEW_CLIENTS.value,
        PermissionEnum.CREATE_CLIENT.value,
        PermissionEnum.EDIT_CLIENT.value,
        PermissionEnum.VIEW_CLIENT_DEBTS.value,
        PermissionEnum.VIEW_DELIVERIES.value,
        PermissionEnum.CREATE_DELIVERY.value,
        PermissionEnum.UPDATE_DELIVERY_STATUS.value
    ],
    
    "Livreur": [
        PermissionEnum.VIEW_DELIVERIES.value,
        PermissionEnum.UPDATE_DELIVERY_STATUS.value
    ],
    
    "Comptable": [
        PermissionEnum.VIEW_DASHBOARD.value,
        PermissionEnum.VIEW_SALES.value,
        PermissionEnum.VIEW_PURCHASES.value,
        PermissionEnum.VIEW_PAYMENTS.value,
        PermissionEnum.VIEW_CLIENT_DEBTS.value,
        PermissionEnum.VIEW_SUPPLIER_DEBTS.value,
        PermissionEnum.VIEW_EXPENSES.value,
        PermissionEnum.VIEW_CASH.value,
        PermissionEnum.VIEW_CASH_REPORTS.value,
        PermissionEnum.VIEW_REPORTS.value,
        PermissionEnum.VIEW_FINANCIAL_REPORTS.value,
        PermissionEnum.EXPORT_REPORTS.value,
        PermissionEnum.PRINT_DOCUMENTS.value,
        PermissionEnum.GENERATE_DOCUMENTS.value
    ]
}