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

## Audit actualisé — phase 0, branche arena/be170884-depot-python

Python 3.11.2 Linux, environnement virtuel temporaire et dépendances du projet :
`pip check` réussi ; `pytest -q --tb=short` : **110 réussis, 7 ignorés**, un
avertissement SQLAlchemy. Les sept tests navigateur sont ignorés car Chromium et
`DEPOTPRO_BROWSER` ne sont pas configurés. Import individuel : échecs de
`services.business_rules_service` (`datetime`) et `services.cash_closure_service`
(`CashRegister`). Aucune base commerciale ni plateforme Windows/macOS testée.
Le résultat antérieur de 117 tests, navigateur inclus, est historique et n'a pas
été reproduit dans cet environnement.

## Reprise phase 1 — 17 novembre 2026

Sur Linux/Python 3.11.2 : 114 tests réussis et 7 tests navigateur ignorés ;
`pip check` et `git diff --check` réussis. Tests supplémentaires : modification
concurrente du PIN, persistance des échecs, refus d'une base temporaire dont
l'index de caisse unique a été supprimé et refus d'une clé étrangère invalide,
sans réparation ni suppression de l'historique. Le premier démarrage est exercé
sur une base temporaire. Une tentative de préparation de Chromium headless a
échoué faute de bibliothèques NSS/NSPR dans cet environnement ; le résultat
navigateur d'un précédent environnement demeure historique, pas une validation
actuelle. Aucune base commerciale, installation Windows/macOS ou fenêtre native
n'a été testée. Les contrôles de schéma ne vérifient pas toutes les contraintes ni
la cohérence métier et peuvent refuser une ancienne base incomplète : diagnostiquer
sur copie après sauvegarde, ne pas corriger en supprimant les données.

### Complément : parcours navigateur et migration simulée

La suite complète a ensuite été exécutée sur Linux avec Playwright 1.50 et
Chromium headless 133, utilisant les bibliothèques fournies dans l'archive
`al2023` du paquet npm `@sparticuz/chromium` dans un répertoire temporaire :
**121 tests réussis**, aucun ignoré, un avertissement SQLAlchemy. Cela inclut le
parcours PIN, changement de PIN, temporisation, verrouillage et inactivité réelle,
ainsi que six autres parcours UI existants. Le test PIN bloque et vérifie les
requêtes externes, ce qui ne démontre pas le fonctionnement hors ligne de toute
l'application. Depuis, un test supplémentaire vérifie le refus d'un index de caisse
de mauvaise définition, et le test de migration vérifie aussi le schéma migré :
**24 tests ciblés de démarrage et migration réussis**. `pip check` et `git diff
--check` réussis. Pas de test Windows/macOS, fenêtre native, installateur ni base
commerciale réelle ; une migration représentative sur copie reste indispensable.

## Reprise phase 2 — 17 novembre 2026

La suite complète Linux avec Chromium headless : **126 tests réussis**, un
avertissement SQLAlchemy, `pip check` et `git diff --check` réussis. Les tests
ajoutés couvrent notamment une course réelle entre création de produit et de
conditionnement avec même code-barres sur SQLite fichier, la conservation de
modifications en attente, et le refus atomique d'un CSV mal formé. Deux tests
supplémentaires ont ensuite été ajoutés : canette comme unité de base et conflit
CSV/conditionnement ; **15 tests ciblés produits/CSV réussis** après cet ajout.
Les exemples de coefficients sont des données de test, pas des valeurs imposées.
Aucune validation d'une base commerciale, d'un installateur ou de Windows/macOS.

## Prix ajusté et codes-barres — 17 novembre 2026

Suite complète sur Linux/Python 3.11.2 et Chromium headless : **133 tests réussis**,
un avertissement SQLAlchemy ; `pip check` et `git diff --check` réussis. La
migration v10→v11 est exercée sur bases temporaires : sauvegarde préalable,
conservation des données, refus d'une collision préexistante sans altération,
refus des insertions et mises à jour SQL directes des deux côtés et refus du
démarrage si un déclencheur manque. Le parcours navigateur couvre la saisie d'un
prix ajusté, l'aperçu, l'encaissement et le prix enregistré en base ; les tests
métier vérifient aussi idempotence, tarif modifié depuis l'aperçu, prix invalide,
refus d'une fraction de FCFA et invariants stock/caisse en cas d'échec. Windows,
macOS et base commerciale réelle non testés.

## Paiements mixtes au comptant — 17 novembre 2026

Linux/Python 3.11.2 avec Chromium headless : **142 tests réussis**, un avertissement
SQLAlchemy ; `pip check` et `git diff --check` réussis. Les tests couvrent la
migration v11→v12 sur copie temporaire avec sauvegarde et conservation d'une vente
et d'un mouvement historique, une vente répartie espèces/Wave, les liens aux
mouvements, l'idempotence, les montants invalides ou différents du total et le
rollback si le second mouvement échoue. Le parcours navigateur vérifie l'aperçu,
l'encaissement, le stock et les flux séparés. Aucun test ni migration de base
commerciale réelle, aucun test Windows/macOS. Les paiements mixtes ne prennent
pas encore en charge le crédit, les consignes ou les annulations.

## Annulation totale au comptant — 17 novembre 2026

Suite complète Linux/Python 3.11.2 avec Chromium headless : **149 tests réussis**,
un avertissement SQLAlchemy ; `pip check` et `git diff --check` réussis. Tests
sur bases temporaires : migration v12→v13 avec sauvegarde et conservation de
vente/mouvement historiques, annulation intégrale d'une vente mixte, remboursements
séparés et reliés aux encaissements, idempotence, retour du stock, coût moyen
pondéré, refus sans confirmation de récupération ou espèces suffisantes, rollback
d'un échec de remboursement, historique incohérent et remboursement dans une
session suivante sans changer la clôture précédente. Parcours navigateur testé.
Les retours partiels, le crédit, les consignes et leurs annulations ne sont pas
implémentés ; soldes non espèces et éventuels remboursements manuels extérieurs
ne sont pas automatiquement vérifiables. Aucun test Windows/macOS ou base réelle.

## Crédit — premier circuit, 17 novembre 2026

Suite complète Linux avec Chromium headless : **156 tests réussis**, un avertissement
SQLAlchemy ; `pip check` et `git diff --check` réussis. Elle couvre le crédit avec
acompte espèces/Wave et règlements successifs, les liens caisse, l'idempotence,
le refus des trop-perçus et historiques non rapprochés, le plafond et sa confirmation,
le rollback, deux règlements concurrents sur SQLite fichier, la migration v13→v14
sur copie et un parcours navigateur. Après cette suite, la sélection explicite du
type de client a été ajoutée : 5 tests ciblés crédit et le parcours navigateur
crédit ont été relancés avec succès. Aucune base réelle, aucun Windows/macOS.
Les annulations de crédit, consignes, retours partiels, échéances et reçus ne sont
pas couverts ni implémentés ; le rapprochement historique reste à concevoir.

## Retours partiels et annulations de crédit — 17 novembre 2026

Suite complète sur Linux avec Chromium headless : **166 tests réussis**, un
avertissement SQLAlchemy ; `pip check` et `git diff --check` réussis. Tests sur
bases temporaires : annulation crédit sans acompte ou avec paiements mixtes et
règlement ultérieur, conservation des écritures, prévention de double annulation,
retours successifs, calcul exact, limites de quantité et de remboursement,
idempotence, échec atomique, migration v14→v15 et sauvegarde préalable. Les
parcours navigateur crédit/annulation et retour partiel ont réussi. Après la suite
complète, un affichage d'historique a été ajouté puis les deux parcours navigateur
et 35 tests ciblés ont été relancés avec succès.

Les consignes intégrées, l'annulation d'un retour et l'annulation totale après un
retour partiel ne sont pas prises en charge. Soldes non espèces et remboursements
manuels externes ne sont pas vérifiables automatiquement. Aucun test Windows/macOS
ni sur base commerciale réelle.

## Annulation de retour et annulation après retour partiel — 17 novembre 2026

Suite complète Linux, Python 3.11.2 et Chromium headless : **174 tests réussis** ;
un avertissement SQLAlchemy. `pip check` et `git diff --check` réussis. Essais sur
bases temporaires : migration v15→v16 avec sauvegarde et retour antérieur conservé,
contrepassation et idempotence, récupération des remboursements, coût moyen,
refus après mouvement de stock ultérieur, rollback sur erreur de caisse, nouveau
retour après contrepassation, annulation totale après retour partiel sans double
restitution ; deux parcours navigateur couvrent ces opérations.

Les consignes ne sont pas intégrées aux ventes, crédits ou retours. Les soldes
réels non espèces et remboursements manuels externes restent à vérifier par
l'opérateur. Aucun test ni migration d'une base commerciale, aucun Windows/macOS.

## Préparation des consignes — 17 novembre 2026

Suite complète Linux/Python 3.11.2 avec Chromium headless : **181 tests réussis**,
un avertissement SQLAlchemy ; `pip check` et `git diff --check` réussis. Tests sur
bases temporaires : migration v16→v17 avec sauvegarde et aucun rattachement
inventé, choix explicite sans/avec consigne, plusieurs composants et valeurs,
pièces fractionnaires ou valeurs inconnues refusées, archivage, rollback des
configurations invalides et blocage des ventes inconnues ou consignées sans
écriture de caisse ni de stock. Le navigateur couvre la configuration et le
blocage. Les ventes configurées sans consigne sont également exercées.

Les ventes consignées, comptes clients de vides, mouvements et remboursements
liés ne sont pas implémentés. Aucun test Windows/macOS ou de base commerciale.

### Consignes v18

Tests sur bases temporaires : vente comptant/crédit mixte, valeurs figées, retours partiels de vides, remboursement lié y compris après règlement ultérieur du crédit, échecs et rollback, concurrence et parcours navigateur. La migration v18 a été essayée sur copie synthétique avec sauvegarde préalable, pas sur une base commerciale. Les validations Linux et navigateur headless ne constituent pas des validations Windows/macOS.

Retours séparés : tests des deux ordres marchandise/vides, contreparties cumulées, puis annulation et nouvelle saisie d'un retour de marchandise. Le rapprochement historique manuel et la contrepassation des vides ne sont pas couverts car non implémentés.

Tableau de bord dynamique : tests sur base vide, création et désactivation de données, flux de caisse, vente à crédit puis annulation ; test navigateur de navigation, création d'un produit et actualisation. Les indicateurs commerciaux n'incluent pas les historiques non rapprochés.

### Moyens de paiement v19

Tests ciblés : création concurrente d'un même nom, refus de doublons, vente et remboursement après renommage, désactivation et réexécution idempotente ; interface navigateur et migration avec sauvegarde sur base synthétique. Suite Linux/Chromium : 201 réussites, un avertissement SQLAlchemy. Pas de validation Windows/macOS ou sur une base commerciale.

### Annulations de consignes v20

Tests des contreparties et du retour à nouveau, idempotence, concurrence, blocage sur mouvement de stock ultérieur et rollback après échec de caisse ; annulation de vente crédit mixte avec vides et stock initial obligatoire. Parcours navigateur vente consignée, retour et annulation de vides, puis annulation de vente ; 208 tests réussis sous Linux/Chromium. Migration sur base synthétique uniquement ; aucun essai sur base commerciale ou Windows/macOS.
