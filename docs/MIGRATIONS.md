# Migrations — procédure et limites

L'ancienne révision Alembic est bloquée ; ne pas la débloquer. Le script dédié est
manuel et ne s'exécute pas automatiquement sur une installation existante.

## Préparation

1. Arrêter DEPOTPRO et tous les logiciels accédant au fichier SQLite.
2. Identifier `~/DepotPro_Data/depot.db` et faire une sauvegarde externe vérifiée.
3. Tester la procédure sur une copie de la base, puis exécuter :

```
python scripts/migrate_database.py --application-arretee
```

Le script vérifie l'intégrité, les clés étrangères et la présence des tables et
colonnes connues, puis verrouille les écritures, crée un instantané SQLite cohérent
avec le WAL et le vérifie. Il applique dans une transaction les versions :

- 1 : journal `depotpro_schema_migrations` ;
- 2 : configuration propriétaire `owner_security` et effacement des valeurs des
  anciens PIN dans `users.pin_code`, sans suppression d'utilisateurs ni d'historiques.

Le script vérifie à nouveau l'intégrité et annule la transaction en cas d'erreur.
La répétition est sans effet ; une version inconnue ou un schéma incomplet est
refusé. Au redémarrage, le propriétaire crée un nouveau PIN à six chiffres. Les
anciennes valeurs peuvent subsister dans les sauvegardes et les anciens journaux
SQLite : protégez ces fichiers et contrôlez leur rétention. Le script n'effectue
pas d'effacement sécurisé des blocs physiques, copies, journaux ou sauvegardes.

Une base neuve créée par `init_db.py` reçoit les mêmes versions. Une base déjà
existante non migrée est refusée au lancement, sans `create_all` ni modification.
La vérification des colonnes ne garantit pas la compatibilité complète des types,
index, contraintes et données métier : il faut examiner les bases particulières.
Les anciennes colonnes monétaires `NUMERIC` ne sont pas converties.

## Retour arrière interversions

Une restauration revient à l'état de la sauvegarde : toutes les opérations faites
depuis sont perdues dans la base active, même si une copie de sécurité est conservée.
Arrêter tous les accès, choisir une sauvegarde et examiner sa date. Pour autoriser
explicitement un schéma différent :

```
python scripts/restore_backup.py /chemin/vers/sauvegarde.db --application-arretee --schema-different
```

La commande vérifie l'intégrité et les tables principales, sauvegarde la base
actuelle et utilise l'API SQLite. L'option autorise les différences de schéma : elle
ne démontre pas la compatibilité de la sauvegarde. Le retour à une ancienne base
restaure aussi ses anciens PIN ; le prochain démarrage exigera une nouvelle
migration. Tester sur copies avant toute restauration réelle.

## Version 3 — conditionnements

La migration 3 ajoute uniquement `product_packagings`, ses contraintes et son index.
Elle n'ajoute aucun prix, conditionnement ni coefficient aux produits historiques.
La base version 2 doit être migrée manuellement avec la même commande ci-dessus ;
une sauvegarde préalable est créée et vérifiée. Elle conserve le PIN déjà configuré.
Le retour arrière nécessite `--schema-different` et perd les opérations ultérieures :
la sauvegarde de l'état courant est conservée. Tester d'abord sur une copie.

## Version 4 — coût moyen exact

La migration 4 ajoute deux colonnes facultatives au produit : numérateur et
dénominateur du coût moyen rationnel. Les champs sont initialement vides, sans
reprise du prix d'achat de référence ni invention de coût. Comme pour les versions
précédentes, arrêter les accès, vérifier une sauvegarde et lancer la commande
manuelle ; la migration crée également une sauvegarde SQLite vérifiée. Le calcul
pondéré à partir des réceptions et son coût historique de vente restent à développer.
Les images sont des fichiers séparés et ne figurent pas dans cette sauvegarde SQLite.

## Version 5 — réceptions et inventaires (phase 3 en cours)

La migration ajoute les tables d'inventaire et de réception ainsi que les colonnes
d'instantané du conditionnement sur les lignes d'achat. Elle ne déduit aucun
conditionnement pour les anciennes lignes : leur réception automatique est refusée.
Elle crée une sauvegarde SQLite vérifiée avant toute modification et s'exécute
manuellement, application arrêtée, avec la commande décrite plus haut. Testée sur
des bases temporaires uniquement, aucune base réelle n'a été migrée. Les images
restent à sauvegarder séparément. Tester toute migration sur une copie d'abord.

## Version 6 — achats et dettes fournisseurs

La version 6 ajoute la remise et les frais unitaires figés sur les lignes d'achat,
le lien entre réception et dette fournisseur et le statut de rattachement à la
caisse d'un paiement. Les valeurs historiques restent NULL : aucune remise, aucun
frais, ni aucun rattachement n'est supposé. Les anciennes lignes sans ces données
ne sont pas réceptionnables automatiquement ; les dettes historiques sans lien
fiable à une réception restent consultables, mais ne sont pas réglables par ce
nouveau service. Il faut les rapprocher manuellement lors d'un chantier ultérieur.
La migration est manuelle, application arrêtée, avec sauvegarde SQLite vérifiée ;
les images restent séparées. Testée sur copies temporaires puis sur la base de
l'aperçu, après arrêt de celui-ci ; sauvegarde locale créée avant migration.

## Version 7 — catalogue d'emballages physiques

La migration 7 ajoute la table indépendante `returnable_packaging_types` ; elle
ne modifie ni les produits et leurs conditionnements commerciaux, ni les stocks,
ni les consignes historiques. Aucun emballage, tarif, compatibilité ou solde ne
sont créés automatiquement. La valeur de consigne peut être inconnue (NULL), ce
qui diffère d'une valeur explicitement nulle. La migration est manuelle,
application arrêtée, et crée une sauvegarde SQLite vérifiée au préalable ; les
images restent à sauvegarder séparément. Testée sur bases temporaires et appliquée
à la base de l'aperçu après son arrêt. Pour une base existante, tester d'abord sur
une copie et suivre la procédure de sauvegarde et migration ci-dessus.

## Version 8 — journal manuel des emballages vides

La migration 8 ajoute deux tables, les soldes explicitement déclarés de vides et
leurs mouvements. Elle ne crée aucun solde initial ni mouvement à partir des
produits, achats ou anciennes consignes ; l'absence de solde signifie « non
déclaré », pas zéro. Migration manuelle après arrêt de l'application et sauvegarde
SQLite vérifiée ; les images sont toujours à sauvegarder séparément. Testée sur
bases temporaires et appliquée à la base de l'aperçu après son arrêt, avec une
sauvegarde préalable. Tester toute migration d'une autre base sur une copie.

## Version 9 — caisse des nouveaux règlements fournisseurs

La migration 9 ajoute des tables indépendantes pour les sessions de caisse et les
écritures de décaissement fournisseurs liées à un paiement. Elle ne modifie pas les
anciennes sessions, les paiements historiques ou leur statut « hors caisse » et ne
reconstruit aucun lien financier. Toute ancienne caisse ouverte bloque une nouvelle
ouverture jusqu'à rapprochement manuel. Exécuter application arrêtée après sauvegarde
vérifiée et test sur copie ; les images sont à sauvegarder séparément. La base de
l'aperçu a été migrée après arrêt et sauvegarde préalable.

## Version 10 — ventes au comptant et mouvements complémentaires

La migration 10 ajoute des tables séparées pour les nouvelles ventes au comptant,
leurs lignes et les mouvements de caisse complémentaires. Les ventes historiques,
dépenses historiques, règlements fournisseurs et sessions existantes sont conservés
sans être réinterprétés ou rattachés automatiquement. Les nouvelles ventes ne sont
pas intégrées aux anciens rapports et ne constituent pas une migration de l'ancien
module. Sauvegarder SQLite et les images séparément, arrêter tous les accès et tester
la migration sur une copie. La base de l'aperçu a été migrée après arrêt et sauvegarde
vérifiée.
