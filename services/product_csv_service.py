"""Échange CSV explicite et atomique de produits, sans écraser l'existant."""
import csv
import io
from decimal import Decimal
from models.product import Product, Category
from models.stock import StockMovement
from services.packaging_service import quantity
from services.product_service import ProductService
from services.sqlite_transaction import locked_write

FIELDS = ['reference', 'name', 'category', 'unit', 'barcode', 'purchase_price',
          'wholesale_price', 'retail_price', 'semi_wholesale_price', 'stock_quantity', 'min_stock']


class ProductCSVService:
    def __init__(self, db):
        self.db = db
        self.products = ProductService(db)

    def export_csv(self):
        output = io.StringIO(newline='')
        writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        for product in self.db.query(Product).filter_by(is_active=True).order_by(Product.name):
            writer.writerow({'reference': product.reference, 'name': product.name,
                             'category': product.category.name, 'unit': product.unit,
                             'barcode': product.barcode or '', 'purchase_price': product.purchase_price,
                             'wholesale_price': product.wholesale_price, 'retail_price': product.retail_price,
                             'semi_wholesale_price': product.semi_wholesale_price,
                             'stock_quantity': product.stock_quantity, 'min_stock': product.min_stock})
        return output.getvalue()

    def preview(self, contents):
        if not isinstance(contents, str) or len(contents.encode('utf-8')) > 1024 * 1024:
            raise ValueError('Le fichier CSV dépasse 1 Mo ou son encodage est invalide.')
        reader = csv.DictReader(io.StringIO(contents.lstrip('\ufeff'), newline=''), strict=True)
        try:
            fields = reader.fieldnames
        except csv.Error as exc:
            raise ValueError(f'Fichier CSV illisible : {exc}') from exc
        if not fields or len(set(fields)) != len(fields) or set(fields) != set(FIELDS):
            raise ValueError('En-têtes CSV invalides. Utilisez le format exporté par DEPOTPRO.')
        output, seen_refs, seen_barcodes = [], set(), set()
        try:
            for number, row in enumerate(reader, start=2):
                if number > 1001:
                    raise ValueError('Le fichier dépasse 1 000 lignes.')
                if None in row or any(value is None for value in row.values()):
                    output.append({'line': number, 'errors': ['Nombre de colonnes invalide.']})
                    continue
                errors = []
                reference = row['reference'].strip()
                barcode = row['barcode'].strip() or None
                if not reference:
                    errors.append('Référence obligatoire.')
                elif reference in seen_refs or self.products.get_product_by_reference(reference):
                    errors.append('Référence déjà utilisée.')
                seen_refs.add(reference)
                if barcode and (barcode in seen_barcodes or self.products.get_product_by_barcode(barcode)):
                    errors.append('Code-barres déjà utilisé.')
                if barcode:
                    seen_barcodes.add(barcode)
                category = self.db.query(Category).filter_by(name=row['category'].strip(), is_active=True).first()
                if not category:
                    errors.append('Catégorie active introuvable.')
                if row['unit'].strip().lower() in ('', 'unit'):
                    errors.append('Unité de base réelle obligatoire.')
                try:
                    data = self.products._validate_data({
                        'name': row['name'], 'category_id': category.id if category else None,
                        'unit': row['unit'], 'barcode': barcode,
                        'purchase_price': row['purchase_price'] or None, 'wholesale_price': row['wholesale_price'] or None,
                        'retail_price': row['retail_price'] or None, 'semi_wholesale_price': row['semi_wholesale_price'] or None,
                        'min_stock': row['min_stock'],
                    })
                    initial = quantity(row['stock_quantity'], 'Stock initial', allow_zero=True)
                except ValueError as exc:
                    errors.append(str(exc))
                    data, initial = None, None
                output.append({'line': number, 'reference': reference, 'name': row['name'],
                               'errors': errors, 'data': data, 'stock': initial})
        except csv.Error as exc:
            raise ValueError(f'Fichier CSV illisible : {exc}') from exc
        if not output:
            raise ValueError('Le fichier ne contient aucun produit.')
        return output

    @locked_write
    def import_csv(self, contents):
        rows = self.preview(contents)
        if any(row['errors'] for row in rows):
            raise ValueError('Import annulé : corrigez toutes les lignes invalides.')
        try:
            for row in rows:
                product = Product(reference=row['reference'], stock_quantity=row['stock'], **row['data'])
                self.db.add(product)
                self.db.flush()
                if row['stock']:
                    self.db.add(StockMovement(product_id=product.id, movement_type='initial_stock',
                                              quantity=row['stock'], stock_before=Decimal(0),
                                              stock_after=row['stock'], unit=product.unit,
                                              reason='Import : stock initial', reference_document=product.reference))
            self.db.commit()
            return len(rows)
        except Exception:
            self.db.rollback()
            raise
