# Historique

## Travail en cours — 17 novembre 2026

- Spécification du propriétaire conservée dans `MAJ.md`.
- Audit, cible d'architecture et décisions non tranchées documentés.
- Corrections préexistantes de la branche : FCFA entiers, tests, sauvegarde SQLite
  et restauration hors ligne ; ancienne migration dangereuse bloquée.
- L'application reste en cours de correction et ne doit pas être considérée livrée.
- Infrastructure de migration manuelle version 1 sur base existante : sauvegarde
  SQLite, contrôle d'intégrité, transaction et refus d'historique inconnu ; tests sur
  bases temporaires. Aucun changement sur les données commerciales.
- Phase 1 : configuration propriétaire, PIN bcrypt à six chiffres, temporisation,
  délai d'inactivité configurable, initialisation sans compte par défaut, migration
  manuelle des anciens PIN et restauration interversions explicite. Écrans métier
  historiques masqués temporairement. Compatibilité FastAPI/Starlette épinglée.
- Validation navigateur de l'authentification et de l'inactivité ; correction de
  l'erreur `ui.spacer` qui empêchait l'affichage après connexion. Test optionnel
  Chromium avec réseau externe bloqué pour ce parcours.
- Phase 2 en cours : migration 3, conditionnements configurables, validations,
  stock initial traçable, liste produits, filtres, création/modification/archivage,
  aperçu et import/export CSV ; ajout de tests métier et navigateur. Achats et
  ventes ne sont pas encore raccordés.
- Phase 2 : pagination et filtres SQL, images locales validées, déclaration
  explicite d'unité historique sans conversion, stockage rationnel exact et
  migration 4. Le coût pondéré à la réception reste en phase 3.

### Phase 3 — en cours, non livrée
- Structures de réception et inventaire et migration 5 préparées ; migration testée sur bases SQLite de test ; aucune base commerciale réelle migrée.
- Service de commandes/réceptions en cours : conditionnement figé à la commande, réceptions partielles transactionnelles avec clé de déduplication, mouvements de stock et coût moyen rationnel lorsque le coût du stock initial est connu (sinon coût inconnu). Refus des fractions de FCFA.
- Inventaires et corrections de stock tracées, consultations et alertes dans l’interface ; validation atomique, comptages complets, motifs et rejet si le stock a bougé. Une entrée sans coût fiable rend le coût moyen indisponible.
- Interface approvisionnements : création fournisseur et commande multiligne, validation, réceptions partielles et dettes liées à chaque réception, échéances, historique et règlements idempotents hors caisse. Remises et frais explicites par conditionnement. Migration 6 sans conversion des données historiques.
- Réserve majeure : les règlements fournisseurs sont tracés hors caisse, sans mouvement de caisse automatique ; rapprochement et caisse restent à sécuriser aux phases suivantes. Les dettes historiques non rapprochées sont en lecture seule. Pas de mise en production.

### Sous-dépôt — premier incrément : catalogue des emballages physiques
- Nouvelle table et migration 7 additives avec sauvegarde préalable ; aucun
  conditionnement, montant ou compatibilité déduit des données historiques.
- Interface de création et archivage de bouteilles/casiers, avec circuit déclaré
  et valeur de consigne facultative ; archivage non destructif.
- Aucun mouvement de vides, solde client, panachage, rapprochement ou intégration
  achats/ventes n'est créé à ce stade ; ce catalogue ne constitue pas un système
  opérationnel de consignes. Les fonctionnalités suivantes nécessitent leur propre
  conception transactionnelle et des tests, conformément aux phases de MAJ.md.

### Sous-dépôt — deuxième incrément : journal manuel des vides
- Déclaration explicite du stock initial de pièces vides et journal séparé des
  boissons : entrées, sorties, casse, perte et corrections motivées, avec document
  facultatif, soldes avant/après et clés de déduplication côté service.
- Quantités entières, stock négatif refusé et archivage empêché tant que le solde
  déclaré n'est pas nul. Migration 8 additive avec sauvegarde vérifiée.
- Les achats, ventes et retours ne mettent pas encore ce stock à jour ; il n'y a
  pas de compte d'emballages clients, de consigne financière, de compatibilité ou
  de rapprochement automatique. Ne pas présenter le journal manuel comme un stock
  complet ni comme une preuve de propriété.

### Règlements fournisseurs et caisse — premier périmètre
- Ouverture d'une session unique, fonds initial explicite en espèces, règlement
  fournisseur et mouvement lié dans la même transaction, déduplication, contrôle
  du solde espèces, séparation des décaissements par moyen, clôture et écart.
- Les paiements historiques hors caisse ne sont pas modifiés ni automatiquement
  rattachés ; une session de caisse historique encore ouverte bloque l'ouverture.
- La caisse ne traite pas encore ventes, dépenses, recettes diverses, avances,
  compte financier complet des moyens non espèces ou contrepassations. Son solde
  théorique ne reflète que les opérations intégrées. Usage de production interdit
  tant que la caisse complète et les rapprochements ne sont pas achevés.

### Caisse et ventes — extension partielle
- La caisse accepte désormais les dépenses payées, autres recettes et sorties et
  corrections motivées, avec montants FCFA entiers et mouvements par moyen ; seuls
  les flux, pas les soldes des comptes non espèces, sont calculés.
- Nouveau parcours de vente au comptant intégral : panier, tarifs et conversions
  configurés, aperçu du total, déduction du stock et encaissement atomiques,
  instantané du conditionnement et du coût disponible, déduplication ; les produits
  dont une consigne positive est explicitement renseignée sont refusés.
- Périmètre volontairement incomplet : pas de crédit, paiements mixtes, consignes,
  remboursements, annulations, transfert entre moyens, rapprochement historique,
  ni lien aux anciens rapports ou PDF. Les moyens non espèces ne sont pas soldés.
  Les écritures manuelles ne doivent pas reproduire un paiement déjà enregistré.
  Ne pas utiliser en production avant réalisation et validation de ces fonctions.

### Audit actualisé — reprise phase 0
- Diagnostic réécrit dans `docs/AUDIT_TECHNIQUE.md` pour refléter les modules
  actifs, les historiques parallèles, les risques actuels et les étapes suivantes.
- Vérifications Linux : 110 tests réussis, 7 tests navigateur ignorés ; deux imports
  historiques en échec. Aucune base commerciale inspectée ou migrée.

## Reprise phase 1 — 17 novembre 2026

- Changement du PIN : vérification de l'ancien PIN et écriture sous un même verrou
  transactionnel ; les tentatives incorrectes restent enregistrées.
- Démarrage : contrôle en lecture seule de l'intégrité, des clés étrangères, des
  tables/colonnes des modèles et de certaines unicités critiques, sans réparation
  implicite d'une base existante ; vérification également après première création.
- Architecture actualisée et tests de concurrence et de refus non destructif.
  Voir `TESTS.md` pour les limites de la validation actuelle.
- Validation navigateur Linux relancée : suite complète 121 tests réussis, puis
  tests ciblés supplémentaires pour le schéma migré et l'index de caisse incorrect.

## Reprise phase 2 — 17 novembre 2026

- Sérialisation des contrôles et écritures produits, conditionnements et import
  CSV sous verrou SQLite ; aucun changement de schéma ni migration de base réelle.
- CSV mal formé refusé ; avertissement d'interface sur le caractère partiel de
  l'échange CSV et correction d'un texte de présentation devenu obsolète.
- Tests de concurrence, d'échec sans perte des modifications en attente, des cinq
  types de conditionnement et des conflits CSV. Limites dans `ARCHITECTURE.md`.

## Prix ajusté et migration 11 — 17 novembre 2026

- Protection SQLite inter-tables des codes-barres avec refus non destructif des
  collisions préexistantes, sauvegarde et vérification des protections au démarrage.
- Prix unitaire ajustable explicitement dans les ventes au comptant, tarif source
  vérifié à la confirmation, prix réellement appliqué conservé dans l'historique.
- Tests SQLite directs, migration, stock/caisse et parcours navigateur ; les autres
  fonctionnalités commerciales et les validations cibles restent incomplètes.

## Paiements mixtes au comptant — 17 novembre 2026

- Paiement intégral réparti sur plusieurs moyens distincts, montants FCFA entiers
  positifs, caisse et stock atomiques, total exact et liens aux mouvements.
- Migration 12 avec sauvegarde sur copie, sans recréer les liens historiques.
- Parcours d'interface et tests ; crédit, consignes et annulations non achevés.

## Annulation totale au comptant — 17 novembre 2026

- Migration 13 : tables d'annulation et liens entre remboursement et encaissement,
  sans réinterprétation des historiques.
- Annulation complète des nouvelles ventes au comptant, y compris paiement mixte :
  confirmation de récupération totale, stock et remboursements atomiques, calcul
  du coût moyen si connu, traçabilité et affichage du statut ; pas de retour partiel.
- Les ventes à crédit et les consignes intégrées restent à développer et ne sont
  pas couvertes par cette procédure. Aucun traitement sur une base réelle.

## Crédit — premier circuit, 17 novembre 2026

- Migration 14 et profils explicites pour nouveaux clients, créances et règlements
  transactionnels ; aucun rapprochement historique automatique.
- Vente à crédit avec acompte éventuellement mixte, plafond et confirmation de
  dépassement, règlements idempotents et liens aux mouvements de caisse.
- Tests métier, concurrence, migration sur copie et navigateur. Crédit encore
  partiel : pas de consignes, retours ni annulations de crédit ; voir `TESTS.md`.

## Retours partiels et annulations de crédit — 17 novembre 2026

- Annulation totale des ventes à crédit, remboursements liés aux encaissements,
  créance résiduelle annulée et stock restauré ; aucune trace initiale supprimée.
- Migration 15 et retours partiels en unités de base avec réduction explicite de
  créance et remboursements par encaissement ; contrôle des quantités, soldes,
  idempotence et atomicité. L'annulation totale après retour est interdite.
- Parcours UI et tests. Consignes intégrées et annulation d'un retour restent à
  développer ; pas de migration sur base commerciale réelle.

## Contrepassation des retours — 17 novembre 2026

- Migration 16, annulation idempotente d'un retour avec confirmation explicite,
  rétablissement de la créance et reprises de remboursement tracées ; refus en
  présence de mouvements ultérieurs de stock pour les produits concernés.
- Annulation totale après retour partiel via retour des quantités restantes et
  extinction explicite des contreparties, sans double restitution de stock.
- Tests métier, migration sur copie et navigateur. Les consignes restent à intégrer.

## Préparation des consignes — 17 novembre 2026

- Migration 17, composition explicite des emballages par conditionnement,
  quantités entières et valeurs obligatoires ; aucune configuration déduite.
- Refus des ventes à consigne inconnue ou effectivement consignée. Ces dernières
  restent bloquées tant que les écritures physiques et financières ne sont pas
  intégrées ; ce n'est pas une fonctionnalité de vente consignée terminée.
- Tests et navigateur sur bases temporaires, aucune migration commerciale réelle.

## Version 18 — consignes clients

Les ventes consignées du nouveau circuit exigent un client actif et un aperçu de consigne confirmé ; valeur et composants sont figés. Le retour de vides associe réception physique, stock distinct, réduction explicite de créance et/ou remboursements liés aux encaissements, dans une transaction. Un stock initial de vides doit être déclaré. Les règlements ultérieurs du crédit sont aussi pris en compte. Annulation de vente consignée, retour de marchandise consignée et annulation de retour de vides restent bloqués ou indisponibles ; les historiques anciens ne sont pas rapprochés automatiquement. Les descriptions précédentes de limitations des versions antérieures ne décrivent pas ce nouveau circuit.

### Retours séparés de marchandises consignées

Le nouveau circuit accepte désormais un retour de marchandise même si la vente comprend des consignes. Les vides restent à retourner séparément ; les contreparties des deux types de retour sont cumulées pour éviter les doubles remboursements. L'annulation totale d'une vente consignée et la contrepassation d'un retour de vides restent bloquées. Le rapprochement historique manuel confirmé reste à développer.

### Tableau de bord local dynamique

Remplacement de l'écran d'attente par des indicateurs lus dans SQLite : produits et clients actifs, seuils de stock définis, nombre de ventes non annulées et créances restantes du nouveau circuit, caisse ouverte et espèces théoriques. Actualisation manuelle ou en revenant sur la page. Les historiques commerciaux non rapprochés sont exclus des indicateurs du nouveau circuit ; les espèces affichées ne sont pas un comptage physique. Aucune donnée de démonstration n'est créée et aucune migration n'est nécessaire.

## Version 19 — moyens de paiement configurables

Depuis les paramètres, création, changement de libellé et désactivation des moyens non espèces. L'ancien libellé et identifiant sont conservés pour les écritures précédentes ; les saisies nouvelles utilisent la nouvelle version. La caisse espèces reste un moyen technique immuable, nécessaire au calcul du solde. Les remboursements des anciennes opérations restent possibles après désactivation. Les autres listes métier ne sont pas toutes configurables ; les annulations de consignes et le rapprochement historique manuel restent à développer.

## Version 20 — annulations de consignes

Un retour de vides peut être annulé après confirmation de leur restitution au client et de la récupération des remboursements : sortie de stock, rétablissement de créance et reprises de remboursement liées sont atomiques et tracés. Un mouvement ultérieur sur le stock de l'emballage bloque l'opération. Une vente consignée peut être annulée totalement après confirmation de récupération de tous les produits et vides, avec réintégrations et remboursements liés ; les stocks initiaux de vides sont requis. Un retour actif de marchandise ou de vides bloque l'annulation totale : contrepasser d'abord ces retours lorsque possible. Les descriptions de blocage générales des sections précédentes sont historiques. Le rapprochement des anciens soldes reste à développer.
