# RÈGLES MÉTIER PRIORITAIRES - DEPOTPRO ERP

## 1. FLUX OPÉRATIONNELS CONFIRMÉS

### 1.1 Flux de vente

```
Étapes obligatoires :
1. Sélection du client (comptant ou crédit)
2. Recherche des produits par nom/code-barres
3. Ajout au panier avec quantité et prix
4. Calcul automatique du total (marchandises + consignes)
5. Sélection du mode de paiement
6. Validation de la vente
7. Déduction automatique du stock
8. Enregistrement des mouvements de stock
9. Création de la facture et du reçu PDF
10. Mise à jour des créances si paiement à crédit
```

**Règles de validation :**

- Vente non validée = pas de modification du stock
- Vente annulée = mouvement de stock inverse traçable
- Vente partiellement payée = solde restant enregistré comme créance

### 1.2 Flux d'achat

```
Étapes obligatoires :
1. Création du bon de commande fournisseur
2. Sélection des produits et quantités
3. Validation du bon de commande
4. Impression/envoi du bon
5. Réception partielle ou totale des marchandises
6. Vérification des écarts commandé/reçu
7. Mise à jour du stock UNIQUEMENT à la réception
8. Enregistrement de la dette fournisseur
9. Paiement partiel ou total
```

**Règles de validation :**

- Bon de commande = pas de modification du stock avant réception
- Réception partielle = stock augmenté uniquement pour les quantités reçues
- Écarts = enregistrés avec motif justificatif

### 1.3 Flux de paiement

```
Étapes obligatoires :
1. Sélection de la facture/dette à régler
2. Saisie du montant payé
3. Sélection du mode de paiement
4. Enregistrement du paiement
5. Génération du reçu PDF
6. Mise à jour du solde de la créance/dette
7. Mise à jour du solde de caisse
```

**Règles de validation :**

- Paiement partiel = solde restant conservé
- Paiement multiple = plusieurs modes de paiement autorisés
- Reçu généré systématiquement

### 1.4 Flux de retour client

```
Étapes obligatoires :
1. Sélection de la vente d'origine
2. Sélection des produits retournés
3. Saisie des quantités retournées
4. Motif du retour
5. Validation du retour
6. Réintégration du stock
7. Génération de l'avoir
8. Mise à jour de la créance client
```

**Règles de validation :**

- Retour = mouvement de stock positif traçable
- Avoir = document distinct de la facture
- Retour partiel = ligne par ligne

### 1.5 Flux de clôture de caisse

```
Étapes obligatoires :
1. Ouverture de caisse avec fond initial
2. Enregistrement des encaissements/décaissements
3. Saisie du montant physique en fin de journée
4. Calcul automatique des totaux théoriques
5. Comparaison théorique vs physique
6. Enregistrement des écarts avec motif
7. Validation de la clôture
8. Génération du rapport PDF
```

**Règles de validation :**

- Clôture = non modifiable après validation
- Écarts = enregistrés systématiquement
- Rapport = généré systématiquement

---

## 2. RÈGLES MÉTIER FIXÉES

### 2.1 Règles de crédit

- Plafond de crédit configurable par client
- Vente à crédit interdite si plafond dépassé
- Délai de paiement configurable par client
- Alertes de retard de paiement
- Créances = traçables par facture

### 2.2 Règles de stock négatif

- Stock négatif INTERDIT par défaut
- Autorisation exceptionnelle = paramètre global dans paramètres avancés
- Stock négatif = alerte enregistrée dans le journal d'audit
- Stock = toujours positif sauf autorisation explicite

### 2.3 Règles de tarification

- 3 niveaux de prix par produit : gros, demi-gros, détail
- Prix personnalisé par client = autorisé selon permissions
- Remises = autorisées selon permissions
- Prix = modifiables uniquement par rôles autorisés
- Historique des modifications de prix = conservé

### 2.4 Règles de consigne

- Consigne = montant séparé du prix produit
- Suivi individuel par client : quantités sorties/reçues/restantes
- Retour de consigne = mouvement distinct des paiements
- Valeur consigne = configurable par type d'emballage
- Alertes de consignes en circulation

### 2.5 Règles de numérotation des documents

- Format : `PREFIX-ANNEE-NUMERO`
- Exemples :
  - FAC-2026-00001 (Facture)
  - VTE-2026-00001 (Vente)
  - ACH-2026-00001 (Achat)
  - CMD-2026-00001 (Commande)
  - BL-2026-00001 (Bon de livraison)
  - REC-2026-00001 (Reçu)
- Numéros = uniques et séquentiels
- Préfixes = configurables dans paramètres avancés

---

## 3. PERMISSIONS PAR RÔLE

| Fonctionnalité                   | Administrateur | Gérant | Caissier | Magasinier | Commercial | Livreur | Comptable |
| -------------------------------- | -------------- | ------ | -------- | ---------- | ---------- | ------- | --------- |
| **Consultation tableau de bord** | ✅             | ✅     | ✅       | ✅         | ✅         | ❌      | ✅        |
| **Gestion produits**             | ✅             | ✅     | ❌       | ✅         | ❌         | ❌      | ❌        |
| **Gestion stocks**               | ✅             | ✅     | ❌       | ✅         | ❌         | ❌      | ❌        |
| **Ventes**                       | ✅             | ✅     | ✅       | ❌         | ✅         | ❌      | ❌        |
| **Annulation vente**             | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ❌        |
| **Achats**                       | ✅             | ✅     | ❌       | ✅         | ❌         | ❌      | ❌        |
| **Réceptions**                   | ✅             | ✅     | ❌       | ✅         | ❌         | ❌      | ❌        |
| **Paiements**                    | ✅             | ✅     | ✅       | ❌         | ❌         | ❌      | ✅        |
| **Clôture caisse**               | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ✅        |
| **Gestion clients**              | ✅             | ✅     | ❌       | ❌         | ✅         | ❌      | ❌        |
| **Gestion fournisseurs**         | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ❌        |
| **Livraisons**                   | ✅             | ✅     | ❌       | ❌         | ❌         | ✅      | ❌        |
| **Consignations**                | ✅             | ✅     | ✅       | ✅         | ✅         | ✅      | ❌        |
| **Dépenses**                     | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ✅        |
| **Inventaires**                  | ✅             | ✅     | ❌       | ✅         | ❌         | ❌      | ✅        |
| **Rapports**                     | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ✅        |
| **Rapports financiers**          | ✅             | ✅     | ❌       | ❌         | ❌         | ❌      | ✅        |
| **Gestion utilisateurs**         | ✅             | ❌     | ❌       | ❌         | ❌         | ❌      | ❌        |
| **Modification paramètres**      | ✅             | ❌     | ❌       | ❌         | ❌         | ❌      | ❌        |
| **Sauvegarde/restauration**      | ✅             | ❌     | ❌       | ❌         | ❌         | ❌      | ❌        |

---

## 4. CONTRAINTES TECHNIQUES OBLIGATOIRES

1. **Transactions ACID** : Toutes les opérations multi-tables utilisent des transactions SQL
2. **Types décimaux** : Tous les montants financiers utilisent Decimal, pas float
3. **Traçabilité** : Toutes les modifications sont enregistrées avec utilisateur et date
4. **Suppression interdite** : Aucune écriture validée ne peut être supprimée, seulement annulée
5. **Journal d'audit** : Toutes les actions sensibles sont enregistrées
6. **Intégrité référentielle** : Toutes les clés étrangères sont activées
7. **Index** : Index sur tous les champs de recherche
