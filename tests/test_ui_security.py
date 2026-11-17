"""Test navigateur optionnel : DEPOTPRO_BROWSER pointe vers Chromium local."""
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

BROWSER = os.environ.get('DEPOTPRO_BROWSER')
pytestmark = pytest.mark.skipif(not BROWSER, reason='Définir DEPOTPRO_BROWSER pour les tests navigateur')


@pytest.fixture
def application(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    env['HOME'] = str(tmp_path)
    command = ('from main import initialize_app; from nicegui import ui; '
               f'initialize_app(); ui.run(host="127.0.0.1", port={port}, show=False, reload=False, language="fr")')
    process = subprocess.Popen([sys.executable, '-c', command], cwd=Path(__file__).resolve().parents[1],
                               env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url = f'http://127.0.0.1:{port}/'
    try:
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(f'Le serveur a quitté : {process.stdout.read()}')
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.1)
        else:
            pytest.fail('Le serveur ne répond pas')
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        output = process.stdout.read()
        if 'Traceback' in output:
            print('SERVER LOG:', output)
        process.stdout.close()


def test_premier_pin_verrouillage_et_parametres(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        context = browser.new_context()
        external_requests = []
        def local_only(route):
            from urllib.parse import urlsplit
            if urlsplit(route.request.url).hostname not in ('127.0.0.1', 'localhost'):
                external_requests.append(route.request.url)
                route.abort()
            else:
                route.continue_()
        context.route('**/*', local_only)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()

        def enter(pin):
            for digit in pin:
                page.get_by_role('button', name=digit, exact=True).click()

        enter('123456')
        page.get_by_text('Confirmez votre PIN').wait_for()
        enter('123456')
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        second = context.new_page()
        second.goto(application)
        second.get_by_text('Entrez votre PIN').wait_for()
        assert second.get_by_text('Les données existantes sont conservées.').count() == 0
        second.close()
        page.get_by_role('button', name='Paramètres et sécurité').click()
        page.get_by_text('Modifier le PIN', exact=True).first.wait_for()
        page.get_by_label('PIN actuel').fill('123456')
        page.get_by_label('Nouveau PIN à 6 chiffres').fill('654321')
        page.get_by_label('Confirmer le nouveau PIN').fill('654321')
        page.get_by_role('button', name='Modifier le PIN').click()
        page.get_by_text('PIN modifié.').wait_for()
        page.get_by_label('Délai en minutes').fill('1')
        page.get_by_role('button', name='Enregistrer le délai').click()
        page.get_by_text('Délai enregistré.').wait_for()
        page.get_by_role('button', name='Verrouiller').click()
        page.get_by_text('Entrez votre PIN').wait_for()
        for _ in range(3):
            enter('000000')
            page.get_by_text('Code PIN incorrect.').wait_for()
        enter('654321')
        page.get_by_text('Trop de tentatives.', exact=False).wait_for()
        page.wait_for_timeout(6000)
        enter('654321')
        page.get_by_text('Modifier le PIN', exact=True).first.wait_for()
        # Inactivité réelle : 60 s + période de contrôle de 5 s.
        page.get_by_text('Entrez votre PIN').wait_for(timeout=72000)
        assert not errors
        assert not external_requests
        browser.close()


def test_produits_et_conditionnement(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Produits', exact=True).click()
        page.get_by_text('Produits et conditionnements').wait_for()
        page.get_by_role('button', name='Nouvelle catégorie').click()
        page.get_by_label('Nom de la catégorie').fill('Boissons test')
        page.get_by_role('button', name='Enregistrer catégorie').click()
        page.get_by_text('Catégorie enregistrée.').wait_for()
        page.get_by_role('button', name='Nouveau produit').click()
        page.get_by_label('Nom du produit').fill('Eau test')
        page.get_by_label('Catégorie', exact=True).click()
        page.get_by_role('option', name='Boissons test').click()
        page.get_by_label('Unité de base', exact=True).fill('bouteille')
        for label, value in [('Prix achat de référence FCFA', '100'), ('Prix gros FCFA', '150'),
                             ('Prix détail FCFA', '200'), ('Prix semi-gros FCFA (facultatif)', '175'),
                             ('Stock initial en unité de base', '10'), ('Seuil stock faible', '2')]:
            page.get_by_label(label, exact=True).fill(value)
        page.get_by_role('button', name='Enregistrer produit').click()
        page.get_by_text('Produit enregistré.').wait_for()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Eau test', exact=False).click()
        page.get_by_role('button', name='Conditionnements', exact=True).click()
        page.get_by_role('button', name='Ajouter conditionnement').click()
        page.get_by_label('Conditionnement', exact=True).click()
        page.get_by_role('option', name='casier', exact=True).click()
        page.get_by_label('Coefficient en bouteille').fill('24')
        page.get_by_label('Prix gros FCFA (facultatif)').fill('3600')
        page.get_by_role('button', name='Enregistrer conditionnement').click()
        page.get_by_text('Conditionnement enregistré.').wait_for()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Eau test', exact=False).click()
        page.get_by_role('button', name='Conditionnements', exact=True).click()
        page.get_by_text('casier : 24.000 bouteille', exact=False).wait_for()
        page.get_by_role('button', name='Fermer').last.click()
        page.get_by_role('button', name='Image produit').click()
        from io import BytesIO
        from PIL import Image
        content_image = BytesIO()
        Image.new('RGB', (10, 10), 'red').save(content_image, format='PNG')
        page.locator('input[type=file]').set_input_files({'name': 'produit.png', 'mimeType': 'image/png', 'buffer': content_image.getvalue()})
        page.get_by_text('Image enregistrée.').wait_for()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Eau test', exact=False).click()
        page.get_by_role('button', name='Image produit').click()
        page.get_by_role('button', name='Retirer image').wait_for()
        page.get_by_role('button', name='Retirer image').click()
        page.get_by_text('Image retirée de la fiche.').wait_for()
        page.get_by_role('button', name='Importer CSV').click()
        content = ('reference,name,category,unit,barcode,purchase_price,wholesale_price,retail_price,semi_wholesale_price,stock_quantity,min_stock\n'
                   'IMP-1,Jus test,Boissons test,bouteille,,100,120,150,,6,1\n')
        page.locator('input[type=file]').set_input_files({'name': 'produits.csv', 'mimeType': 'text/csv', 'buffer': content.encode()})
        page.get_by_text('1 ligne(s), 0 invalide(s).').wait_for()
        page.get_by_role('button', name='Confirmer import').click()
        page.get_by_text('1 produit(s) importé(s).').wait_for()
        page.get_by_text('Jus test').first.wait_for()
        with page.expect_download() as downloaded:
            page.get_by_role('button', name='Exporter CSV').click()
        assert downloaded.value.suggested_filename == 'produits.csv'
        assert 'Jus test' in downloaded.value.path().read_text(encoding='utf-8-sig')
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Jus test', exact=False).click()
        page.get_by_role('button', name='Archiver produit').click()
        page.get_by_role('button', name='Confirmer archivage').click()
        page.get_by_text('Produit archivé.').wait_for()
        assert page.get_by_text('Jus test').count() == 0
        page.get_by_text('Afficher les produits archivés').click()
        page.get_by_text('Jus test').first.wait_for()
        page.get_by_label('Rechercher nom, référence ou code-barres').fill('Eau test')
        page.get_by_label('Rechercher nom, référence ou code-barres').press('Tab')
        page.get_by_text('Eau test').first.wait_for()
        assert page.get_by_text('Jus test').count() == 0
        browser.close()


def test_pagination_et_unite_historique(application, tmp_path):
    import sqlite3
    playwright = pytest.importorskip('playwright.sync_api')
    database = tmp_path / 'DepotPro_Data' / 'depot.db'
    with sqlite3.connect(database) as db:
        db.execute("INSERT INTO categories (id, name, is_active) VALUES (1, 'Ancien', 1)")
        for i in range(20):
            db.execute('INSERT INTO products (name, reference, category_id, unit, stock_quantity, min_stock, is_active) VALUES (?, ?, 1, ?, ?, 0, 1)',
                       (f'{i:02} Article', f'P-{i}', 'unit' if i == 0 else 'bouteille', 9 if i == 0 else 0))
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Produits', exact=True).click()
        page.get_by_text('Page 1 / 2 — 20 produit(s)').wait_for()
        page.get_by_role('button', name='Page suivante').click()
        page.get_by_text('Page 2 / 2 — 20 produit(s)').wait_for()
        assert page.get_by_text('19 Article').first.is_visible()
        page.get_by_role('button', name='Page précédente').click()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='00 Article', exact=False).click()
        page.get_by_role('button', name='Déclarer unité historique').click()
        page.get_by_label('Unité réelle').fill('bouteille')
        page.get_by_label('Motif et source de vérification').fill('Contrôle des étiquettes originales')
        page.get_by_text('Je confirme que les anciennes quantités correspondent à cette unité').click()
        page.get_by_role('button', name='Confirmer unité').click()
        page.get_by_text('Unité historique déclarée.').wait_for()
        browser.close()
    with sqlite3.connect(database) as db:
        assert db.execute("SELECT unit, stock_quantity FROM products WHERE reference='P-0'").fetchone() == ('bouteille', 9)
        assert db.execute("SELECT quantity, stock_before, stock_after FROM stock_movements WHERE movement_type='unit_declaration'").fetchone() == (0, 9, 9)


def test_inventaire_physique_ui(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Produits', exact=True).click()
        page.get_by_role('button', name='Nouvelle catégorie').click()
        page.get_by_label('Nom de la catégorie').fill('Inventaire')
        page.get_by_role('button', name='Enregistrer catégorie').click()
        page.get_by_text('Catégorie enregistrée.').wait_for()
        page.get_by_role('button', name='Nouveau produit').click()
        page.get_by_label('Nom du produit').fill('Eau inventaire')
        page.get_by_label('Catégorie', exact=True).click()
        page.get_by_role('option', name='Inventaire').click()
        page.get_by_label('Unité de base', exact=True).fill('bouteille')
        page.get_by_label('Stock initial en unité de base').fill('10')
        page.get_by_label('Seuil stock faible').fill('0')
        page.get_by_role('button', name='Enregistrer produit').click()
        page.get_by_text('Produit enregistré.').wait_for()
        page.get_by_role('button', name='Stocks et inventaires').click()
        page.get_by_role('button', name='Nouvel inventaire').click()
        page.get_by_label('Produits à compter').click()
        page.get_by_role('option', name='Eau inventaire', exact=False).click()
        page.keyboard.press('Escape')
        page.get_by_role('button', name='Démarrer', exact=True).click()
        page.get_by_text('Inventaire démarré.').wait_for()
        page.get_by_role('button', name='Ouvrir inventaire').click()
        page.get_by_label('Stock physique').fill('7')
        page.get_by_label('Motif de l’écart').fill('Casse')
        page.get_by_role('button', name='Enregistrer comptage').click()
        page.get_by_text('Comptage enregistré.', exact=False).wait_for()
        page.get_by_role('button', name='Ouvrir inventaire').click()
        page.get_by_text('Écart enregistré : -3', exact=False).wait_for()
        page.get_by_role('button', name='Valider inventaire').click()
        page.get_by_role('button', name='Confirmer validation').click()
        page.get_by_text('Inventaire validé.').wait_for()
        page.get_by_text('État et alertes de stock').click()
        page.get_by_text('Eau inventaire : 7.000 bouteille', exact=False).wait_for()
        assert not errors
        browser.close()


def test_approvisionnement_et_reglement_ui(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Produits', exact=True).click()
        page.get_by_role('button', name='Nouvelle catégorie').click()
        page.get_by_label('Nom de la catégorie').fill('Boissons réception')
        page.get_by_role('button', name='Enregistrer catégorie').click()
        page.get_by_text('Catégorie enregistrée.').wait_for()
        page.get_by_role('button', name='Nouveau produit').click()
        page.get_by_label('Nom du produit').fill('Eau réception')
        page.get_by_label('Catégorie', exact=True).click()
        page.get_by_role('option', name='Boissons réception').click()
        page.get_by_label('Unité de base', exact=True).fill('bouteille')
        page.get_by_label('Stock initial en unité de base').fill('0')
        page.get_by_label('Seuil stock faible').fill('0')
        page.get_by_role('button', name='Enregistrer produit').click()
        page.get_by_text('Produit enregistré.').wait_for()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Eau réception', exact=False).click()
        page.get_by_role('button', name='Conditionnements', exact=True).click()
        page.get_by_role('button', name='Ajouter conditionnement').click()
        page.get_by_label('Conditionnement', exact=True).click()
        page.get_by_role('option', name='casier', exact=True).click()
        page.get_by_label('Coefficient en bouteille').fill('24')
        page.get_by_role('button', name='Enregistrer conditionnement').click()
        page.get_by_text('Conditionnement enregistré.').wait_for()
        page.get_by_role('button', name='Approvisionnements', exact=True).click()
        page.get_by_role('button', name='Nouveau fournisseur').click()
        page.get_by_label('Nom fournisseur').fill('Fournisseur test')
        page.get_by_label('Téléphone fournisseur').fill('010101')
        page.get_by_role('button', name='Enregistrer fournisseur').click()
        page.get_by_text('Fournisseur enregistré.').wait_for()
        page.get_by_role('button', name='Nouvelle commande').click()
        page.get_by_label('Fournisseur', exact=True).click()
        page.get_by_role('option', name='Fournisseur test', exact=False).click()
        page.get_by_label('Référence facultative').fill('CMD-TEST')
        page.get_by_label('Conditionnement', exact=True).click()
        page.get_by_role('option', name='Eau réception', exact=False).click()
        page.get_by_label('Quantité commandée').fill('10')
        page.get_by_label('Prix par conditionnement FCFA').fill('2400')
        page.get_by_label('Remise par conditionnement FCFA').fill('100')
        page.get_by_label('Frais par conditionnement FCFA').fill('50')
        page.get_by_role('button', name='Ajouter ligne').click()
        page.get_by_role('button', name='Enregistrer commande').click()
        page.get_by_text('Commande enregistrée en brouillon.').wait_for()
        page.get_by_role('button', name='Ouvrir commande').click()
        page.get_by_role('button', name='Valider commande').click()
        page.get_by_text('Commande validée.').wait_for()
        page.get_by_role('button', name='Ouvrir commande').click()
        page.get_by_label('Reçu ligne', exact=False).fill('10')
        page.get_by_role('button', name='Enregistrer réception').click()
        page.get_by_text('Réception enregistrée.').wait_for()
        page.get_by_role('button', name='Caisse et trésorerie').click()
        page.get_by_role('button', name='Ouvrir caisse').click()
        page.get_by_label('Fonds initial espèces FCFA').fill('10000')
        page.get_by_role('button', name='Confirmer ouverture').click()
        page.get_by_text('Caisse ouverte.').wait_for()
        page.get_by_role('button', name='Approvisionnements', exact=True).click()
        page.get_by_role('button', name='Ouvrir commande').click()
        page.get_by_text('reste 23500 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Régler cette dette').click()
        page.get_by_label('Montant à régler FCFA').fill('5000')
        page.get_by_label('Moyen de paiement').click()
        page.get_by_role('option', name='Espèces').click()
        page.get_by_role('button', name='Enregistrer règlement').click()
        page.get_by_text('Règlement enregistré en caisse.').wait_for()
        page.get_by_role('button', name='Ouvrir commande').click()
        page.get_by_text('reste 18500 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Fermer', exact=True).last.click()
        page.get_by_role('button', name='Caisse et trésorerie').click()
        page.get_by_text('espèces théoriques : 5000 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Clôturer caisse').click()
        page.get_by_label('Espèces comptées FCFA').fill('5000')
        page.get_by_role('button', name='Confirmer clôture').click()
        page.get_by_text('Caisse clôturée.').wait_for()
        page.get_by_text('écart 0 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Stocks et inventaires').click()
        page.get_by_text('État et alertes de stock').click()
        page.get_by_text('Eau réception : 240.000 bouteille', exact=False).wait_for()
        assert not errors
        browser.close()


def test_catalogue_emballages_ui(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Emballages consignés').click()
        page.get_by_text('Les achats, ventes et retours ne mettent pas ce journal', exact=False).wait_for()
        page.get_by_role('button', name='Nouvel emballage').click()
        page.get_by_label('Code emballage').fill('TEST-C24')
        page.get_by_label('Nom emballage').fill('Casier test')
        page.get_by_label('Brasseur ou propriétaire du circuit').fill('Circuit test')
        page.get_by_label('Type physique').click()
        page.get_by_role('option', name='Casier', exact=True).click()
        page.get_by_label('Description ou format confirmé (facultatif)').fill('C24')
        page.get_by_role('button', name='Enregistrer emballage').click()
        page.get_by_text('Emballage enregistré.').wait_for()
        page.get_by_text('TEST-C24', exact=False).wait_for()
        page.get_by_text('consigne non renseignée', exact=False).wait_for()
        page.get_by_text('stock de vides enregistré : non déclaré', exact=False).wait_for()
        page.get_by_role('button', name='Déclarer stock initial').click()
        page.get_by_label('Nombre de pièces vides').fill('10')
        page.get_by_label('Motif du mouvement').fill('Comptage')
        page.get_by_role('button', name='Confirmer mouvement').click()
        page.get_by_text('Mouvement de vides enregistré.').wait_for()
        page.get_by_text('stock de vides enregistré : 10', exact=False).wait_for()
        page.get_by_role('button', name='Mouvement de vides', exact=True).click()
        page.get_by_label('Type de mouvement').click()
        page.get_by_role('option', name='Sortie', exact=True).click()
        page.get_by_label('Nombre de pièces vides').fill('10')
        page.get_by_label('Motif du mouvement').fill('Retour fournisseur')
        page.get_by_label('Référence de document (facultatif)').fill('BON-VIDE')
        page.get_by_role('button', name='Confirmer mouvement').click()
        page.get_by_text('stock de vides enregistré : 0', exact=False).wait_for()
        page.get_by_role('button', name='Historique des vides').click()
        page.get_by_text('BON-VIDE', exact=False).wait_for()
        page.get_by_role('button', name='Fermer historique').click()
        page.get_by_role('button', name='Archiver emballage').click()
        page.get_by_role('button', name='Confirmer archivage').click()
        page.get_by_text('Emballage archivé.').wait_for()
        page.get_by_text('archivé', exact=False).first.wait_for()
        assert not errors
        browser.close()


def test_vente_depense_et_caisse_ui(application):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(executable_path=BROWSER, headless=True, args=['--no-sandbox'])
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(application)
        page.get_by_text('Créez votre PIN à 6 chiffres').wait_for()
        for digit in '123456123456':
            page.get_by_role('button', name=digit, exact=True).click()
        page.get_by_text('Les données existantes sont conservées.').wait_for()
        page.get_by_role('button', name='Produits', exact=True).click()
        page.get_by_role('button', name='Nouvelle catégorie').click()
        page.get_by_label('Nom de la catégorie').fill('Ventes test')
        page.get_by_role('button', name='Enregistrer catégorie').click()
        page.get_by_text('Catégorie enregistrée.').wait_for()
        page.get_by_role('button', name='Nouveau produit').click()
        page.get_by_label('Nom du produit').fill('Boisson vente')
        page.get_by_label('Catégorie', exact=True).click()
        page.get_by_role('option', name='Ventes test').click()
        page.get_by_label('Unité de base', exact=True).fill('bouteille')
        page.get_by_label('Stock initial en unité de base').fill('48')
        page.get_by_label('Seuil stock faible').fill('0')
        page.get_by_role('button', name='Enregistrer produit').click()
        page.get_by_text('Produit enregistré.').wait_for()
        page.get_by_label('Sélectionner un produit de cette page').click()
        page.get_by_role('option', name='Boisson vente', exact=False).click()
        page.get_by_role('button', name='Conditionnements', exact=True).click()
        page.get_by_role('button', name='Ajouter conditionnement').click()
        page.get_by_label('Conditionnement', exact=True).click()
        page.get_by_role('option', name='casier', exact=True).click()
        page.get_by_label('Coefficient en bouteille').fill('24')
        page.get_by_label('Prix détail FCFA (facultatif)').fill('3000')
        page.get_by_role('button', name='Enregistrer conditionnement').click()
        page.get_by_text('Conditionnement enregistré.').wait_for()
        page.get_by_role('button', name='Caisse et trésorerie').click()
        page.get_by_role('button', name='Ouvrir caisse').click()
        page.get_by_label('Fonds initial espèces FCFA').fill('1000')
        page.get_by_role('button', name='Confirmer ouverture').click()
        page.get_by_text('Caisse ouverte.').wait_for()
        page.get_by_role('button', name='Ventes au comptant').click()
        page.get_by_role('button', name='Nouvelle vente au comptant').click()
        page.get_by_label('Tarif de vente').click()
        page.get_by_role('option', name='Détail', exact=True).click()
        page.get_by_label('Moyen de paiement').click()
        page.get_by_role('option', name='Espèces', exact=True).click()
        page.get_by_label('Conditionnement à vendre').click()
        page.get_by_role('option', name='Boisson vente', exact=False).click()
        page.get_by_label('Quantité vendue').fill('1')
        page.get_by_role('button', name='Ajouter au panier').click()
        page.get_by_role('button', name='Vérifier vente').click()
        page.get_by_text('Total à encaisser : 3000 FCFA').wait_for()
        page.get_by_role('button', name='Confirmer et encaisser').click()
        page.get_by_text('Vente enregistrée : 3000 FCFA.').wait_for()
        page.get_by_role('button', name='Caisse et trésorerie').click()
        page.get_by_text('espèces théoriques : 4000 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Nouvelle dépense ou autre mouvement').click()
        page.get_by_label('Type de mouvement').click()
        page.get_by_role('option', name='Dépense', exact=True).click()
        page.get_by_label('Moyen de paiement').click()
        page.get_by_role('option', name='Espèces', exact=True).click()
        page.get_by_label('Montant FCFA').fill('500')
        page.get_by_label('Description obligatoire').fill('Carburant')
        page.get_by_label('Catégorie de dépense (obligatoire pour dépense)').click()
        page.get_by_role('option', name='Carburant', exact=True).click()
        page.get_by_role('button', name='Enregistrer mouvement').click()
        page.get_by_text('Mouvement de trésorerie enregistré.').wait_for()
        page.get_by_text('espèces théoriques : 3500 FCFA', exact=False).wait_for()
        page.get_by_role('button', name='Stocks et inventaires').click()
        page.get_by_text('État et alertes de stock').click()
        page.get_by_text('Boisson vente : 24.000 bouteille', exact=False).wait_for()
        assert not errors
        browser.close()
