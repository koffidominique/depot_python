# MASTER PROMPT — DEPOTPRO

Spécification fonctionnelle, technique et instructions d'implémentation intégrale

**PROJET :** DEPOTPRO — Logiciel professionnel de gestion de dépôt de boissons
**DÉPÔT GITHUB :** https://github.com/koffidominique/depot_python.git
**ENVIRONNEMENT CIBLE :** Windows et macOS
**LANGUE DE L'APPLICATION :** Français
**DEVISE :** FCFA (XOF)
**UTILISATEUR :** Un seul utilisateur, propriétaire du dépôt
**MODE DE FONCTIONNEMENT :** Application de bureau autonome, utilisable sans connexion Internet.

## 1. TON RÔLE ET TA MISSION

Tu es un ingénieur logiciel senior, architecte Python, expert en applications de gestion commerciale, ERP de distribution, gestion des stocks, comptabilité commerciale, bases de données SQLite et développement d'applications desktop.

Tu es chargé de transformer le dépôt GitHub DEPOTPRO existant en une application de bureau professionnelle, stable, ergonomique, sécurisée et prête pour une utilisation quotidienne dans un dépôt de boissons.

Tu dois travailler directement dans le code source existant.

**Ta mission n'est pas de produire uniquement un cahier des charges, une maquette ou des recommandations. Tu dois réellement auditer, modifier, développer, intégrer, tester et documenter l'application.**

Tu dois respecter intégralement les besoins décrits dans ce document.

Tu es responsable de la cohérence fonctionnelle et technique de l'ensemble du logiciel.

### Résultat final attendu

Construire DEPOTPRO Desktop, une application premium qui permet à son propriétaire de gérer :

- Les produits et les catégories.
- Les conditionnements et leurs conversions.
- Les prix d'achat et les tarifs de vente.
- Les approvisionnements.
- Les stocks et les inventaires.
- Les ventes en gros et au détail.
- Les clients.
- Les ventes à crédit.
- Les règlements et remboursements.
- Les fournisseurs et leurs dettes.
- La caisse.
- Les dépenses.
- Les rapports commerciaux et financiers.
- Les sauvegardes et les restaurations.
- Les paramètres et la sécurité.

Le logiciel doit être simple à utiliser, même pour une personne qui ne maîtrise pas l'informatique.

## 2. CONTEXTE COMMERCIAL À RESPECTER IMPÉRATIVEMENT

Voici le fonctionnement commercial confirmé du dépôt.

### 2.1 Types de vente

Le dépôt pratique les deux types de vente :

- Vente en gros.
- Vente au détail.

Ces deux modes doivent être disponibles dans le logiciel.

La vente en gros et la vente au détail peuvent utiliser les tarifs configurés pour chaque produit.

Le système doit pouvoir gérer plusieurs niveaux tarifaires :

- Prix de gros.
- Prix de détail.
- Prix intermédiaire ou semi-gros, facultatif et configurable.

Ne suppose jamais qu'un tarif est identique pour tous les produits.

### 2.2 Conditionnements commerciaux

Les unités utilisées dans le dépôt sont :

1. Casier.
2. Carton.
3. Bouteille.
4. Pack.
5. Canette.

Ces conditionnements doivent être gérés individuellement pour chaque produit.

Un produit peut utiliser certains conditionnements sans être obligé d'utiliser les cinq.

### 2.3 Ventes à crédit

Les ventes à crédit sont autorisées.

Le logiciel doit enregistrer les ventes totalement payées, partiellement payées et non payées.

Il doit gérer les créances clients et permettre plusieurs remboursements pour une même dette.

Le montant effectivement encaissé doit toujours être distinct du chiffre d'affaires réalisé.

### 2.4 Environnement commercial

- Une seule personne utilise le logiciel.
- Un seul dépôt physique.
- Une seule base de données locale.
- Une seule devise : FCFA.
- Aucun abonnement mensuel.
- Aucune authentification cloud.
- Aucune dépendance à Internet.
- Aucune gestion de plusieurs utilisateurs ou de rôles.

Ne développe aucune fonctionnalité multi-utilisateur sans nécessité technique réelle.

## 3. RÈGLES ABSOLUES DE DÉVELOPPEMENT

Ces règles sont obligatoires pendant toutes les phases du projet.

### Règle 1 — Examiner avant de modifier

Avant toute modification :

- Parcours l'ensemble du dépôt.
- Examine les fichiers Python.
- Examine les modèles SQLAlchemy.
- Examine tous les services métier.
- Examine toutes les pages NiceGUI.
- Examine les composants réutilisables.
- Examine les dépendances.
- Examine la configuration de la base de données.
- Examine les scripts d'initialisation.
- Examine les fonctionnalités déjà implémentées.

Identifie les fonctions existantes, les fonctions incomplètes, les fonctions cassées et les doublons.

Ne suppose jamais qu'une fonctionnalité décrite dans le README fonctionne réellement.

### Règle 2 — Ne pas reconstruire inutilement

Conserve les parties du projet qui sont fonctionnelles et adaptées au besoin.

Refactorise celles qui sont mal conçues.

Remplace celles qui sont incompatibles avec la nouvelle architecture.

Supprime uniquement les fonctionnalités devenues inutiles après avoir vérifié leurs dépendances et leurs éventuelles données historiques.

### Règle 3 — Préserver les données

Ne supprime jamais la base de données existante.

Ne réinitialise jamais automatiquement les données commerciales.

Ne détruis jamais les historiques de ventes, de paiements, de stocks, de clients ou de fournisseurs.

Avant toute migration :

1. Identifier la base utilisée.
2. Créer une sauvegarde vérifiée.
3. Préparer une migration versionnée.
4. Exécuter la migration.
5. Vérifier l'intégrité des données.
6. Documenter le résultat.

### Règle 4 — Ne jamais inventer des données commerciales

Tu ne dois jamais inventer :

- Les conversions des conditionnements.
- Les tarifs des produits.
- Les prix d'achat.
- Les stocks initiaux.
- Les plafonds de crédit.
- Les montants des ventes.
- Les paramètres fiscaux.

Toutes ces valeurs doivent être configurables ou saisies par l'utilisateur.

### Règle 5 — Développer des fonctionnalités réellement opérationnelles

Un bouton doit effectuer son action.

Un formulaire doit enregistrer ses données.

Un tableau doit afficher les informations réelles de la base.

Un indicateur doit correspondre à un calcul métier vérifiable.

Aucune page ne doit contenir de données fictives en production.

Aucun bouton décoratif ne doit être présenté comme une fonctionnalité terminée.

### Règle 6 — Travailler par étapes

Respecte l'ordre de développement défini dans ce document.

Après chaque phase :

- Exécute les tests concernés.
- Corrige les erreurs.
- Vérifie les effets sur les autres modules.
- Mets à jour la documentation.
- Fais un compte rendu de validation.

Ne passe pas à une phase suivante si la phase précédente contient une anomalie bloquante.

Ne t'arrête pas après avoir produit un plan : exécute les phases successivement sans demander une confirmation entre chaque phase, sauf blocage réel ou décision commerciale indispensable.

## 4. ARCHITECTURE TECHNIQUE CIBLE

Tu dois privilégier une architecture Python modulaire, maintenable et évolutive.

### 4.1 Technologies principales

Technologies à conserver ou à utiliser après vérification de leur compatibilité :

- Python.
- NiceGUI pour l'interface.
- PyWebView pour l'ouverture dans une fenêtre native.
- SQLAlchemy pour la gestion des données.
- SQLite pour la base de données locale.
- bcrypt pour le hachage du PIN.
- ReportLab pour la génération de PDF.
- PyInstaller pour les exécutables.
- pytest pour les tests automatisés.

Vérifie les versions de dépendances et leurs compatibilités avec les versions de Python et les systèmes d'exploitation ciblés.

Ne conserve pas aveuglément des versions anciennes si elles présentent des problèmes de sécurité, de maintenance ou de compatibilité.

Ne réalise aucune mise à jour majeure sans vérifier les changements d'API et les impacts sur le projet.

### 4.2 Organisation logique souhaitée

L'application doit séparer clairement :

**Interface :**

- Pages.
- Composants.
- Formulaires.
- Tables.
- Navigation.
- Dialogues.
- Notifications.

**Services métier :**

- ProductService.
- PackagingService.
- StockService.
- PurchaseService.
- SalesService.
- ClientService.
- SupplierService.
- PaymentService.
- DebtService.
- CashService.
- ExpenseService.
- ReportService.
- BackupService.
- AuthService.

**Données :**

- Modèles SQLAlchemy.
- Configuration SQLite.
- Contraintes de données.
- Index.
- Migrations.

**Infrastructure :**

- Démarrage desktop.
- Journalisation.
- Sauvegarde.
- Restauration.
- Génération de PDF.
- Export.
- Packaging de l'application.

Les pages graphiques ne doivent pas contenir directement les calculs métier ou les règles de gestion complexes.

Toute opération importante doit passer par un service dédié.

### 4.3 Base de données

Conserver SQLite pour le fonctionnement mono-utilisateur.

Configurer correctement :

- Les clés étrangères.
- Les transactions.
- Les index.
- Le mode WAL si adapté.
- Le délai d'attente en cas de verrouillage.
- Les contraintes de cohérence.
- Les migrations versionnées.

Utiliser Decimal ou Numeric pour les montants financiers.

Éviter les calculs monétaires en nombres flottants binaires.

Toutes les sommes financières doivent être calculées avec une précision maîtrisée et arrondies selon une règle cohérente.

Les quantités de stock doivent être exprimées dans une unité de base et utiliser une précision adaptée aux unités du dépôt.

## 5. MODULE 1 — AUTHENTIFICATION ET PREMIER DÉMARRAGE

Construire une authentification très simple.

### 5.1 Premier lancement

Au premier démarrage, si aucun PIN n'est configuré :

- Afficher un assistant de première utilisation.
- Demander la création d'un PIN de six chiffres.
- Demander sa confirmation.
- Vérifier que les deux saisies correspondent.
- Enregistrer uniquement le hash du PIN.
- Ouvrir l'application après validation.

Ne jamais afficher un PIN par défaut.

Ne jamais conserver un PIN en clair dans la base de données ou les journaux.

### 5.2 Connexion

Créer un écran de connexion avec :

- Logo DEPOTPRO.
- Nom de l'application.
- Six emplacements de saisie.
- Clavier numérique.
- Bouton d'effacement.
- Validation automatique à six chiffres.
- Message d'erreur discret.
- Protection contre les tentatives répétées.

### 5.3 Sécurité

Utiliser bcrypt avec un sel approprié.

Ajouter une limitation des tentatives incorrectes et une temporisation progressive.

Prévoir le verrouillage automatique après une période d'inactivité configurable.

Ne jamais prétendre que le PIN chiffre le fichier SQLite.

Proposer une procédure documentée de récupération locale en cas de PIN oublié, après sauvegarde et vérification de l'identité du propriétaire selon une procédure locale définie.

### 5.4 Paramètres avancés

Permettre :

- La modification du PIN.
- La confirmation du nouveau PIN.
- Le paramétrage du verrouillage automatique.
- La configuration des sauvegardes.
- L'accès aux informations de l'application.

Supprimer de l'interface les fonctions de gestion des utilisateurs, des rôles et des permissions multiples.

Pour les anciennes installations, traiter les PIN historiques en clair comme des données à migrer : ne pas maintenir les identifiants par défaut. Exiger la configuration d'un nouveau PIN sécurisé.

## 6. MODULE 2 — TABLEAU DE BORD

Créer un tableau de bord professionnel, sobre et immédiatement compréhensible.

Le tableau de bord est l'écran principal après connexion.

Il doit afficher des chiffres réels provenant de la base de données.

### 6.1 Indicateurs

Afficher :

- Chiffre d'affaires du jour.
- Encaissements du jour.
- Ventes à crédit du jour.
- Créances clients restantes.
- Dépenses du jour.
- Achats du jour.
- Valeur du stock.
- Nombre de produits.
- Produits en stock faible.
- Produits en rupture.

Afficher également une synthèse de la période sélectionnée.

### 6.2 Graphiques

Ajouter si cela améliore réellement la compréhension :

- Évolution des ventes.
- Évolution des encaissements.
- Répartition des ventes par catégorie.
- Produits les plus vendus.
- Évolution des dépenses.

### 6.3 Actions rapides

Prévoir :

- Nouvelle vente.
- Nouvel approvisionnement.
- Nouveau produit.
- Nouveau client.
- Encaisser une dette.
- Ajouter une dépense.
- Effectuer un inventaire.

Tous les indicateurs doivent être filtrables par période lorsque cela est pertinent.

Ne jamais afficher un bénéfice estimé sans connaître correctement le coût des marchandises vendues.

## 7. MODULE 3 — PRODUITS ET CONDITIONNEMENTS

C'est une fonctionnalité centrale du projet.

### 7.1 Gestion des produits

Chaque produit doit disposer des informations suivantes :

- Identifiant unique.
- Référence automatique.
- Code-barres facultatif.
- Nom.
- Marque.
- Catégorie.
- Description facultative.
- Fournisseur habituel facultatif.
- Unité de base.
- Prix d'achat de référence.
- Prix de gros.
- Prix de détail.
- Prix intermédiaire facultatif.
- Coût moyen d'achat.
- Stock disponible.
- Seuil d'alerte.
- Statut actif ou archivé.
- Image facultative.

Pouvoir créer, modifier, rechercher, archiver et consulter une fiche produit.

Ne pas supprimer définitivement un produit qui possède un historique commercial.

### 7.2 Unité de base

Chaque produit doit posséder une unité de base de stock.

Cette unité est généralement :

- Bouteille.
- Canette.
- Autre unité simple appropriée.

Le stock théorique est conservé dans cette unité de base.

Une vente en carton, pack ou casier doit être convertie automatiquement en quantité de base.

### 7.3 Gestion des cinq conditionnements

Mettre à disposition les conditionnements suivants :

- Casier.
- Carton.
- Bouteille.
- Pack.
- Canette.

Tous ne sont pas obligatoires pour chaque produit.

Créer un modèle ProductPackaging qui contient au minimum :

- Produit associé.
- Nom du conditionnement.
- Unité de base correspondante.
- Coefficient de conversion.
- Prix d'achat facultatif.
- Prix de gros.
- Prix de détail.
- Tarif intermédiaire facultatif.
- Code-barres facultatif.
- Statut actif.

Le coefficient de conversion doit être propre à chaque produit.

Exemple purement illustratif :

1 carton = 12 bouteilles.

1 casier = 24 bouteilles.

1 pack = 6 bouteilles.

Ces chiffres sont des exemples et ne doivent jamais devenir des valeurs commerciales imposées.

L'utilisateur doit pouvoir renseigner les véritables équivalences de son dépôt.

Vérifier que les coefficients sont strictement positifs et cohérents.

Par défaut, les quantités vendues et achetées doivent être des nombres entiers de conditionnements. N'autoriser les fractions que pour les unités qui le permettent explicitement.

### 7.4 Tarification

Chaque conditionnement peut posséder ses propres prix.

Par exemple :

- Prix d'un carton.
- Prix d'un pack.
- Prix d'un casier.
- Prix d'une bouteille.
- Prix d'une canette.

Les tarifs doivent être indépendants lorsque nécessaire.

Le logiciel doit proposer automatiquement le prix correspondant au mode de vente et au conditionnement.

L'utilisateur doit pouvoir ajuster le prix au moment de la vente.

Le logiciel doit conserver le prix réellement appliqué dans l'historique.

### 7.5 Import et export

Permettre :

- L'export CSV de la liste des produits.
- L'import CSV avec prévisualisation.
- La détection des références en doublon.
- Le contrôle des champs obligatoires.
- Le refus des lignes invalides sans altérer les données déjà enregistrées.

## 8. MODULE 4 — APPROVISIONNEMENTS

Développer une gestion complète des achats et des réceptions.

### 8.1 Création d'un approvisionnement

Permettre de renseigner :

- Fournisseur.
- Date.
- Référence.
- Produits.
- Conditionnements.
- Quantités commandées.
- Prix d'achat.
- Remises éventuelles.
- Frais complémentaires facultatifs.
- Total.
- Montant réglé.
- Reste à payer.
- Notes.

### 8.2 Réception

Prévoir :

- Commande en brouillon.
- Commande validée.
- Réception partielle.
- Réception complète.
- Commande annulée.

Une commande non réceptionnée ne doit jamais modifier le stock disponible.

Une réception partielle doit augmenter le stock de la seule quantité effectivement reçue.

Les réceptions doivent produire des mouvements de stock détaillés et traçables.

Empêcher la réception d'une quantité supérieure au solde commandé, sauf procédure explicite d'ajustement.

### 8.3 Dettes fournisseurs

Permettre de suivre :

- Total des achats.
- Total payé.
- Montant restant.
- Historique des règlements.
- Échéances facultatives.
- Solde par fournisseur.

Les paiements fournisseurs doivent être liés aux dettes ou factures correspondantes et ne pas être comptabilisés deux fois.

## 9. MODULE 5 — STOCKS ET INVENTAIRES

### 9.1 Stock centralisé

Le stock de chaque produit est toujours exprimé dans son unité de base.

Toute entrée ou sortie doit produire un mouvement de stock.

Types de mouvements à gérer :

- Stock initial.
- Réception d'achat.
- Vente.
- Retour client.
- Retour fournisseur.
- Casse.
- Perte.
- Correction.
- Régularisation d'inventaire.

Ne jamais modifier silencieusement le stock sans créer un mouvement correspondant.

### 9.2 Historique

Chaque mouvement doit contenir :

- Produit.
- Date et heure.
- Type de mouvement.
- Quantité positive ou négative.
- Unité.
- Stock avant.
- Stock après.
- Référence du document.
- Motif lorsque nécessaire.

Conserver un journal historique non destructif.

### 9.3 Alertes

Prévoir :

- Stock faible.
- Rupture.
- Produits inactifs.
- Quantités incohérentes.

### 9.4 Inventaire physique

Permettre de :

1. Démarrer un inventaire.
2. Afficher le stock théorique.
3. Saisir le stock réel.
4. Calculer l'écart.
5. Ajouter un motif.
6. Afficher un résumé.
7. Valider la régularisation.

La validation doit créer les mouvements de correction correspondants.

### 9.5 Valorisation

Calculer la valeur du stock en utilisant le coût moyen pondéré lorsque les données le permettent.

Ne pas confondre :

- Valeur du stock.
- Prix de vente potentiel.
- Chiffre d'affaires.
- Bénéfice.

## 10. MODULE 6 — VENTES EN GROS ET AU DÉTAIL

Créer un écran Nouvelle vente ergonomique, rapide et complet.

### 10.1 Modes de vente

Proposer deux modes :

- Vente en gros.
- Vente au détail.

Le mode sélectionné influence le tarif proposé.

Il ne doit pas interdire un conditionnement valide pour un produit.

### 10.2 Création d'une vente

Champs :

- Référence automatique.
- Date et heure.
- Client.
- Mode de vente.
- Produits.
- Conditionnements.
- Quantités.
- Prix unitaires.
- Remises.
- Total par ligne.
- Total général.
- Montant payé.
- Reste à payer.
- Moyen de paiement.
- Commentaire.

Permettre l'ajout et le retrait de produits dans un panier.

Prévoir une recherche rapide par nom, référence ou code-barres.

### 10.3 Calculs

Pour chaque ligne :

Quantité en stock de base = quantité vendue × coefficient de conversion.

Total ligne = quantité vendue × prix unitaire du conditionnement − remise.

Total vente = somme des lignes, après remises et ajustements applicables.

Reste à payer = total vente − paiements valides.

Empêcher :

- Quantité nulle ou négative.
- Prix négatif.
- Remise supérieure au montant autorisé.
- Dépassement du stock disponible.
- Paiement supérieur au solde restant, sauf traitement explicite d'un trop-perçu.

### 10.4 Validation

Lorsqu'une vente est validée :

1. Vérifier les produits.
2. Vérifier le stock.
3. Vérifier les prix et les quantités.
4. Créer la vente.
5. Enregistrer les lignes.
6. Déduire le stock.
7. Enregistrer les paiements reçus.
8. Créer la créance éventuelle.
9. Enregistrer les mouvements de caisse des paiements encaissés.
10. Générer la référence et le document commercial.

Toutes ces opérations doivent être réalisées dans une transaction atomique.

Une erreur ne doit jamais laisser une vente partiellement enregistrée.

### 10.5 Documents

Générer :

- Facture.
- Reçu de paiement.
- État de vente.
- Historique de vente.

Prévoir une présentation PDF imprimable au format A4 et un format reçu compact configurable.

Les informations commerciales du dépôt doivent être configurables avant impression.

### 10.6 Retours et annulations

Prévoir une procédure de retour partiel ou total.

Un retour doit :

- Être rattaché à une vente existante.
- Identifier les quantités retournées.
- Vérifier qu'elles n'ont pas déjà été retournées.
- Restaurer le stock réellement récupéré.
- Enregistrer le remboursement éventuel.
- Corriger les montants dus.
- Garder l'historique initial.

Ne jamais supprimer une vente validée pour corriger une erreur.

Préférer des opérations d'annulation, de remboursement et de contrepassation traçables.

## 11. MODULE 7 — CLIENTS ET CRÉANCES

Les ventes à crédit sont obligatoires dans le périmètre.

### 11.1 Fiche client

Informations :

- Code client.
- Nom.
- Type : particulier ou professionnel.
- Téléphone.
- Adresse.
- Ville.
- Contact facultatif.
- Plafond de crédit facultatif.
- Solde dû.
- Date de création.
- Statut.

Autoriser les ventes au comptoir sans créer systématiquement une fiche client.

Une vente à crédit doit obligatoirement être rattachée à un client identifié.

### 11.2 Créances

À chaque vente partiellement payée ou non payée :

- Créer la créance correspondante.
- Enregistrer le montant initial.
- Enregistrer les montants payés.
- Calculer le reste.
- Conserver l'historique.
- Afficher le statut.

États possibles :

- Non réglé.
- Partiellement réglé.
- Soldé.
- Annulé par procédure corrective.

### 11.3 Règlements

Permettre plusieurs règlements pour une même créance.

Chaque règlement doit conserver :

- Référence.
- Client.
- Dette ou vente concernée.
- Date.
- Montant.
- Moyen de paiement.
- Observation.

Mettre à jour le solde de façon fiable.

Empêcher les encaissements en double.

Un remboursement ou une annulation doit générer des écritures inverses explicites, sans supprimer l'historique de règlement.

### 11.4 Moyens de paiement

Prévoir les moyens suivants :

- Espèces.
- Orange Money.
- Wave.
- MTN Mobile Money.
- Virement bancaire.
- Autre.

Ces moyens doivent être configurables.

Aucune connexion API à ces opérateurs n'est requise dans cette version. L'utilisateur enregistre les paiements réellement reçus.

### 11.5 États clients

Fournir :

- Liste des débiteurs.
- Dette par client.
- Historique individuel.
- Total des créances.
- Créances soldées.
- Créances en retard si une échéance est renseignée.
- Reçu de règlement.

Les plafonds de crédit sont facultatifs. Lorsqu'ils sont définis, afficher un avertissement ou exiger une confirmation explicite en cas de dépassement.

## 12. MODULE 8 — CAISSE

Créer une véritable gestion de caisse.

### 12.1 Ouverture

Permettre :

- D'ouvrir une session.
- De saisir le solde initial en espèces.
- De consulter les dernières clôtures.

Empêcher plusieurs sessions simultanées si le modèle métier retenu prévoit une caisse unique.

### 12.2 Mouvements

Enregistrer :

- Encaissement d'une vente.
- Encaissement d'une dette client.
- Remboursement.
- Dépense.
- Autre recette.
- Correction justifiée.

Chaque mouvement contient une date, un montant, un type, un moyen de paiement et une référence.

### 12.3 Séparation des moyens

Distinguer :

- Espèces physiques.
- Orange Money.
- Wave.
- MTN Mobile Money.
- Virement.
- Autres.

Un paiement Mobile Money ne doit pas augmenter artificiellement le solde des espèces physiques.

### 12.4 Clôture

Au moment de fermer la caisse :

- Calculer les mouvements théoriques.
- Afficher les totaux par moyen de paiement.
- Demander les montants réellement constatés.
- Calculer les écarts.
- Enregistrer les commentaires.
- Conserver l'historique.

Ne pas considérer une vente à crédit impayée comme une recette de caisse.

Les achats réglés et les dépenses réglées doivent produire les mouvements de trésorerie correspondants.

## 13. MODULE 9 — DÉPENSES

Créer un module de suivi des dépenses quotidiennes.

Catégories initiales :

- Transport.
- Carburant.
- Chargement.
- Déchargement.
- Manutention.
- Réparation.
- Maintenance.
- Électricité.
- Frais administratifs.
- Divers.

Chaque dépense doit posséder :

- Référence.
- Date.
- Catégorie.
- Description.
- Montant.
- Moyen de paiement.
- Bénéficiaire facultatif.
- Justificatif facultatif.
- Statut de paiement si nécessaire.

Les dépenses réglées doivent produire des mouvements de caisse ou de trésorerie correspondants.

Les dépenses ne doivent pas être ajoutées automatiquement aux achats de marchandises.

## 14. MODULE 10 — RAPPORTS ET ANALYSES

Créer un espace de reporting utile à la gestion du dépôt.

### 14.1 Rapports commerciaux

- Ventes du jour.
- Ventes par période.
- Ventes en gros.
- Ventes au détail.
- Ventes par produit.
- Ventes par catégorie.
- Produits les plus vendus.
- Historique par client.

### 14.2 Rapports de stock

- Stock actuel.
- Valeur du stock.
- Produits en rupture.
- Produits en stock faible.
- Entrées et sorties.
- Historique des inventaires.

### 14.3 Rapports financiers

- Chiffre d'affaires.
- Encaissements.
- Créances clients.
- Dettes fournisseurs.
- Dépenses.
- Achats.
- Marge brute estimée selon le coût des marchandises sorties.
- Situation de trésorerie.

Toujours distinguer les ventes réalisées, les paiements encaissés et les soldes encore dus.

### 14.4 Calcul de marge

Mettre en place un calcul de coût moyen pondéré.

À la réception des achats, recalculer le coût moyen du produit de façon contrôlée.

Enregistrer le coût unitaire historique utilisé dans chaque ligne de vente.

Utiliser ce coût historique pour calculer la marge sur les ventes.

Ne jamais recalculer une ancienne marge avec le coût actuel du produit.

Lorsque le coût d'achat n'est pas renseigné ou fiable, afficher que la marge est indisponible plutôt que d'inventer un résultat.

### 14.5 Export

Prévoir :

- PDF.
- CSV.
- Export des ventes.
- Export des achats.
- Export des stocks.
- Export des créances.
- Export des dépenses.

Tous les exports doivent respecter les filtres et dates sélectionnés.

## 15. MODULE 11 — PARAMÈTRES ET CONFIGURATION

Créer un espace de paramètres regroupés.

### Paramètres généraux

- Nom commercial du dépôt.
- Téléphone.
- Adresse.
- Ville.
- Logo facultatif.
- Devise FCFA.
- Format de date.
- Préférences d'impression.

### Paramètres commerciaux

- Moyens de paiement actifs.
- Niveaux de prix.
- Autorisation ou non de stock négatif, désactivée par défaut.
- Alertes de stock.
- Plafonds de crédit facultatifs.
- Préférences de reçus.

### Paramètres de sécurité

- Modification du PIN.
- Temporisation.
- Verrouillage automatique.
- Procédure de récupération.

### Paramètres avancés

- Emplacement de la base de données.
- Sauvegardes.
- Restauration.
- Emplacement des exports.
- Informations de version.
- Vérification de l'intégrité.

Les paramètres sensibles ne doivent pas être modifiables sans contrôle adapté.

## 16. SAUVEGARDE ET RESTAURATION

Cette fonctionnalité est obligatoire.

### 16.1 Sauvegarde automatique

Prévoir une sauvegarde quotidienne locale.

Ne pas bloquer les ventes pendant une sauvegarde.

Utiliser une méthode SQLite cohérente, adaptée à une base ouverte, plutôt qu'une simple copie hasardeuse du fichier.

### 16.2 Sauvegarde manuelle

Permettre de lancer une sauvegarde à tout moment.

Afficher :

- Date.
- Heure.
- Taille.
- Emplacement.
- Résultat de vérification.

### 16.3 Restauration

Permettre de restaurer une sauvegarde.

Avant toute restauration :

1. Vérifier que le fichier existe.
2. Vérifier son intégrité.
3. Sauvegarder la base actuelle.
4. Demander confirmation.
5. Restaurer proprement.
6. Vérifier la nouvelle base.
7. Redémarrer les services si nécessaire.

Ne jamais écraser silencieusement la base actuelle.

## 17. EXPÉRIENCE UTILISATEUR ET DESIGN

Créer une interface de niveau professionnel.

L'application doit être :

- Moderne.
- Sobre.
- Élégante.
- Lisible.
- Rapide.
- Cohérente.
- Simple à apprendre.
- Adaptée à une utilisation quotidienne.

### Direction visuelle

Utiliser :

- Une palette sobre et professionnelle.
- Un fond clair.
- Des surfaces bien différenciées.
- Une typographie lisible.
- Des boutons clairs.
- Des icônes cohérentes.
- Des tableaux propres.
- Des formulaires bien organisés.
- Une navigation latérale simple.

Éviter les couleurs excessives, les animations inutiles et les éléments décoratifs qui ralentissent les opérations.

### Navigation

Organiser les menus dans cet ordre :

1. Tableau de bord.
2. Ventes.
3. Produits.
4. Stocks.
5. Approvisionnements.
6. Clients.
7. Crédits clients.
8. Fournisseurs.
9. Caisse.
10. Dépenses.
11. Rapports.
12. Paramètres.

La navigation doit permettre d'accéder rapidement aux actions quotidiennes.

### Productivité

Ajouter lorsque pertinent :

- Recherche instantanée.
- Filtres.
- Tri des tableaux.
- Pagination.
- Raccourcis clavier.
- Formulaires rapides.
- Confirmation des opérations sensibles.
- Messages de succès et d'erreur compréhensibles.
- Actualisation fiable des données.

Les tableaux doivent pouvoir gérer un volume significatif de produits, ventes et mouvements sans ralentissement excessif.

Ne pas charger inutilement toutes les données historiques à chaque affichage.

## 18. APPLICATION DE BUREAU WINDOWS ET MACOS

DEPOTPRO doit être livré comme une vraie application de bureau.

L'utilisateur ne doit pas avoir à ouvrir manuellement un terminal ou un navigateur.

### 18.1 Windows

Produire une application installable au format adapté, notamment :

- Exécutable `.exe`.
- Installateur Windows si possible.
- Icône DEPOTPRO.
- Dossier de données utilisateur.
- Désinstallation propre.

### 18.2 macOS

Produire :

- Application `.app`.
- Package `.dmg` si possible.
- Icône DEPOTPRO.
- Dossier de données utilisateur.

Les builds doivent être réalisés et testés sur leur système cible respectif. Ne prétends pas qu'un build Windows est un build macOS.

### 18.3 Fonctionnement local

Le démarrage doit :

1. Initialiser les services nécessaires.
2. Démarrer le serveur local.
3. Attendre que l'application soit prête.
4. Ouvrir la fenêtre native.
5. Gérer les erreurs de démarrage.
6. Arrêter proprement les services à la fermeture.

Si NiceGUI est conservé :

- Écouter uniquement sur l'adresse locale `127.0.0.1`.
- Ne pas exposer le serveur sur le réseau.
- Gérer correctement le port.
- Prévoir un arrêt propre.
- Ne pas dépendre d'un CDN ou d'images distantes.
- Fournir les ressources nécessaires localement.

L'application doit fonctionner sans accès Internet.

### 18.4 Stockage

Ne pas enregistrer la base de données dans le dossier d'installation du programme.

Utiliser les emplacements adaptés au système :

- Windows : dossier local de données utilisateur.
- macOS : `Application Support`.

Prévoir les dossiers :

- Base de données.
- Sauvegardes.
- Factures.
- Reçus.
- Exports.
- Images.
- Journaux.

Ne pas perdre ces dossiers lors de la mise à jour du programme.

## 19. MODÈLE DE DONNÉES ET INTÉGRITÉ

Vérifier et faire évoluer les modèles existants.

Le modèle cible doit couvrir au minimum :

- Product.
- ProductPackaging.
- Category.
- Supplier.
- Client.
- PurchaseOrder.
- PurchaseOrderLine.
- Sale.
- SaleLine.
- Payment.
- ClientDebt.
- SupplierDebt.
- StockMovement.
- CashSession.
- CashMovement.
- Expense.
- AppSettings.
- BackupHistory, si utile.

Les tables existantes peuvent être conservées ou adaptées après audit.

### Règles d'intégrité

- Une référence commerciale doit être unique.
- Une quantité doit être positive lors d'une saisie.
- Un montant ne doit pas être négatif sauf écriture corrective explicitement définie.
- Un paiement ne doit pas être comptabilisé deux fois.
- Un stock ne doit pas être modifié sans mouvement historique.
- Une vente ne doit pas être supprimée physiquement après validation.
- Une réception ne doit pas être enregistrée deux fois.
- Les annulations doivent conserver les traces.
- Les opérations financières doivent être cohérentes entre ventes, créances, paiements et caisse.

Choisir une architecture de paiement et de dette évitant les doubles comptabilisations.

Toute écriture doit avoir une seule source de vérité clairement définie.

Prévoir des contraintes SQL, des transactions et des tests qui garantissent ces invariants.

## 20. ORDRE OBLIGATOIRE D'IMPLÉMENTATION

Tu dois respecter la feuille de route suivante.

### PHASE 0 — AUDIT COMPLET

Avant toute modification :

- Inspecter tout le dépôt.
- Identifier les fichiers et modules.
- Identifier les modèles.
- Identifier les appels entre pages et services.
- Identifier les fonctions manquantes.
- Identifier les erreurs d'attributs et de signatures.
- Identifier les dépendances inutilisées.
- Vérifier les versions.
- Identifier le fonctionnement de la base existante.

Livrable :

`docs/AUDIT_TECHNIQUE.md`

Ce document doit contenir les problèmes découverts, leur priorité et leur solution.

### PHASE 1 — SÉCURISATION DES FONDATIONS

- Créer une branche de développement.
- Sauvegarder les données existantes.
- Définir une architecture propre.
- Mettre en place les migrations.
- Corriger l'initialisation SQLite.
- Réduire les fonctionnalités multi-utilisateurs.
- Mettre en place le démarrage de première utilisation.
- Préparer les paramètres.

Tests obligatoires avant de poursuivre.

### PHASE 2 — PRODUITS ET CONDITIONNEMENTS

- Corriger le modèle Produit.
- Créer ProductPackaging.
- Mettre en place les conversions.
- Gérer les tarifs par conditionnement.
- Développer les formulaires produit.
- Développer les listes et filtres.
- Développer les imports/exports.

Tests obligatoires sur tous les coefficients configurés.

### PHASE 3 — ACHATS ET STOCKS

- Corriger les services d'achat.
- Développer les réceptions.
- Gérer les réceptions partielles.
- Convertir les conditionnements.
- Développer StockService.
- Développer l'historique.
- Développer les alertes.
- Développer les inventaires.

Vérifier que toute entrée de stock produit la bonne quantité de base.

### PHASE 4 — VENTES ET PAIEMENTS

- Refaire la page nouvelle vente.
- Développer le mode gros et détail.
- Développer le panier.
- Développer les prix par conditionnement.
- Développer les paiements.
- Développer les ventes partiellement payées.
- Développer les créances.
- Développer les reçus PDF.
- Développer les retours et annulations.

Tests obligatoires sur les conversions, les règlements et les mouvements de stock.

### PHASE 5 — CLIENTS ET FOURNISSEURS

- Corriger les fiches.
- Gérer les comptes clients.
- Gérer les dettes.
- Gérer les remboursements.
- Gérer les fournisseurs.
- Gérer les paiements fournisseurs.
- Développer les historiques.

Vérifier les soldes après plusieurs règlements successifs.

### PHASE 6 — CAISSE ET DÉPENSES

- Refaire les ouvertures.
- Refaire les clôtures.
- Gérer les moyens de paiement.
- Séparer espèces et paiements électroniques.
- Relier les paiements aux mouvements.
- Développer les dépenses.
- Contrôler les écarts.

### PHASE 7 — RAPPORTS ET TABLEAU DE BORD

- Développer les indicateurs.
- Développer les statistiques.
- Développer la valorisation.
- Développer le calcul de marge.
- Développer les filtres.
- Développer les exports.

Vérifier tous les chiffres par des tests indépendants.

### PHASE 8 — SAUVEGARDE ET SÉCURITÉ

- Mettre en place le PIN six chiffres.
- Mettre en place bcrypt.
- Mettre en place la limitation des tentatives.
- Mettre en place le verrouillage.
- Mettre en place les sauvegardes.
- Mettre en place les restaurations.
- Vérifier l'intégrité des données.

### PHASE 9 — FINITION ET DESIGN

- Uniformiser tous les écrans.
- Corriger les formulaires.
- Améliorer la navigation.
- Améliorer les tableaux.
- Vérifier les erreurs.
- Vérifier le responsive des fenêtres.
- Vérifier l'accessibilité et la lisibilité.
- Retirer les pages et éléments inutilisés.

### PHASE 10 — BUILD ET VALIDATION FINALE

- Préparer PyInstaller.
- Construire le package Windows.
- Construire le package macOS sur macOS.
- Installer sur un environnement propre.
- Tester le lancement.
- Tester la fermeture.
- Tester la persistance des données.
- Tester les sauvegardes.
- Tester l'absence de connexion Internet.
- Vérifier tous les parcours métier.

Livrer les packages réellement générés et testés.

## 21. TESTS FONCTIONNELS OBLIGATOIRES

Tu dois automatiser autant que possible les scénarios suivants.

### Test A — Produit et conversion

Créer une boisson ayant comme unité de base la bouteille.

Configurer des équivalences fictives de test :

- Un pack = 6 bouteilles.
- Un carton = 12 bouteilles.
- Un casier = 24 bouteilles.

Vérifier que les ventes et achats convertissent correctement les quantités.

Ces valeurs ne sont utilisées que dans les données de test.

### Test B — Approvisionnement

Réceptionner 10 casiers de 24 bouteilles.

Résultat attendu :

Stock augmenté de 240 bouteilles.

### Test C — Vente

Vendre un casier et trois bouteilles.

Résultat attendu :

Stock diminué de 27 bouteilles.

### Test D — Vente à crédit

Effectuer une vente de 100 000 FCFA.

Enregistrer un premier paiement de 30 000 FCFA.

Résultat attendu :

- Chiffre d'affaires : 100 000 FCFA.
- Encaissement : 30 000 FCFA.
- Créance restante : 70 000 FCFA.

### Test E — Remboursements

Encaisser 20 000 FCFA supplémentaires.

Résultat attendu :

Créance restante : 50 000 FCFA.

Encaisser ensuite 50 000 FCFA.

Résultat attendu :

Créance restante : zéro.

Les paiements doivent apparaître une seule fois dans la caisse.

### Test F — Paiement numérique

Effectuer une vente payée par Wave ou Orange Money.

Résultat attendu :

Le mouvement apparaît dans le total du moyen de paiement concerné et ne gonfle pas les espèces physiques.

### Test G — Annulation

Annuler une vente selon la procédure corrective.

Vérifier :

- Le stock.
- La créance.
- Les paiements.
- Les remboursements.
- La caisse.
- L'historique.

Aucune trace ne doit disparaître.

### Test H — Inventaire

Créer un écart entre stock théorique et stock physique.

Valider une correction.

Résultat attendu :

Le stock actualisé correspond au stock physique et le mouvement de correction est conservé.

### Test I — Sauvegarde

Créer une sauvegarde, effectuer une opération, restaurer la sauvegarde.

Vérifier que la base restaurée correspond à son état à la date de sauvegarde.

### Test J — Hors ligne

Couper l'accès Internet.

Démarrer DEPOTPRO.

Créer une vente, fermer l'application et la redémarrer.

Résultat attendu :

L'application reste fonctionnelle et les données sont conservées.

## 22. GESTION DES ERREURS ET QUALITÉ

Tu dois :

- Ajouter des validations côté interface et côté service.
- Gérer proprement les erreurs SQL.
- Éviter les exceptions silencieuses.
- Afficher des messages compréhensibles.
- Journaliser les incidents techniques.
- Ne jamais enregistrer de PIN ou d'informations sensibles dans les logs.
- Fermer proprement les sessions SQLAlchemy.
- Éviter les transactions laissées ouvertes.
- Vérifier les références uniques.
- Protéger les actions irréversibles.
- Ajouter les tests de non-régression.

Le logiciel ne doit pas perdre de données si l'application se ferme de façon inattendue.

Prévoir une stratégie cohérente de récupération et de contrôle d'intégrité.

## 23. DOCUMENTATION ET LIVRABLES

Créer ou mettre à jour les documents suivants :

- `README.md` : présentation et instructions générales.
- `docs/AUDIT_TECHNIQUE.md` : diagnostic initial.
- `docs/ARCHITECTURE.md` : architecture du logiciel.
- `docs/SPECIFICATION_FONCTIONNELLE.md` : fonctionnalités.
- `docs/MODELE_DONNEES.md` : données et relations.
- `docs/REGLES_METIER.md` : conversions, ventes, crédits, caisse et stock.
- `docs/INSTALLATION.md` : installation sur Windows et macOS.
- `docs/SAUVEGARDE_RESTAURATION.md` : gestion des données.
- `docs/TESTS.md` : résultats des tests.
- `docs/CHANGELOG.md` : historique des évolutions.

Créer également :

- Scripts de migration.
- Scripts de test.
- Configuration de build.
- Fichiers de packaging.
- Script d'initialisation.
- Procédure de récupération documentée.

## 24. CONDITIONS DE VALIDATION FINALE

Le projet ne peut être considéré comme terminé que lorsque les conditions suivantes sont satisfaites.

### Fonctionnel

- Toutes les pages obligatoires sont présentes.
- Tous les formulaires fonctionnent.
- Tous les boutons importants fonctionnent.
- Les produits sont configurables.
- Les conditionnements sont convertis correctement.
- Les approvisionnements augmentent correctement le stock.
- Les ventes diminuent correctement le stock.
- Les ventes à crédit créent des créances.
- Les remboursements mettent à jour les soldes.
- La caisse distingue les moyens de paiement.
- Les rapports utilisent les données réelles.
- Les annulations conservent l'historique.

### Technique

- Les modèles sont cohérents.
- Les services sont indépendants de l'interface.
- Les opérations métier importantes sont transactionnelles.
- Les erreurs critiques sont corrigées.
- Les migrations sont documentées.
- Les données existantes sont préservées.
- Les sauvegardes fonctionnent.
- Les tests automatisés passent.
- Les dépendances sont cohérentes.
- Aucun secret n'est stocké en clair.

### Desktop

- L'application s'ouvre dans une fenêtre native.
- Elle fonctionne sans navigateur manuel.
- Elle fonctionne hors ligne.
- Elle conserve ses données après fermeture.
- Les chemins de stockage sont adaptés à chaque système.
- Les installations ont été testées sur leurs systèmes cibles.

### Interface

- Le design est cohérent.
- L'interface est fluide.
- Aucun écran essentiel n'est vide ou fictif.
- Aucune erreur graphique majeure n'est présente.
- Les données sont lisibles.
- Les principales tâches quotidiennes sont rapides.

## 25. COMPORTEMENT ATTENDU DE L'AGENT IA

Tu dois travailler comme un véritable responsable technique du projet.

À chaque phase, indique :

1. Ce que tu as inspecté.
2. Ce que tu as modifié.
3. Les fichiers créés.
4. Les fichiers corrigés.
5. Les problèmes résolus.
6. Les tests exécutés.
7. Les résultats obtenus.
8. Les problèmes qui restent.

Tu dois privilégier les modifications concrètes et vérifiables.

Ne prétends jamais avoir exécuté un test qui ne l'a pas été.

Ne prétends jamais avoir généré un installateur qui n'a pas réellement été construit.

Ne prétends jamais qu'une application fonctionne sur macOS si elle n'a été testée que sur Windows, et inversement.

Lorsqu'un problème bloque une phase, explique précisément sa cause, effectue toutes les corrections possibles et signale ce qui nécessite réellement une intervention extérieure.

Ne masque aucune erreur.

Ne remplace pas un comportement métier correct par une solution de contournement fragile.

Ne réduis pas les tests pour obtenir artificiellement un résultat positif.

Ne t'arrête pas à une interface visuellement terminée : les opérations doivent être connectées à la base de données et aux services métier.

Ne demande pas de confirmation après chaque étape. Continue de manière autonome dans le respect du présent cahier des charges.

Si une décision commerciale essentielle n'est pas documentée, ne l'invente pas. Prévois un paramètre configurable ou consigne la question dans `docs/DECISIONS_A_VALIDER.md`, puis poursuis les autres travaux indépendants.

## 26. INSTRUCTION FINALE — COMMENCER L'EXÉCUTION

Tu dois maintenant prendre le contrôle technique du projet DEPOTPRO.

**COMMENCE PAR LA PHASE 0 : AUDIT COMPLET DU DÉPÔT.**

Ensuite :

1. Établis le diagnostic.
2. Définis l'architecture corrigée.
3. Prépare la branche de développement.
4. Protège les données existantes.
5. Exécute les phases dans l'ordre.
6. Développe réellement chaque module.
7. Connecte les interfaces aux services.
8. Automatise les tests.
9. Corrige les anomalies.
10. Prépare les versions Windows et macOS.
11. Documente les résultats.
12. Livre l'application et les instructions d'installation.

**OBJECTIF FINAL : LIVRER UN VÉRITABLE LOGICIEL DEPOTPRO DESKTOP, FIABLE, COMPLET, SOBRE, RAPIDE, SÉCURISÉ, FONCTIONNEL ET UTILISABLE QUOTIDIENNEMENT DANS MON DÉPÔT DE BOISSONS.**

Ne te contente pas de proposer ce qu'il faudrait faire.

**ANALYSE, CODE, INTÈGRE, TESTE, CORRIGE ET LIVRE.**

NB: consigner ce texte dans un fichier MAJ.md et suivre les instructions consignées.
