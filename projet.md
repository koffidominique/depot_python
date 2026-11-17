# MASTER PROMPT D'EXÉCUTION — DEPOTPRO ERP DESKTOP

## Création d'un logiciel professionnel de gestion de dépôt de boissons — Production Ready

---

# 1. RÔLE ET MISSION DE L'AGENT IA

Agis comme une équipe senior composée de :

- Un architecte logiciel Python spécialisé en applications desktop.
- Un développeur expert Python 3.11+, NiceGUI et SQLAlchemy.
- Un expert en gestion commerciale, stocks et distribution de boissons.
- Un expert en comptabilité opérationnelle et gestion des créances.
- Un expert UI/UX spécialisé dans les ERP SaaS modernes.
- Un ingénieur DevOps spécialisé dans PyInstaller et la distribution d'applications Windows/macOS.
- Un ingénieur QA spécialisé dans les tests automatisés et la fiabilité des applications métier.

Ta mission consiste à concevoir et développer une application complète, autonome, professionnelle et commercialisable appelée provisoirement :

**DEPOTPRO ERP**

Cette application doit permettre à un commerçant, grossiste ou distributeur de boissons de gérer intégralement son activité depuis un ordinateur Windows ou macOS.

Il ne s'agit pas de produire une maquette, une démonstration visuelle ou un simple prototype.

Tu dois développer un véritable logiciel métier fonctionnel, persistant, sécurisé, évolutif et prêt à être utilisé dans un environnement commercial réel.

**RÈGLE ABSOLUE : aucune fonctionnalité affichée dans l'interface ne doit être fictive. Chaque bouton, formulaire, filtre, action et indicateur doit être relié à une véritable logique métier et à la base de données.**

Ne laisse aucun TODO, aucune fonction vide, aucune donnée simulée dans les fonctionnalités de production et aucun raccourci architectural.

---

# 2. OBJECTIFS FONCTIONNELS DU LOGICIEL

Le logiciel doit couvrir les domaines suivants :

1. Tableau de bord général.
2. Gestion des produits et du catalogue.
3. Gestion avancée des catégories et conditionnements.
4. Gestion des stocks et des mouvements.
5. Gestion des clients.
6. Gestion des fournisseurs.
7. Gestion des achats.
8. Gestion des bons de commande fournisseurs.
9. Réception des marchandises.
10. Gestion des ventes en gros et demi-gros.
11. Point de vente et caisse.
12. Facturation et édition des reçus.
13. Gestion des livraisons.
14. Gestion des créances clients.
15. Gestion des dettes fournisseurs.
16. Gestion des paiements et encaissements.
17. Gestion des consignes et emballages récupérables.
18. Gestion des dépenses.
19. Gestion des caisses et clôtures journalières.
20. Inventaires physiques.
21. Rapports et statistiques.
22. Gestion des utilisateurs et des permissions.
23. Paramètres avancés et personnalisation.
24. Sauvegarde et restauration.
25. Journal d'activité et audit.

L'ensemble doit être cohérent : les opérations réalisées dans un module doivent automatiquement mettre à jour les autres modules concernés.

---

# 3. STACK TECHNIQUE OBLIGATOIRE

## Langage

- Python 3.11 minimum.
- Architecture modulaire.
- Typage Python lorsque pertinent.
- Code documenté et maintenable.

## Interface graphique

- NiceGUI.
- Mode bureau natif avec pywebview.
- Lancement via `ui.run(native=True, reload=False)`.
- Aucune fenêtre de navigateur visible.
- Navigation interne sans rechargement complet des pages.
- Interface optimisée pour les écrans desktop.

Utiliser les véritables classes Tailwind CSS intégrées à la version de NiceGUI retenue.

Éviter de remplacer Tailwind par une accumulation de CSS personnalisé.

## Base de données

- SQLite.
- SQLAlchemy ORM.
- Transactions ACID.
- Contraintes d'intégrité.
- Clés étrangères activées.
- Index sur les champs de recherche.
- Gestion correcte des sessions et connexions.
- Migrations de schéma avec Alembic.

## Documents PDF

Utiliser ReportLab pour générer :

- Factures.
- Reçus de paiement.
- Bons de livraison.
- Bons de commande.
- Bons de réception.
- Relevés de compte client.
- Relevés de compte fournisseur.
- Rapports de caisse.
- Rapports d'inventaire.

## Bibliothèques complémentaires

- Pydantic pour la validation des données.
- bcrypt ou Argon2 pour le hachage des mots de passe.
- Alembic pour les migrations.
- ReportLab pour les PDF.
- openpyxl pour les exports Excel.
- pytest pour les tests.
- logging pour les journaux techniques.

## Stockage permanent

Le stockage des données ne doit jamais dépendre du dossier temporaire de PyInstaller.

Utiliser obligatoirement :

`Path.home() / "DepotPro_Data"`

Arborescence des données :

- DepotPro_Data/depot.db
- DepotPro_Data/Factures/
- DepotPro_Data/Bons_Commande/
- DepotPro_Data/Bons_Livraison/
- DepotPro_Data/Reçus/
- DepotPro_Data/Exports/
- DepotPro_Data/Backups/
- DepotPro_Data/Logs/
- DepotPro_Data/Images/

Créer automatiquement les dossiers manquants.

Le logiciel doit conserver ses données après fermeture, redémarrage, mise à jour et recompilation de l'application.

---

# 4. ARCHITECTURE GÉNÉRALE ET ORGANISATION

Construire une architecture propre séparant l'interface, la logique métier, les données et les services.

Structure attendue :

DepotPro/
│
├── main.py
├── database.py
├── config.py
├── theme.py
├── requirements.txt
├── README.md
├── build.py
├── alembic.ini
│
├── migrations/
│ └── versions/
│
├── models/
│ ├── **init**.py
│ ├── product.py
│ ├── category.py
│ ├── client.py
│ ├── supplier.py
│ ├── sale.py
│ ├── purchase.py
│ ├── stock.py
│ ├── payment.py
│ ├── delivery.py
│ ├── consignation.py
│ ├── expense.py
│ ├── cash.py
│ ├── user.py
│ └── settings.py
│
├── services/
│ ├── product_service.py
│ ├── stock_service.py
│ ├── sales_service.py
│ ├── purchase_service.py
│ ├── client_service.py
│ ├── supplier_service.py
│ ├── payment_service.py
│ ├── delivery_service.py
│ ├── debt_service.py
│ ├── consignation_service.py
│ ├── cash_service.py
│ ├── reporting_service.py
│ ├── backup_service.py
│ └── auth_service.py
│
├── repositories/
│ ├── product_repository.py
│ ├── client_repository.py
│ ├── supplier_repository.py
│ └── sales_repository.py
│
├── pages/
│ ├── dashboard.py
│ ├── products.py
│ ├── categories.py
│ ├── stock.py
│ ├── clients.py
│ ├── suppliers.py
│ ├── sales.py
│ ├── purchases.py
│ ├── deliveries.py
│ ├── debts.py
│ ├── consignations.py
│ ├── cash.py
│ ├── expenses.py
│ ├── inventory.py
│ ├── reports.py
│ ├── users.py
│ └── settings.py
│
├── components/
│ ├── sidebar.py
│ ├── header.py
│ ├── data_table.py
│ ├── dialogs.py
│ ├── forms.py
│ ├── notifications.py
│ └── charts.py
│
├── utils/
│ ├── formatters.py
│ ├── validators.py
│ ├── permissions.py
│ ├── numbering.py
│ └── dates.py
│
├── pdf/
│ ├── invoice.py
│ ├── receipt.py
│ ├── purchase_order.py
│ ├── delivery_note.py
│ └── reports.py
│
├── assets/
│ ├── logo.png
│ └── icons/
│
└── tests/
├── test_products.py
├── test_stock.py
├── test_sales.py
├── test_purchases.py
├── test_payments.py
├── test_consignment.py
├── test_cash.py
└── test_backup.py

Tu peux enrichir cette structure si cela améliore réellement la qualité de l'architecture.

Ne concentre pas toute l'application dans main.py.

---

# 5. DESIGN UI/UX — EXIGENCE PREMIUM

Créer une interface professionnelle inspirée des meilleurs ERP SaaS modernes.

## Identité visuelle

Nom : DEPOTPRO.

Style :

- Moderne.
- Minimaliste.
- Professionnel.
- Élégant.
- Lisible.
- Orienté productivité.

Palette recommandée :

- Fond général : `bg-slate-50`.
- Sidebar : `bg-slate-900`.
- Cartes : `bg-white`.
- Bordures : `border-slate-200`.
- Texte principal : `text-slate-900`.
- Texte secondaire : `text-slate-500`.
- Bleu primaire : `bg-blue-600`.
- Vert : encaissements et indicateurs positifs.
- Orange : avertissements.
- Rouge : erreurs et alertes critiques.

## Sidebar

Créer une barre latérale fixe de 256 px environ.

Elle doit comporter :

- Logo et nom DEPOTPRO.
- Tableau de bord.
- Ventes.
- Nouvelle vente.
- Produits.
- Stocks.
- Achats.
- Fournisseurs.
- Clients.
- Livraisons.
- Créances et dettes.
- Consignations.
- Caisse.
- Dépenses.
- Inventaires.
- Rapports.
- Utilisateurs.
- Paramètres.

Prévoir des icônes cohérentes et un état actif clairement visible.

## Header

Afficher :

- Titre de la page.
- Fil d'Ariane.
- Date du jour.
- Nom de l'utilisateur connecté.
- État de la caisse.
- Bouton Nouvelle vente.
- Notifications.

## Composants

Créer des composants réutilisables :

- Cartes KPI.
- Tableaux avec pagination.
- Filtres.
- Recherche instantanée.
- Modales de création et modification.
- Formulaires validés.
- Badges de statut.
- Boutons d'action.
- Notifications.
- Graphiques.
- Fenêtres de confirmation.

Toutes les pages doivent conserver une identité visuelle homogène.

Prévoir une interface responsive pour les différentes résolutions desktop.

---

# 6. MODULE TABLEAU DE BORD

Créer un tableau de bord donnant une vision instantanée de l'activité.

## Indicateurs KPI

Afficher :

1. Chiffre d'affaires du jour.
2. Total des ventes du jour.
3. Valeur du stock disponible.
4. Nombre de produits en rupture ou sous seuil.
5. Créances clients.
6. Dettes fournisseurs.
7. Nombre de clients actifs.
8. Nombre de casiers consignés chez les clients.

## Graphiques

- Évolution du chiffre d'affaires sur 7 jours.
- Évolution mensuelle.
- Répartition des ventes par catégorie.
- Top 10 des produits vendus.
- Évolution des achats.
- Comparaison ventes et dépenses.

## Tableaux

- Dernières ventes.
- Derniers achats.
- Produits à réapprovisionner.
- Créances en retard.
- Livraisons en cours.
- Derniers mouvements de stock.

Tous les indicateurs doivent être calculés à partir des données réelles.

Ajouter des filtres par période.

---

# 7. MODULE PRODUITS ET CATALOGUE

Créer une gestion complète des boissons.

## Informations produit

Chaque produit doit contenir :

- Référence interne unique.
- Code-barres facultatif.
- Nom commercial.
- Marque.
- Catégorie.
- Description.
- Fournisseur principal.
- Conditionnement.
- Unité de stockage.
- Prix d'achat.
- Prix de vente gros.
- Prix de vente demi-gros.
- Prix de vente détail.
- Quantité disponible.
- Stock minimum.
- Stock maximum.
- Montant de consigne.
- Image du produit.
- Statut actif/inactif.

## Catégories initiales

- Eau minérale.
- Eau gazeuse.
- Soda.
- Jus.
- Bière.
- Vin.
- Spiritueux.
- Boissons énergétiques.
- Autres boissons.

Les catégories doivent être personnalisables.

## Conditionnements

Prendre en charge :

- Unité.
- Pack.
- Carton.
- Casier.
- Fût.
- Palette.

Prévoir une gestion des équivalences entre unités.

Exemple :

1 casier = 24 bouteilles.

1 palette = 50 casiers.

Ces équivalences doivent être configurables par produit et ne doivent jamais être supposées identiques pour tous les produits.

Permettre les conversions automatiques et exactes lors des ventes, achats et inventaires.

## Actions

- Ajouter.
- Modifier.
- Désactiver.
- Supprimer uniquement si aucune opération historique ne l'interdit.
- Rechercher.
- Filtrer.
- Importer Excel.
- Exporter Excel.
- Imprimer le catalogue.
- Consulter l'historique.

---

# 8. MODULE STOCKS

Créer une gestion fiable et traçable des stocks.

Chaque mouvement doit être enregistré.

Types de mouvements :

- Stock initial.
- Entrée fournisseur.
- Sortie vente.
- Retour client.
- Retour fournisseur.
- Casse.
- Perte.
- Ajustement positif.
- Ajustement négatif.
- Transfert éventuel.

Chaque mouvement comporte :

- Produit.
- Date.
- Type.
- Quantité.
- Unité.
- Stock avant.
- Stock après.
- Utilisateur.
- Motif.
- Document de référence.

## Fonctionnalités

- Consultation du stock en temps réel.
- Alertes de stock minimum.
- Détection des ruptures.
- Historique des mouvements.
- Inventaire physique.
- Ajustement après validation.
- Valorisation du stock.
- Export des états.
- Recherche multicritère.

Utiliser une méthode cohérente de valorisation, par exemple le coût moyen pondéré, configurable si nécessaire.

Interdire les stocks négatifs par défaut, avec possibilité de paramétrage explicite.

Les ventes, achats, retours et inventaires doivent modifier le stock dans une transaction atomique.

---

# 9. MODULE CLIENTS

Créer une fiche complète pour chaque client.

Types :

- Grossiste.
- Bar.
- Restaurant.
- Hôtel.
- Épicerie.
- Revendeur.
- Particulier.
- Autre.

Informations :

- Code client.
- Nom ou raison sociale.
- Téléphone.
- Adresse.
- Ville.
- Email.
- Contact principal.
- Plafond de crédit.
- Solde financier.
- Solde de consignes.
- Conditions de paiement.
- Statut.
- Date de création.

## Fiche client détaillée

Afficher :

- Historique des ventes.
- Factures.
- Paiements.
- Créances.
- Consignations.
- Retours de casiers.
- Livraisons.
- Relevé de compte.
- Solde actuel.

Actions :

- Nouvelle vente.
- Enregistrer paiement.
- Retour de consignes.
- Consulter les dettes.
- Imprimer relevé.
- Exporter historique.

Un client doit pouvoir acheter au comptant ou à crédit selon les autorisations et paramètres définis.

---

# 10. MODULE FOURNISSEURS

Créer un module complet de gestion des fournisseurs.

Informations :

- Code fournisseur.
- Nom commercial.
- Raison sociale.
- Téléphone.
- Adresse.
- Email.
- Contact.
- Conditions de règlement.
- Solde dû.
- Statut.

Fonctionnalités :

- Historique des achats.
- Bons de commande.
- Réceptions.
- Factures fournisseurs.
- Paiements.
- Dettes.
- Retours fournisseurs.
- Relevés de compte.
- Documents PDF.

---

# 11. MODULE ACHATS ET BONS DE COMMANDE

Créer un processus d'achat professionnel.

Étapes :

1. Création du bon de commande.
2. Sélection du fournisseur.
3. Ajout des produits.
4. Définition des quantités.
5. Calcul automatique des montants.
6. Validation.
7. Impression du bon de commande.
8. Réception totale ou partielle.
9. Mise à jour du stock.
10. Enregistrement de la dette fournisseur.
11. Enregistrement du paiement éventuel.

Statuts :

- Brouillon.
- En attente.
- Validé.
- Partiellement réceptionné.
- Réceptionné.
- Annulé.

Une commande ne doit pas augmenter le stock avant sa réception effective.

Conserver l'historique des réceptions partielles.

Gérer les écarts entre quantités commandées et reçues.

---

# 12. MODULE VENTES ET POINT DE VENTE

Créer un véritable écran de caisse rapide.

L'écran doit être ergonomique et adapté à une utilisation intensive.

## Interface

- Recherche de produits.
- Recherche par nom ou code-barres.
- Sélection du client.
- Catégories rapides.
- Panier.
- Quantités modifiables.
- Prix unitaires.
- Remises.
- Consignes.
- Total à payer.
- Paiements.

## Tarification

Prendre en charge :

- Tarif grossiste.
- Tarif demi-gros.
- Tarif détaillant.
- Tarif personnalisé client.

Les prix doivent être sélectionnables et modifiables selon les autorisations.

## Panier

Afficher :

- Produit.
- Conditionnement.
- Quantité.
- Prix unitaire.
- Remise.
- Consigne.
- Total ligne.

Calculer :

- Total marchandises.
- Remises.
- Taxes éventuelles.
- Total consignes.
- Total général.
- Montant payé.
- Reste à payer.
- Monnaie à rendre.

## Modes de paiement

- Espèces.
- Mobile Money.
- Virement.
- Carte bancaire.
- Chèque.
- Paiement mixte.
- Crédit client.

Les moyens de paiement doivent être personnalisables.

## Validation

Lors de la validation :

- Créer la vente.
- Créer ses lignes.
- Décrémenter le stock.
- Enregistrer les paiements.
- Mettre à jour les créances.
- Mettre à jour les consignes.
- Enregistrer les mouvements.
- Générer le numéro de facture.
- Produire le document PDF.

Toutes ces opérations doivent être effectuées dans une transaction cohérente.

Ne jamais enregistrer une vente partiellement.

Prévoir l'annulation contrôlée d'une vente avec mouvements de stock inverses et traçabilité.

---

# 13. MODULE CONSIGNATIONS

Ce module est essentiel pour un dépôt de boissons.

Gérer :

- Casiers.
- Bouteilles consignées.
- Fûts.
- Palettes.
- Autres emballages récupérables.

Créer un véritable registre des consignations.

Pour chaque client, suivre :

- Quantités sorties.
- Quantités retournées.
- Quantités restantes.
- Valeur financière.
- Date de sortie.
- Date de retour.
- Référence de vente.
- État des emballages.

## Retours

Permettre :

- Retour complet.
- Retour partiel.
- Retour d'emballages endommagés.
- Retour avec remboursement.
- Retour avec déduction sur une nouvelle vente.

Le système doit distinguer les quantités physiques des montants financiers.

Un retour de casier ne doit pas être traité comme un paiement ordinaire.

Conserver un historique complet et éviter les doubles retours.

---

# 14. MODULE LIVRAISONS

Créer une gestion des livraisons clients.

Fonctionnalités :

- Création d'une livraison depuis une vente.
- Affectation d'un livreur.
- Adresse de livraison.
- Date prévue.
- Frais de transport.
- Produits et quantités.
- Statut de livraison.

Statuts :

- À préparer.
- En préparation.
- En cours.
- Livrée.
- Partiellement livrée.
- Échec.
- Annulée.

Générer un bon de livraison PDF.

Permettre la confirmation de réception par le client ou le livreur.

Une livraison ne doit pas provoquer une seconde sortie de stock si celle-ci a déjà été comptabilisée au moment de la vente.

Gérer les livraisons partielles et les retours de marchandises.

---

# 15. MODULE CRÉANCES CLIENTS ET DETTES FOURNISSEURS

Créer un véritable suivi des comptes tiers.

## Créances clients

Afficher :

- Client.
- Numéro de facture.
- Montant initial.
- Montant payé.
- Solde restant.
- Date d'échéance.
- Retard.
- Statut.

Actions :

- Enregistrer un règlement.
- Effectuer un règlement partiel.
- Consulter l'historique.
- Imprimer un reçu.
- Générer un relevé.
- Filtrer les retards.

## Dettes fournisseurs

Même principe :

- Fournisseur.
- Facture d'achat.
- Montant initial.
- Paiements.
- Solde restant.
- Échéance.
- Statut.

Ne jamais confondre une dette, un encaissement et une dépense.

Les soldes doivent être calculés à partir des écritures financières enregistrées.

Prévoir un historique non destructif de tous les règlements.

---

# 16. MODULE CAISSE ET CLÔTURE JOURNALIÈRE

Créer une véritable gestion de caisse.

Fonctionnalités :

- Ouverture de caisse.
- Fond de caisse initial.
- Encaissements.
- Décaissements.
- Dépenses.
- Retraits.
- Entrées exceptionnelles.
- Clôture.
- Écart de caisse.

Afficher :

- Total espèces.
- Total Mobile Money.
- Total virements.
- Total autres paiements.
- Dépenses.
- Montant théorique.
- Montant physique.
- Différence.

La clôture doit être historisée et protégée contre les modifications non autorisées.

Permettre l'impression du rapport de caisse.

Prévoir plusieurs caisses ou sessions utilisateurs si nécessaire.

---

# 17. MODULE DÉPENSES

Enregistrer les dépenses du dépôt.

Catégories configurables :

- Transport.
- Carburant.
- Personnel.
- Électricité.
- Loyer.
- Entretien.
- Emballages.
- Divers.

Informations :

- Référence.
- Catégorie.
- Montant.
- Date.
- Mode de paiement.
- Bénéficiaire.
- Justificatif.
- Commentaire.
- Utilisateur.

Les dépenses payées depuis la caisse doivent modifier son solde.

Les dépenses à crédit doivent être identifiées séparément.

---

# 18. MODULE INVENTAIRE

Créer un processus d'inventaire physique.

Fonctionnalités :

- Démarrer un inventaire.
- Générer une liste des produits.
- Saisir les quantités physiques.
- Comparer avec les quantités théoriques.
- Calculer les écarts.
- Justifier les différences.
- Valider l'inventaire.
- Générer les mouvements correctifs.
- Imprimer le rapport.

Interdire la validation d'un même inventaire plusieurs fois.

Préserver la traçabilité avant/après.

---

# 19. MODULE DOCUMENTS ET IMPRESSIONS

Tous les documents doivent être professionnels.

Utiliser ReportLab.

Prévoir :

## Facture A4

- Logo.
- Nom du dépôt.
- Coordonnées.
- Informations client.
- Numéro de facture.
- Date.
- Tableau des produits.
- Quantités.
- Prix.
- Remises.
- Consignes.
- Taxes.
- Total.
- Montant payé.
- Reste dû.
- Signature.
- Conditions commerciales.

## Reçu de paiement

- Format A4 et ticket thermique.
- Référence.
- Client.
- Montant reçu.
- Mode de paiement.
- Date.
- Solde restant.

## Autres documents

- Bon de commande A4.
- Bon de livraison A4.
- Bon de réception.
- Relevé client.
- Relevé fournisseur.
- État de stock.
- Rapport d'inventaire.
- Rapport de caisse.

Prévoir l'aperçu PDF avant impression et l'ouverture du fichier avec le lecteur PDF du système.

La génération PDF ne doit jamais bloquer l'interface.

---

# 20. MODULE RAPPORTS ET STATISTIQUES

Créer des rapports filtrables par période.

Rapports obligatoires :

- Chiffre d'affaires journalier.
- Chiffre d'affaires mensuel.
- Ventes par produit.
- Ventes par catégorie.
- Ventes par client.
- Achats par fournisseur.
- Marge commerciale estimée.
- État du stock.
- Valeur du stock.
- Produits à faible rotation.
- Produits les plus vendus.
- Créances clients.
- Dettes fournisseurs.
- Consignations en circulation.
- Dépenses.
- Bilan de caisse.

Permettre les exports PDF et Excel.

Les rapports financiers doivent distinguer le chiffre d'affaires, les encaissements, les dettes et les dépenses.

---

# 21. MODULE PARAMÈTRES ET PERSONNALISATION AVANCÉE

Créer un véritable centre de configuration.

## Identité du dépôt

Permettre de personnaliser :

- Nom commercial.
- Raison sociale.
- Logo.
- Adresse.
- Téléphone.
- Email.
- Ville.
- Pays.
- Devise.
- Identifiant fiscal.
- Informations légales.

## Personnalisation de l'interface

Permettre :

- Changement du logo.
- Changement du nom affiché.
- Couleur principale.
- Couleur secondaire.
- Mode clair.
- Mode sombre.
- Densité des tableaux.
- Affichage ou masquage des éléments de navigation.
- Préférences d'impression.

## Paramètres commerciaux

- Devise par défaut : FCFA.
- Séparateurs de milliers.
- Nombre de décimales.
- Taux de taxe configurable.
- Prix TTC ou HT.
- Remises autorisées.
- Prix de gros.
- Prix de demi-gros.
- Prix de détail.
- Conditions de crédit.
- Plafonds clients.
- Seuils de stock.
- Frais de livraison.

Ne jamais coder en dur les règles commerciales modifiables.

## Numérotation automatique

Configurer les préfixes :

- FAC-2026-00001.
- VTE-2026-00001.
- ACH-2026-00001.
- CMD-2026-00001.
- BL-2026-00001.
- REC-2026-00001.

Assurer l'unicité des numéros, même en cas d'opérations concurrentes.

## Sauvegardes

Permettre :

- Sauvegarde manuelle.
- Sauvegarde automatique.
- Sauvegarde quotidienne.
- Restauration.
- Choix du dossier de sauvegarde.
- Historique des sauvegardes.
- Vérification de l'intégrité.

Ne jamais écraser la seule sauvegarde valide sans confirmation.

---

# 22. UTILISATEURS, RÔLES ET SÉCURITÉ

Créer un système d'authentification.

Rôles initiaux :

- Administrateur.
- Gérant.
- Caissier.
- Magasinier.
- Commercial.
- Livreur.
- Comptable.

Permissions granulaires :

- Consulter.
- Créer.
- Modifier.
- Valider.
- Annuler.
- Supprimer.
- Exporter.
- Imprimer.
- Consulter les rapports financiers.
- Modifier les paramètres.

Un caissier ne doit pas pouvoir modifier les paramètres financiers sans autorisation.

Enregistrer les actions sensibles dans un journal d'audit.

Sécurité obligatoire :

- Mots de passe hachés.
- Sessions sécurisées.
- Validation serveur des entrées.
- Protection contre les injections SQL.
- Protection contre les modifications non autorisées.
- Journalisation des erreurs.
- Pas de mots de passe en clair.
- Pas de suppression physique des écritures financières validées.

Prévoir une procédure de première installation permettant de créer le compte administrateur.

Ne pas utiliser de compte administrateur avec mot de passe universel intégré au logiciel.

---

# 23. RÈGLES MÉTIER ET INTÉGRITÉ DES DONNÉES

Ces règles sont non négociables.

1. Une vente validée doit modifier le stock une seule fois.
2. Une réception fournisseur doit augmenter le stock une seule fois.
3. Une commande fournisseur non réceptionnée ne modifie pas le stock.
4. Un paiement partiel doit diminuer le solde dû sans effacer la facture.
5. Un retour client doit générer une opération de retour traçable.
6. Un retour de consigne doit mettre à jour les quantités physiques et les soldes concernés.
7. Une annulation doit produire des écritures inverses traçables.
8. Une clôture de caisse ne doit pas être modifiable par un utilisateur non autorisé.
9. Les numéros de documents doivent être uniques.
10. Les données historiques doivent rester consultables.
11. Les montants financiers doivent utiliser Decimal et non les nombres flottants.
12. Les opérations multi-tables doivent utiliser des transactions SQL.
13. Les quantités doivent supporter les conversions de conditionnement.
14. Les écritures validées ne doivent pas être supprimées silencieusement.
15. Les opérations doivent conserver l'identité de leur auteur.

Adopter une logique de registre pour les mouvements de stock, les paiements et les consignations.

Les soldes affichés doivent pouvoir être rapprochés de leurs écritures sources.

---

# 24. INITIALISATION ET DONNÉES DE DÉMONSTRATION

Lors du premier démarrage :

- Créer la base SQLite.
- Exécuter les migrations.
- Créer les paramètres initiaux.
- Créer les catégories.
- Configurer la devise.
- Initialiser les moyens de paiement.
- Proposer la création du premier administrateur.

Proposer un jeu de démonstration facultatif comprenant :

- Produits de boissons réalistes.
- Plusieurs catégories.
- Fournisseurs.
- Clients.
- Stocks.
- Historique de quelques ventes.

Ne jamais insérer automatiquement des données fictives dans une base commerciale existante.

Prévoir un mode démonstration distinct du mode production.

---

# 25. PERFORMANCE ET FIABILITÉ

L'application doit fonctionner correctement sur un ordinateur de bureau standard.

Exigences :

- Démarrage rapide.
- Navigation fluide.
- Requêtes SQL optimisées.
- Pagination des tableaux.
- Recherche performante.
- Chargement différé des données volumineuses.
- Gestion des erreurs sans fermeture brutale.
- Transactions sécurisées.
- Aucun blocage de l'interface pendant les exports.
- Fermeture propre de la base à la sortie.

Activer les mécanismes SQLite adaptés :

- Foreign keys.
- WAL lorsque compatible avec le contexte.
- Busy timeout.
- Index.
- Transactions.

Prévoir un verrouillage adapté pour les écritures concurrentes.

Ne jamais partager une même session SQLAlchemy entre plusieurs opérations concurrentes.

---

# 26. MODE HORS LIGNE

L'application doit être totalement autonome et fonctionner sans connexion Internet.

Aucun service cloud ne doit être indispensable.

Les fonctionnalités suivantes doivent rester disponibles hors ligne :

- Ventes.
- Achats.
- Stocks.
- Clients.
- Fournisseurs.
- Caisse.
- Créances.
- Dettes.
- Consignations.
- Documents PDF.
- Rapports.
- Sauvegardes.

Afficher dans la sidebar :

« Mode hors ligne — Données stockées localement ».

Ne pas afficher un état de connexion Internet fictif.

---

# 27. EMPAQUETAGE WINDOWS ET MACOS

Préparer la distribution sous forme :

- Windows : fichier .exe ou installateur.
- macOS : application .app et image .dmg.

Utiliser NiceGUI et pywebview.

Le lancement doit respecter :

```python
if __name__ in {"__main__", "__mp_main__"}:
    multiprocessing.freeze_support()
    ui.run(native=True, reload=False)
```
