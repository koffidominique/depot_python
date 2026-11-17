"""Gestion des produits et de leurs conditionnements."""
from uuid import uuid4
import base64
from nicegui import ui
from config import DATA_DIR
from services.product_service import ProductService
from services.packaging_service import PackagingService, PACKAGING_TYPES
from services.product_csv_service import ProductCSVService
from services.supplier_service import SupplierService
from services.product_image_service import ProductImageService
from services.deposit_configuration_service import DepositConfigurationService
from models.deposit_configuration import DepositPackagingProfile, DepositPackagingComponent
from models.returnable_packaging import ReturnablePackagingType


def create_products_page(db, refresh_page):
    products = ProductService(db)
    packagings = PackagingService(db)
    csv_service = ProductCSVService(db)
    image_service = ProductImageService(db)
    deposit_service = DepositConfigurationService(db)
    selected = {'id': None}
    csv_data = {'text': None}

    def run(action):
        try:
            action()
        except Exception as exc:
            db.rollback()
            ui.notify(f'Opération impossible : {exc}', type='negative')

    def selected_product():
        if selected['id'] is None:
            raise ValueError('Sélectionnez un produit.')
        result = products.get_product_by_id(selected['id'])
        if not result:
            raise ValueError('Produit introuvable.')
        return result

    def category_dialog():
        with ui.dialog() as dialog, ui.card():
            ui.label('Nouvelle catégorie').classes('text-lg font-semibold')
            name = ui.input('Nom de la catégorie')
            def save():
                def action():
                    if not name.value or not name.value.strip():
                        raise ValueError('Le nom de catégorie est obligatoire.')
                    products.create_category(name.value.strip())
                    dialog.close()
                    refresh_page()
                    ui.notify('Catégorie enregistrée.', type='positive')
                run(action)
            ui.button('Enregistrer catégorie', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    def product_dialog(product=None):
        categories = {c.id: c.name for c in products.get_all_categories()}
        if not categories:
            ui.notify('Créez d’abord une catégorie.', type='warning')
            return
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
            ui.label('Modifier le produit' if product else 'Nouveau produit').classes('text-lg font-semibold')
            if product:
                cost = product.average_cost
                ui.label(f'Coût moyen exact : {cost} FCFA / {product.unit}' if cost is not None else 'Coût moyen : indisponible tant que les réceptions ne sont pas calculées.')
            name = ui.input('Nom du produit', value=product.name if product else '')
            category = ui.select(categories, label='Catégorie', value=product.category_id if product else None)
            brand = ui.input('Marque facultative', value=(product.brand or '') if product else '')
            description = ui.input('Description facultative', value=(product.description or '') if product else '')
            suppliers = {s.id: s.name for s in SupplierService(db).get_all_suppliers()}
            supplier = ui.select(suppliers, label='Fournisseur habituel facultatif', clearable=True,
                                 value=product.supplier_id if product else None)
            unit = ui.input('Unité de base', value=product.unit if product else '', placeholder='Ex. bouteille ou canette')
            barcode = ui.input('Code-barres facultatif', value=product.barcode or '' if product else '')
            prices = {}
            labels = [('purchase_price', 'Prix achat de référence FCFA'), ('wholesale_price', 'Prix gros FCFA'),
                      ('retail_price', 'Prix détail FCFA'), ('semi_wholesale_price', 'Prix semi-gros FCFA (facultatif)')]
            for field, label in labels:
                prices[field] = ui.input(label, value=str(getattr(product, field)) if product and getattr(product, field) is not None else '')
            initial = None if product else ui.input('Stock initial en unité de base', value='')
            minimum = ui.input('Seuil stock faible', value=str(product.min_stock) if product else '')
            def save():
                def action():
                    data = {'name': name.value, 'category_id': category.value, 'unit': unit.value,
                            'brand': brand.value or None, 'description': description.value or None,
                            'supplier_id': supplier.value,
                            'barcode': barcode.value, 'min_stock': minimum.value,
                            **{field: widget.value for field, widget in prices.items()}}
                    if product:
                        products.update_product(product.id, data)
                    else:
                        data['stock_quantity'] = initial.value
                        products.create_product(data)
                    dialog.close()
                    refresh_page()
                    ui.notify('Produit enregistré.', type='positive')
                run(action)
            ui.button('Enregistrer produit', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    def archive_dialog():
        def action():
            product = selected_product()
            with ui.dialog() as dialog, ui.card():
                ui.label(f'Archiver {product.name} ? L’historique sera conservé.')
                def confirm():
                    def commit():
                        products.deactivate_product(product.id)
                        dialog.close()
                        refresh_page()
                        ui.notify('Produit archivé.', type='positive')
                    run(commit)
                ui.button('Confirmer archivage', on_click=confirm)
                ui.button('Annuler', on_click=dialog.close)
            dialog.open()
        run(action)

    def packaging_dialog(product, item=None):
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
            ui.label(f'Conditionnement — {product.name}').classes('text-lg font-semibold')
            kind = ui.select(list(PACKAGING_TYPES), label='Conditionnement', value=item.name if item else None)
            coefficient = ui.input(f'Coefficient en {product.unit}', value=str(item.coefficient) if item else '')
            barcode = ui.input('Code-barres conditionnement', value=item.barcode or '' if item else '')
            values = {}
            for field, label in [('purchase_price', 'Prix achat FCFA (facultatif)'),
                                 ('wholesale_price', 'Prix gros FCFA (facultatif)'),
                                 ('retail_price', 'Prix détail FCFA (facultatif)'),
                                 ('semi_wholesale_price', 'Prix semi-gros FCFA (facultatif)')]:
                current = getattr(item, field) if item else None
                values[field] = ui.input(label, value=str(current) if current is not None else '')
            fraction = ui.checkbox('Autoriser les quantités fractionnaires', value=item.allow_fraction if item else False)
            active = ui.checkbox('Conditionnement actif', value=item.is_active if item else True)
            def save():
                def action():
                    packagings.save(product.id, {'name': kind.value, 'coefficient': coefficient.value,
                                                 'barcode': barcode.value, 'allow_fraction': fraction.value,
                                                 'is_active': active.value,
                                                 **{field: widget.value for field, widget in values.items()}},
                                    item.id if item else None)
                    dialog.close()
                    refresh_page()
                    ui.notify('Conditionnement enregistré.', type='positive')
                run(action)
            ui.button('Enregistrer conditionnement', on_click=save)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    def deposit_dialog(item):
        profile = db.get(DepositPackagingProfile, item.id)
        existing = {c.returnable_id: c.pieces_per_pack for c in db.query(DepositPackagingComponent).filter_by(packaging_id=item.id)}
        physical = db.query(ReturnablePackagingType).order_by(ReturnablePackagingType.producer, ReturnablePackagingType.name).all()
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
            ui.label(f'Consigne — {item.product.name} / {item.name}').classes('text-lg font-semibold')
            ui.label('Indiquez explicitement sans consigne ou la composition physique. Les ventes consignées exigent un client ; les annulations et retours de marchandise consignée restent bloqués.')
            mode = ui.select({'none': 'Sans consigne', 'deposit': 'Avec consigne'}, label='Configuration de consigne', value=profile.mode if profile else None)
            widgets = {}
            for physical_item in physical:
                value = 'non renseignée' if physical_item.deposit_value is None else f'{physical_item.deposit_value} FCFA'
                ui.label(f'{physical_item.code} — {physical_item.name} — {physical_item.producer} — valeur {value} — {"actif" if physical_item.is_active else "archivé"}')
                widgets[physical_item.id] = ui.input(f'Pièces {physical_item.code} par conditionnement', value=str(existing[physical_item.id]) if physical_item.id in existing else '')
            def save():
                def action():
                    components = [{'returnable_id': ident, 'pieces_per_pack': widget.value} for ident, widget in widgets.items() if widget.value not in (None, '')]
                    deposit_service.configure(item.id, mode.value, components)
                    dialog.close(); refresh_page(); ui.notify('Configuration de consigne enregistrée.', type='positive')
                run(action)
            ui.button('Enregistrer configuration consigne', on_click=save)
            ui.button('Fermer configuration consigne', on_click=dialog.close)
        dialog.open()

    def manage_packaging():
        def action():
            product = selected_product()
            items = packagings.list_for_product(product.id, include_inactive=True)
            with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
                ui.label(f'Conditionnements de {product.name}').classes('text-lg font-semibold')
                ui.label(f'Unité de base : {product.unit}')
                ui.button('Ajouter conditionnement', on_click=lambda: packaging_dialog(product))
                for item in items:
                    with ui.row().classes('items-center'):
                        ui.label(f'{item.name} : {item.coefficient} {item.base_unit} — {"actif" if item.is_active else "archivé"}')
                        ui.button('Modifier', on_click=lambda p=item: packaging_dialog(product, p))
                        profile = db.get(DepositPackagingProfile, item.id)
                        status = 'non définie' if profile is None else 'sans consigne' if profile.mode == 'none' else 'avec consigne'
                        ui.label(f'Consigne : {status}')
                        ui.button('Configurer consigne', on_click=lambda p=item: deposit_dialog(p))
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        run(action)

    def legacy_unit_dialog():
        def action():
            product = selected_product()
            if product.unit != 'unit':
                raise ValueError('Ce produit ne possède pas une unité historique générique.')
            with ui.dialog() as dialog, ui.card().classes('max-w-xl'):
                ui.label('Déclarer l’unité historique').classes('text-lg font-semibold')
                ui.label('Le stock et les historiques ne seront pas convertis. Vérifiez que chaque ancienne unité correspond exactement à l’unité indiquée.')
                unit = ui.input('Unité réelle')
                reason = ui.input('Motif et source de vérification')
                confirm = ui.checkbox('Je confirme que les anciennes quantités correspondent à cette unité')
                def save():
                    def commit():
                        products.declare_legacy_base_unit(product.id, unit.value, reason.value, confirmed=confirm.value)
                        dialog.close()
                        refresh_page()
                        ui.notify('Unité historique déclarée.', type='positive')
                    run(commit)
                ui.button('Confirmer unité', on_click=save)
                ui.button('Annuler', on_click=dialog.close)
            dialog.open()
        run(action)

    def image_dialog():
        def action():
            product = selected_product()
            with ui.dialog() as dialog, ui.card().classes('max-w-xl'):
                ui.label(f'Image — {product.name}').classes('text-lg font-semibold')
                path = image_service.safe_path(product)
                if path:
                    encoded = base64.b64encode(path.read_bytes()).decode('ascii')
                    ui.image('data:image/png;base64,' + encoded).classes('w-48')
                else:
                    ui.label('Aucune image disponible.')
                def upload(e):
                    def save():
                        image_service.save(product.id, e.content.read())
                        dialog.close()
                        refresh_page()
                        ui.notify('Image enregistrée.', type='positive')
                    run(save)
                ui.upload(label='Choisir une image JPEG ou PNG', auto_upload=True,
                          max_file_size=5 * 1024 * 1024, on_upload=upload,
                          on_rejected=lambda _: ui.notify('Image refusée : taille supérieure à 5 Mo ou format incompatible.', type='negative')).props('accept=.jpg,.jpeg,.png')
                if path:
                    def remove():
                        def commit():
                            image_service.remove(product.id)
                            dialog.close()
                            refresh_page()
                            ui.notify('Image retirée de la fiche.', type='positive')
                        run(commit)
                    ui.button('Retirer image', on_click=remove)
                ui.button('Fermer', on_click=dialog.close)
            dialog.open()
        run(action)

    def export_csv():
        def action():
            target = DATA_DIR / 'Exports' / f'produits_{uuid4().hex}.csv'
            target.write_text(csv_service.export_csv(), encoding='utf-8-sig')
            ui.download(target, filename='produits.csv')
        run(action)

    def csv_dialog():
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl'):
            ui.label('Import CSV — prévisualisation').classes('text-lg font-semibold')
            ui.label('Utilisez les colonnes du fichier exporté. Les catégories doivent déjà exister. Ce CSV ne contient ni conditionnements, ni images, ni historique : ce n’est pas une sauvegarde.')
            result = ui.label('Aucun fichier chargé.')
            preview_table = ui.table(columns=[{'name': 'line', 'label': 'Ligne', 'field': 'line'},
                                               {'name': 'reference', 'label': 'Référence', 'field': 'reference'},
                                               {'name': 'name', 'label': 'Nom', 'field': 'name'},
                                               {'name': 'errors', 'label': 'Erreurs', 'field': 'errors'}], rows=[], row_key='line', pagination=10)
            def load(e):
                csv_data['text'] = None
                def action():
                    text = e.content.read().decode('utf-8-sig')
                    rows = csv_service.preview(text)
                    preview_table.rows = [{'line': r['line'], 'reference': r.get('reference', ''), 'name': r.get('name', ''),
                                           'errors': '; '.join(r['errors'])} for r in rows]
                    preview_table.update()
                    invalid = sum(bool(r['errors']) for r in rows)
                    result.text = f'{len(rows)} ligne(s), {invalid} invalide(s).'
                    if not invalid:
                        csv_data['text'] = text
                run(action)
            ui.upload(label='Choisir un CSV', auto_upload=True, max_file_size=1048576, on_upload=load,
                      on_rejected=lambda _: ui.notify('Fichier refusé : taille supérieure à 1 Mo ou format incompatible.', type='negative')).props('accept=.csv')
            def do_import():
                def action():
                    if csv_data['text'] is None:
                        raise ValueError('Chargez un fichier sans erreur avant l’import.')
                    count = csv_service.import_csv(csv_data['text'])
                    csv_data['text'] = None
                    dialog.close()
                    refresh_page()
                    ui.notify(f'{count} produit(s) importé(s).', type='positive')
                run(action)
            ui.button('Confirmer import', on_click=do_import)
            ui.button('Fermer', on_click=dialog.close)
        dialog.open()

    with ui.column().classes('w-full gap-4 p-6'):
        ui.label('Produits et conditionnements').classes('text-2xl font-bold')
        ui.label('Les parcours de vente et d’approvisionnement restent partiels ; ne pas utiliser en production.')
        with ui.row().classes('gap-2'):
            ui.button('Nouvelle catégorie', on_click=category_dialog)
            ui.button('Nouveau produit', on_click=lambda: product_dialog())
            ui.button('Modifier produit', on_click=lambda: run(lambda: product_dialog(selected_product())))
            ui.button('Archiver produit', on_click=archive_dialog)
            ui.button('Conditionnements', on_click=manage_packaging)
            ui.button('Déclarer unité historique', on_click=legacy_unit_dialog)
            ui.button('Image produit', on_click=image_dialog)
            ui.button('Exporter CSV', on_click=export_csv)
            ui.button('Importer CSV', on_click=csv_dialog)
        filters = {'search': '', 'category': None, 'archived': False, 'page': 1}
        def filter_change(key, value):
            filters.update({key: value, 'page': 1})
            refresh_table()
        with ui.row().classes('w-full gap-3'):
            ui.input('Rechercher nom, référence ou code-barres',
                     on_change=lambda e: filter_change('search', e.value or '')).classes('w-72')
            ui.select({c.id: c.name for c in products.get_all_categories()}, label='Filtrer par catégorie',
                      clearable=True, on_change=lambda e: filter_change('category', e.value)).classes('w-56')
            ui.checkbox('Afficher les produits archivés', on_change=lambda e: filter_change('archived', e.value))
        selector = ui.select({}, label='Sélectionner un produit de cette page',
                             on_change=lambda e: selected.update(id=e.value), with_input=True, clearable=True).classes('w-full max-w-xl')
        columns = [{'name': c, 'label': label, 'field': c} for c, label in
                   [('reference', 'Référence'), ('name', 'Produit'), ('category', 'Catégorie'),
                    ('unit', 'Unité'), ('stock', 'Stock'), ('retail', 'Détail FCFA'), ('status', 'Statut')]]
        table = ui.table(columns=columns, rows=[], row_key='id', pagination=15).classes('w-full')
        with ui.row().classes('items-center gap-3'):
            def move(delta):
                filters['page'] = max(1, filters['page'] + delta)
                refresh_table()
            previous = ui.button('Page précédente', on_click=lambda: move(-1))
            page_label = ui.label('')
            following = ui.button('Page suivante', on_click=lambda: move(1))

        def refresh_table():
            records, total, page = products.get_products_page(page=filters['page'], page_size=15,
                search=filters['search'], category_id=filters['category'], include_inactive=filters['archived'])
            filters['page'] = page
            options = {p.id: f'{p.reference} — {p.name}' for p in records}
            chosen = selected['id'] if selected['id'] in options else None
            selected['id'] = chosen
            selector.set_options(options, value=chosen)
            table.rows = [{'id': p.id, 'reference': p.reference, 'name': p.name, 'category': p.category.name,
                           'unit': p.unit, 'stock': str(p.stock_quantity), 'retail': p.retail_price,
                           'status': 'Actif' if p.is_active else 'Archivé'} for p in records]
            table.update()
            total_pages = max(1, (total + 14) // 15)
            page_label.text = f'Page {page} / {total_pages} — {total} produit(s)'
            previous.set_enabled(page > 1)
            following.set_enabled(page < total_pages)
        refresh_table()
