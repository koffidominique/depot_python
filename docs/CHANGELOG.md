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
