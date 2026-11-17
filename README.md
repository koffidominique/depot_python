# DEPOTPRO ERP

Application de bureau professionnelle pour la gestion de dépôt de boissons.

## Fonctionnalités

- Tableau de bord avec indicateurs clés de performance
- Gestion complète des produits et catégories
- Suivi des stocks avec alertes de stock bas
- Gestion des ventes et des factures
- Gestion des clients et des dettes
- Gestion des fournisseurs et des commandes
- Gestion de la caisse
- Rapports et analyses
- Authentification et gestion des utilisateurs
- Sauvegarde et restauration des données

## Installation

1. Installer les dépendances:

```bash
pip install -r requirements.txt
```

2. Initialiser la base de données:

```bash
python init_db.py
```

3. Lancer l'application:

```bash
python main.py
```

## Identifiants par défaut

- Nom d'utilisateur: `admin`
- Mot de passe: `admin123`

## Structure du projet

```
new_depo/
├── main.py                 # Point d'entrée de l'application
├── config.py               # Configuration de l'application
├── database.py             # Configuration de la base de données
├── theme.py                # Thème et styles UI
├── init_db.py              # Script d'initialisation de la BDD
├── models/                 # Modèles SQLAlchemy
├── services/               # Couche de services métier
├── pages/                  # Pages UI de l'application
├── components/             # Composants UI réutilisables
└── requirements.txt        # Dépendances Python
```
