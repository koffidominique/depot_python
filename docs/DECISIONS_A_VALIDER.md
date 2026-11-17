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

- Crédit historique : définir une procédure de rapprochement des anciennes ventes,
  créances et soldes avant de permettre l'accès au nouveau circuit pour ces clients.
  Aucun solde ancien n'est supposé, et les rapports anciens ne sont pas fusionnés.
- Consignes et retours : définir pour chaque conditionnement la correspondance
  explicite avec les emballages, quantités, valeurs, propriété et règles de retour ;
  aucune règle ne doit être déduite du nom du produit ou du brasseur. Les règles
  de remboursement extérieur et de vérification des comptes non espèces restent
  à définir avec l'exploitant ; le logiciel ne peut confirmer seul les soldes réels.

### Consignes v18

Définir les procédures d'annulation d'une vente consignée, de retour de marchandise consignée et de contrepassation d'un retour de vides avant leur ouverture. Définir aussi le rapprochement éventuel des historiques et l'approvisionnement des vides ; aucune correspondance n'est supposée.

Décision utilisateur : les retours de marchandises et d'emballages sont séparés selon les éléments physiquement récupérés ; les anciens historiques doivent être rapprochés manuellement après confirmation explicite, sans inventer de correspondances. La fonctionnalité de rapprochement reste à développer.

Les moyens personnalisés sont traités comme non espèces. Un renommage crée une nouvelle version pour conserver le libellé d'origine ; les flux des versions sont distincts, sans regroupement automatique. Le code espèces conserve sa sémantique et ne peut être désactivé ou renommé.

Rapprochement historique : l'utilisateur souhaite une procédure de **reprise des soldes après contrôle**, justification et confirmation explicites, plutôt qu'un simple lien documentaire. La conception et l'implémentation restent à faire ; aucun solde n'est repris automatiquement et les anciens historiques restent séparés. Il faut préserver les écritures d'origine et éviter tout double comptage avant d'autoriser des opérations sur les soldes repris.
