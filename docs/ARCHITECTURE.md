# Architecture DEPOTPRO — état et cible

## État au 17 novembre 2026

L'application NiceGUI utilise SQLAlchemy et une base SQLite locale (`WAL`, clés
étrangères activées sur les connexions SQLAlchemy). L'authentification propriétaire
utilise un PIN bcrypt à six chiffres ; l'état d'interface est associé au client.
Les anciens utilisateurs et leurs relations restent en base pour préserver l'histoire,
mais les écrans de gestion multi-rôles ne sont pas exposés. Le PIN ne chiffre pas
la base. Les anciens services et les nouveaux circuits coexistent : certains anciens
modules ne s'importent pas et les anciens flux commerciaux ne sont pas fiables ; voir
`AUDIT_TECHNIQUE.md` avant toute utilisation commerciale.

Au premier démarrage sur une base absente, le schéma est créé puis versionné. Une
base existante n'est pas créée ni migrée silencieusement : démarrage refusé si les
versions ne correspondent pas ou si les contrôles de schéma et d'intégrité échouent.
Ces contrôles couvrent les tables et colonnes des modèles, les clés étrangères et
certains index d'unicité critiques, mais pas toutes les contraintes SQL ni la
cohérence métier des données. Les migrations manuelles nécessitent l'arrêt de
l'application et une sauvegarde préalable ; la restauration et ses limites sont
expliquées dans `SAUVEGARDE_RESTAURATION.md`. Les images restent hors sauvegarde SQLite.

Les produits et conditionnements configurables, réceptions partielles, caisse et
ventes au comptant sont partiellement accessibles. Le catalogue d'emballages et le
journal manuel des vides ne sont pas reliés aux opérations commerciales. Les coûts
et conversions ne doivent pas être inventés. Les montants FCFA fractionnaires sont
refusés, y compris ceux issus de calculs ; les anciennes données ne sont pas converties.
La cartographie et les limites à jour sont dans `AUDIT_TECHNIQUE.md`.

## Cible

- Application desktop mono-propriétaire hors ligne Windows/macOS ; cycle de vie,
  fenêtre native, verrouillage d'instance et absence d'accès réseau à valider.
- Présentation séparée des services métier, transactions et intégrité cohérentes.
- Migrations et sauvegardes vérifiées, sans conversion implicite ni destruction de
  l'historique ; vérifications et restauration prudentes avant exploitation.
- Stock liquide et emballage, consignes, crédits, paiements et caisse reliés par
  écritures traçables, sans double comptabilisation ; rapports et PDF cohérents.
- Quantités et conversions explicites, montants FCFA entiers, paramètres commerciaux
  non documentés configurables ou soumis à décision.

L'ordre reste celui de `MAJ.md`. Les étapes antérieurement développées ne constituent
pas une validation globale. Les tests de fondations et les plateformes cibles doivent
être validés sans masquer les blocages avant de poursuivre.

## Reprise phase 2 — produits et échanges

La création et la modification de produits, l'enregistrement de conditionnements
et l'import CSV réservent l'écriture SQLite avant leurs vérifications métier. Cela
sérialise les contrôles de codes-barres entre ces parcours applicatifs, y compris
les conditionnements archivés. Depuis la migration 11, des déclencheurs SQLite empêchent également les collisions
inter-tables lors des insertions et modifications SQL directes ; les index uniques
propres à chaque table sont vérifiés au démarrage. Ils ne protègent pas contre une
modification volontaire du schéma SQLite. Les conditionnements restent modifiables ; les nouvelles ventes et commandes
conservent leurs instantanés, mais les modifications concurrentes de formulaires
n'ont pas de contrôle de version et les anciens circuits doivent encore être audités.

Depuis la migration 17, la vente exige que chaque conditionnement soit explicitement
déclaré sans consigne ou avec sa composition physique. Les conditionnements existants
ne sont pas automatiquement configurés ; une déclaration sans consigne doit être
vérifiée par l'exploitant. Les ventes avec consigne restent bloquées car les écritures
clients et les retours de vides ne sont pas encore intégrés.

Le CSV produit est un échange partiel (maximum 1 Mo et 1 000 lignes), pas une
sauvegarde : il ne contient notamment ni conditionnements, ni images, ni historique.
La prévisualisation et l'import refusent aussi un CSV à guillemets mal formés.
Les fichiers exportés contiennent des textes utilisateur sans neutralisation des
formules de tableur : ne pas ouvrir un CSV non fiable dans un tableur sans précaution.

## Prix de vente ajusté

Le parcours au comptant permet un prix unitaire ajusté explicite en FCFA entiers.
Le tarif configuré doit exister et rester inchangé entre aperçu et confirmation ;
le prix effectivement appliqué est figé sur la ligne de vente et dans son total.
La caisse, le stock et la vente sont validés ensemble. Le paiement mixte au
comptant permet plusieurs moyens distincts dont les montants totalisent exactement
la vente. Chaque mouvement de caisse possède un lien vers la vente via
`managed_sale_payments` ; les anciens paiements ne sont pas reconstruits. Le
premier mouvement utilise le type historique `sale`, les autres le type `income` ;
les liens permettent de les identifier comme paiements de vente. Le nouveau circuit de crédit et les retours restent partiels ; les
consignes restent à intégrer. Le parcours
complet ne doit pas être considéré prêt pour l'exploitation.

## Annulation totale et retours

`SaleCancellationService` annule intégralement les ventes du nouveau circuit au
comptant ou à crédit, avec confirmation de récupération complète. Il conserve
vente et paiements, rétablit le stock, annule la créance résiduelle et rembourse
chaque encaissement sur son moyen d'origine. La caisse doit être ouverte et les
espèces suffisantes. Après un retour partiel actif, cette procédure directe est
refusée pour éviter une double restitution : l'opérateur utilise le retour des
quantités restantes et demande explicitement l'annulation totale, avec extinction
de toute créance et remboursement des encaissements nets. Si toutes les quantités
ont déjà été retournées sans cette option, aucune commande de clôture seule n'existe.

`SaleReturnService` traite les marchandises récupérées en unités de base. Le
montant correspond à la fraction exacte du montant historique de ligne ; une
fraction de FCFA est refusée. L'opérateur répartit explicitement ce montant entre
réduction de créance et remboursements liés à des encaissements de la même vente.
Quantités déjà retournées, remboursements antérieurs, solde et montants sont
contrôlés sous verrou ; les écritures, stock et créance sont atomiques. Le coût
moyen de retour est calculé à partir du coût historique quand il est connu, sinon
il reste inconnu. Un retour peut être contrepassé après confirmation que les
marchandises repartent et que les remboursements ont été effectivement récupérés
sur leurs moyens d'origine. Cette opération rétablit la créance et les mouvements
de caisse sans effacer le retour. Elle est refusée si un mouvement de stock
ultérieur existe pour un produit concerné ou si la vente est déjà annulée ; le
coût est recalculé quand les informations sont suffisantes. L'annulation d'une
vente elle-même ne peut pas encore être annulée.

Les soldes réels des comptes non espèces et les remboursements manuels effectués
hors du parcours ne sont pas vérifiables automatiquement ; l'opérateur doit les
contrôler. Les consignes ne sont pas intégrées à ces opérations.

## Crédit — premier circuit séparé

Une nouvelle vente peut être partiellement payée, y compris avec plusieurs moyens,
ou sans acompte ; le reste positif est enregistré dans `managed_credit_sales`.
Un client et un choix explicite de plafond ou d'absence de plafond sont obligatoires ;
un dépassement exige une confirmation explicite. Les règlements successifs sont
idempotents, ne peuvent dépasser le solde et sont liés à des mouvements de caisse.
La vente, ses lignes, le stock, l'acompte et la créance sont transactionnels.
L'ancien solde et les anciennes créances ne sont pas recalculés ni fusionnés avec
les nouvelles ; les clients avec ventes ou dettes historiques ou solde ancien non
nul sont refusés, en attendant un rapprochement vérifié. L'interface ne crée pour
l'instant que de nouveaux clients avec profil crédit ; elle ne permet pas de
configurer les anciens clients. Le plafond du nouveau circuit est enregistré dans
son propre profil, pas dans le champ historique `clients.credit_limit`.

Ce circuit ne prend pas encore en charge les consignes, les échéances ni les reçus.
Les rapports historiques
ne comprennent pas ces créances. Une correction ou un remboursement manuel ne
met pas automatiquement à jour le crédit : ne pas l'utiliser comme contournement.
Les soldes réels non espèces ne sont pas connus du logiciel.

## Consignes — configuration préparatoire

`DepositPackagingProfile` distingue explicitement absence de consigne et
composition consignée. `DepositPackagingComponent` relie un conditionnement à
un ou plusieurs emballages physiques avec un nombre entier de pièces par
conditionnement. La valeur de chaque emballage doit être renseignée explicitement
dans le catalogue. Le calcul refuse les pièces fractionnaires et les montants
FCFA invalides. Aucune valeur, relation ou solde n'est créé à la migration.

Cette configuration n'est pas une intégration commerciale : les ventes de
conditionnements consignés sont volontairement refusées, sans mouvement de stock
ou caisse. Les écritures client, les échanges de vides, les retours, les
remboursements et les annulations de consigne restent à implémenter avant de
lever ce blocage. Une ancienne consigne positive sur le produit demeure également
bloquante, sans rapprochement automatique.

### Consignes du nouveau circuit (v18)

Les écritures client figent composants, quantités et valeurs à la vente. Les retours de vides rattachent un mouvement de stock physique distinct à la vente et aux éventuelles contreparties financières ; ils ne modifient pas le stock de liquide. Les remboursements référencent leurs encaissements. Aucun rapprochement automatique des anciens historiques ; les corrections de ventes consignées et les annulations de retours de vides restent indisponibles.

Les retours de marchandises consignées et de vides sont indépendants physiquement ; leurs réductions et remboursements actifs sont néanmoins cumulés dans le contrôle financier de la vente. L'annulation du retour de marchandise existante contre-passe uniquement ce retour. L'annulation totale d'une vente consignée et la contrepassation d'un retour de vides ne sont pas encore ouvertes.

### Moyens de paiement v19

Les opérations référencent le code immuable du catalogue local. Renommer un moyen désactive l'ancienne version et crée une nouvelle version avec un nouveau code : les libellés historiques et contreparties restent lisibles, mais les flux de l'ancienne et de la nouvelle version sont présentés séparément. Seul le code technique `cash` est considéré comme espèces ; les moyens créés sont non espèces. L'activation est vérifiée sous verrou pour les nouvelles écritures et non exigée pour les remboursements d'une ancienne transaction.

### Contrepassations de consignes v20

Une annulation de retour de vides conserve l'écriture initiale, référence une sortie de stock et les reprises de chaque remboursement, et rétablit la créance réduite. Elle refuse tout mouvement ultérieur sur ce stock. L'annulation totale d'une vente consignée exige la récupération explicite des produits et de tous les emballages, leur stock initial et l'absence de retours actifs ; elle conserve la vente et trace les entrées de vides par référence de contrepassation. Les retours actifs doivent d'abord être contrepassés ; la reprise d'anciens soldes n'est pas implémentée.
