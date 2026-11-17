# Vérifications

## 17 novembre 2026 — audit et fondations

Environnement Linux Python 3.11.2, dépendances épinglées installées dans un
venv temporaire, `pip check` : aucune incompatibilité déclarée ; import `main` OK.
`pytest -q` : 36 réussis au début de l'audit. Ces tests ne sont pas une validation
fonctionnelle complète : les scénarios A–J de MAJ.md et les interfaces restent à
couvrir. Aucun test ni build Windows ou macOS, aucun test de fonctionnement hors
ligne ou fenêtre native n'a été réalisé. Aucune base commerciale n'a été modifiée.

## 17 novembre 2026 — infrastructure de versionnement

39 tests réussis après ajout du suivi de migration et de trois tests : sauvegarde
préalable et idempotence, refus d'une base étrangère et d'une version inconnue.
Les vérifications finales du tour sont indiquées dans le compte rendu ; la version 1
n'est qu'un journal, pas une migration des données ni une validation de la phase 1.

Vérification finale : 42 tests réussis, dont échec simulé avant commit, refus des
clés étrangères invalides et sauvegarde d'une transaction présente dans le WAL.
`pip check` et compilation Python réussis. Avertissement SQLAlchemy sur l'import
historique de `declarative_base` ; non bloquant pour ces tests.

## Phase 1 — sécurité et initialisation

Tests automatisés : initialisation sans compte par défaut, refus d'une ancienne base
non migrée, migration de PIN en clair avec conservation des données et sauvegarde,
retour arrière interversions sur copie, hachage bcrypt, confirmation, temporisation,
modification de PIN et paramétrage du délai. Test manuel HTTP local sur base temporaire :
la page de premier démarrage répond 200 après correction d'une incompatibilité entre
NiceGUI 1.4 et Starlette récent (FastAPI/Starlette épinglés). Aucun test d'interaction
navigateur, de verrouillage inactivité visuel, d'OS cible ou de fenêtre native.

Vérification finale : 48 tests réussis ; `pip check`, compilation et `git diff
--check` réussis. L'exécution HTTP n'est pas un test du clavier ou de l'inactivité.

## Validation navigateur de la phase 1

Le parcours `tests/test_ui_security.py` utilise une base temporaire et un serveur
local, sans toucher à une base commerciale. Il couvre la création et confirmation
du PIN, l'isolation d'un second onglet, le changement de PIN, le verrouillage
manuel, les tentatives incorrectes et la temporisation, ainsi que le verrouillage
après 60 secondes réelles d'inactivité. Les requêtes non locales sont bloquées et
vérifiées pendant ce parcours limité : cela ne valide pas encore les futures pages
commerciales ni le mode hors ligne complet.

Sur Linux, il a été exécuté avec Playwright 1.50 et Chromium headless 133 ; il a
révélé puis permis de corriger l'utilisation de `ui.spacer`, absente de NiceGUI
1.4. La fenêtre native, Windows et macOS restent non testés.

Pour réexécuter avec un navigateur local compatible :

```
pip install -r requirements.txt -r requirements-dev.txt -r requirements-ui-tests.txt
DEPOTPRO_BROWSER=/chemin/vers/chromium python -m pytest -q tests/test_ui_security.py
```

Sans `DEPOTPRO_BROWSER`, le test navigateur est signalé comme ignoré. Il attend
au moins une minute pour tester réellement l'inactivité.

## Phase 2 — produits et conditionnements

Tests unitaires sur les coefficients fictifs 6/12/24/1, tarifs, valeurs invalides,
fractions, codes-barres, archivage, mouvements de stock initial, import CSV atomique
et migration de la version 2 sans modification du PIN ni des produits. Test
navigateur Linux : catégorie, produit, casier, import/aperçu, export, archivage et
filtrage. Aucun achat ou vente avec conversion n'est testé : ces flux ne sont pas
encore intégrés. Le coût moyen, les images, la pagination serveur et la migration
des unités historiques restent à faire.

## Phase 2 — compléments

Pagination SQL, recherche échappée, images locales, refus des fichiers invalides,
nettoyage en cas d'échec d'écriture, déclaration d'unité historique avec confirmation
et mouvement non destructif, migration 4 et coût moyen rationnel non initialisé.
Les tests navigateur couvrent également l'image, la pagination et la déclaration
d'unité. Le calcul de coût moyen à la réception et les scénarios achats/ventes sont
à réaliser pendant les phases suivantes ; le test sous Windows/macOS reste absent.

Vérification finale Linux : 74 tests réussis, y compris les trois tests navigateur
avec Chromium headless ; `pip check` et `git diff --check` réussis. Aucun test sur
Windows/macOS ni de parcours achat/vente avec conversion n'a été effectué.

## Phase 3 — progression

Tests sur bases temporaires : réception de 10 casiers configurés à 24 bouteilles
(240 unités), réception partielle, déduplication, dépassement, conditionnement
figé, coût pondéré et coût initial inconnu ; refus des fractions de FCFA. Inventaire
avec mouvement traçable, seconde validation refusée, comptage incomplet ou sans
motif refusé, mouvement intermédiaire et transaction annulée ; corrections de stock.
Parcours navigateur Chromium Linux : création de produit, inventaire, comptage et
validation. Suite complète : 85 tests réussis, un avertissement SQLAlchemy.
Les achats ne sont pas accessibles par l'interface ; les dettes/paiements fournisseurs
et les scénarios Windows/macOS restent non testés et non terminés.

## Phase 3 — achats et stocks, compléments

Suite complète Linux : 91 tests réussis (dont parcours Chromium création fournisseur,
commande, remise/frais unitaires, réception de 10 casiers de 24, dette, règlement
partiel hors caisse et stock à 240). Tests de déduplication et de dépassement des
réceptions et règlements, annulation transactionnelle des écritures en cas d'erreur,
coût moyen, inventaire, échéance facultative et migration de v5 à v6 avec conservation
d'une dette historique. `pip check` et `git diff --check` réussis. Les règlements ne
créent pas de mouvement de caisse ; la caisse multi-moyens reste à réaliser et les
parcours Windows/macOS ne sont pas testés.

## Sous-dépôt — premier incrément

96 tests réussis sous Linux, dont Chromium headless pour la création et
l'archivage d'un emballage ; migration v6 vers v7 avec sauvegarde, conservation
produit/PIN, réexécution et refus d'un catalogue non versionné déjà rempli.
Tests de montants fractionnaires, code dupliqué et valeur de consigne inconnue.
Aucune validation Windows/macOS. Le suivi des vides et des consignes clients n'est
pas encore implémenté ; ces tests ne le couvrent pas.

## Sous-dépôt — journal manuel des vides

102 tests réussis sous Linux, dont navigateur Chromium pour déclarer 10 vides,
enregistrer leur sortie, consulter l'historique et archiver à solde nul. Tests du
stock initial inconnu, zéro déclaré, fractions interdites, stock négatif,
déduplication, sessions longues concurrentes, conservation et sauvegarde lors de
la migration 7 vers 8, et refus de données non versionnées. Les flux clients,
fournisseurs et la comptabilité des consignes ne sont pas intégrés ni testés.

## Caisse fournisseurs — premier périmètre

Suite Linux complète : 109 tests réussis dont navigateur création d'une commande,
réception, ouverture, règlement en espèces et clôture. Tests de déduplication,
solde espèces insuffisant, séparation Mobile Money, fermeture avec écart motivé,
rejet d'une ancienne caisse ouverte, sauvegarde/migration v8-v9, préservation des
paiements hors caisse et rollback en cas d'échec d'écriture caisse. `pip check` et
`git diff --check` réussis. Pas de test Windows/macOS ni de caisse générale.

## Caisse et ventes au comptant — extension

117 tests réussis sous Linux, dont navigateur : ouverture de caisse, vente au
comptant d'un casier de 24, mouvement stock, encaissement, dépense carburant et
contrôle des espèces. Tests de déduplication, rollback en cas d'échec de caisse,
prix modifié après aperçu, stock insuffisant, refus de consigne connue et migration
v9-v10 avec sauvegarde et préservation des sessions. `pip check` et `git diff
--check` réussis. Pas de tests Windows/macOS, ni de parcours crédit ou retour.
