# Décisions à valider

- Procédure de récupération locale après oubli du PIN : quelle preuve d'identité du
  propriétaire et quel moyen hors ligne sont acceptables ? À défaut, ne pas créer
  de déverrouillage par défaut ni prétendre vérifier l'identité.
- Le coût moyen interne est représenté exactement sous forme rationnelle sans
  arrondi. La valorisation totale fractionnaire est refusée conformément à la
  décision déjà prise. Son calcul lors des réceptions est implémenté lorsque le
  coût du stock précédent est connu ; sinon le coût reste indisponible.

Décision déjà prise : refuser les montants fractionnaires, y compris les montants
historiques ; ne pas les arrondir automatiquement. Quantités décimales seulement
lorsqu'elles sont autorisées et que le montant résultant est entier.

- Rapprochement des dettes et réceptions historiques : le lien ne peut pas être
  déduit fiablement. Elles restent en lecture seule pour les règlements du nouveau
  service jusqu'à une procédure de rapprochement explicite et vérifiée.
- Les remises et frais d'achat sont actuellement saisis par conditionnement, en
  FCFA entiers, et appliqués proportionnellement à chaque quantité reçue. Aucune
  répartition automatique d'un montant global n'est inventée. Le lien des
  règlements fournisseurs à la caisse reste à réaliser lors de la phase caisse ;
  les paiements existants portent le statut explicite « hors caisse ».

- Sous-dépôt : la compatibilité entre casiers, bouteilles et produits, les droits
  de propriété, les soldes initiaux et les valeurs de consigne doivent être
  confirmés par l'exploitant. Aucun coefficient ou circuit n'est déduit du nom
  d'un brasseur ou d'un format. Le catalogue d'emballages n'enregistre pas encore
  les mouvements physiques ni les dettes de consigne.
- Journal des vides : les mouvements sont actuellement des déclarations manuelles
  et ne déterminent ni la propriété ni le solde d'un client ou d'un fournisseur.
  Le rattachement transactionnel aux documents commerciaux et les règles de
  rapprochement des emballages restent à concevoir avant toute automatisation.
- Caisse fournisseurs : les anciens paiements hors caisse et anciennes sessions
  restent inchangés, sans rattachement rétroactif automatique. Une ancienne session
  ouverte bloque l'ouverture d'une nouvelle session ; sa procédure de rapprochement
  reste à définir. Les moyens non espèces affichent les sorties enregistrées, pas
  un solde bancaire ou Mobile Money. La saisie du fonds espèces est obligatoire.
- Les ventes au comptant introduites ici ne règlent pas les consignes : lorsqu'une
  consigne positive est connue sur le produit, la vente est bloquée. Le catalogue
  de vides n'étant pas encore relié aux produits, son existence ne permet pas de
  détecter toutes les consignes. La procédure complète reste à développer avant
  l'exploitation commerciale. Les anciens rapports ne comprennent pas ces ventes.
- Les flux non espèces de caisse sont affichés séparément sans supposer leurs
  soldes d'ouverture ; rapprochement des comptes, transferts, moyens configurables
  et clôture de chaque compte restent à concevoir.
