"""Définitions versionnées des protections SQLite inter-tables des codes-barres."""

TRIGGERS = {}
for table, other in (('products', 'product_packagings'), ('product_packagings', 'products')):
    for action in ('INSERT', 'UPDATE'):
        name = f'barcode_{table}_{action.lower()}_guard'
        event = 'INSERT' if action == 'INSERT' else 'UPDATE OF barcode'
        TRIGGERS[name] = (
            f'CREATE TRIGGER {name} BEFORE {event} ON {table} '
            f'WHEN NEW.barcode IS NOT NULL AND EXISTS '
            f'(SELECT 1 FROM {other} WHERE barcode = NEW.barcode) '
            "BEGIN SELECT RAISE(ABORT, 'Code-barres déjà utilisé'); END"
        )


def verify_barcode_constraints(db):
    for name, expected in TRIGGERS.items():
        row = db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (name,)).fetchone()
        if not row or ' '.join(row[0].split()).lower() != ' '.join(expected.split()).lower():
            raise ValueError(f'Protection de code-barres absente ou incompatible : {name}.')
    if db.execute('SELECT 1 FROM products p JOIN product_packagings c ON p.barcode = c.barcode LIMIT 1').fetchone():
        raise ValueError('Codes-barres identiques entre produits et conditionnements : diagnostic requis.')
