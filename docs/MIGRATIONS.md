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

## Version 11 — unicité inter-tables des codes-barres

Quatre déclencheurs SQLite empêchent les insertions et modifications de codes-barres
identiques entre produits et conditionnements, actifs ou archivés. Les index
uniques de chaque table et les déclencheurs sont vérifiés au démarrage. La migration
n'efface, ne renomme et ne fusionne aucun code-barres : si une collision existe,
elle est annulée après création de la sauvegarde et exige un diagnostic humain.
Les comparaisons portent sur les valeurs exactement stockées ; les services
normalisent les espaces avant enregistrement. Modifier le schéma ou supprimer les
protections directement contourne ces garanties et le démarrage le refuse.

Pour une base existante, arrêter tous les accès, sauvegarder également les images,
auditer et tester d'abord la migration et la restauration sur une copie ; exécuter
ensuite `python scripts/migrate_database.py --application-arretee` seulement après
validation. Essais réalisés sur bases temporaires uniquement : aucune base
commerciale n'a été migrée. Les sauvegardes créées par la migration restent au
même emplacement que la base ; les protéger car elles peuvent contenir des PIN
historiques en clair.

## Version 12 — liens des paiements mixtes au comptant

La migration ajoute `managed_sale_payments`, table reliant chaque mouvement de
caisse d'un paiement mixte à sa vente. Elle n'altère ni ne reconstruit les ventes
ou paiements historiques. Les ventes antérieures réglées en un moyen conservent
leur lien direct existant. Aucune dette, consigne ou annulation n'est créée.
La procédure reste manuelle, tous les accès arrêtés, après sauvegarde vérifiée de
la base et des images et essai de migration puis restauration sur une copie ; la
migration produit en outre une sauvegarde SQLite préalable. Testée uniquement sur
bases temporaires, pas sur une base commerciale réelle.

## Version 13 — annulations totales de ventes au comptant

Ajoute les tables `managed_sale_cancellations` et `managed_sale_refunds`, qui
conservent l'annulation et les liens entre encaissements initiaux et remboursements.
Aucune vente historique n'est annulée ni reconstruite automatiquement. La
migration est manuelle, application et autres accès arrêtés, avec sauvegarde
SQLite préalable ; sauvegarder aussi les images séparément, puis essayer migration
et restauration sur une copie avant toute intervention réelle. Vérifiée uniquement
sur bases temporaires, sans migration d'une base commerciale.

## Version 14 — nouveau circuit de crédit client

Ajoute les profils de crédit explicites, les créances liées aux nouvelles ventes et
les règlements liés aux mouvements de caisse. Aucun profil, solde ni créance n'est
créé à partir des données historiques. La migration est manuelle, application et
autres accès arrêtés ; sauvegarder base et images, tester migration et restauration
sur une copie et vérifier le résultat avant toute intervention réelle. Une
sauvegarde SQLite préalable est aussi créée par le script. Essais uniquement sur
bases temporaires : aucune base commerciale n'a été migrée.

## Version 15 — retours partiels de vente

Ajoute les tables de retours, lignes retournées et liens aux mouvements de
remboursement. Aucune vente, créance ou consigne antérieure n'est modifiée ou
reconstruite. Arrêter tous les accès, sauvegarder base et images, puis tester la
migration et la restauration sur une copie avant toute migration réelle. Le
script crée aussi une sauvegarde SQLite préalable. Validation sur bases temporaires
uniquement ; aucune base commerciale n'a été migrée.

## Version 16 — contrepassation de retours

Ajoute les tables d'annulation de retour et les liens aux mouvements de reprise
des remboursements. Elle ne modifie aucun retour existant, ne crée pas de
contre-écriture automatique et ne raccorde pas les consignes. Arrêter tous les
accès, sauvegarder base et images, puis tester migration et restauration sur une
copie avant toute migration réelle. Le script crée aussi une sauvegarde SQLite
préalable. Validation sur bases temporaires uniquement ; aucune base commerciale
n'a été migrée.

## Version 17 — configuration des emballages consignés

Ajoute les tables de déclaration « sans consigne » / « avec consigne » et de
composition physique par conditionnement. La migration ne remplit aucune
configuration et ne déduit aucune équivalence ou valeur de l'historique. En
conséquence, chaque conditionnement existant doit être vérifié et configuré avant
vente ; les ventes avec consigne restent bloquées, faute d'écritures intégrées.
Application arrêtée, sauvegarde vérifiée de la base et des images séparément,
essai de migration et restauration sur copie avant tout traitement réel. Le
script crée en outre une sauvegarde SQLite préalable. Testée uniquement sur bases
temporaires : aucune base commerciale n'a été migrée.

## Version 18 — ventes et retours de consignes

Ajoute les écritures de consigne client, retours de vides et liens aux remboursements. Aucun historique ni stock initial n'est reconstruit. Les configurations v17 restent à renseigner ; les ventes consignées sont désormais prises en charge dans le nouveau circuit. Avant migration réelle : arrêter l'application, sauvegarder et vérifier la base et les images séparément, puis tester migration et restauration sur une copie. Le script crée aussi une sauvegarde SQLite préalable. Migration testée uniquement sur bases temporaires, sans migration commerciale dans cette session.

## Version 19 — catalogue des moyens de paiement

Crée un catalogue local, initialisé avec les moyens techniques déjà reconnus par le circuit précédent ; aucune transaction n'est modifiée. Les nouveaux moyens sont créés dans les paramètres. Un renommage crée une nouvelle version et conserve l'ancien code et son libellé pour les écritures existantes ; les flux des deux versions restent distincts. Le moyen espèces demeure actif et immuable. Une désactivation empêche les nouvelles saisies mais ne bloque pas les contreparties d'opérations existantes. La migration a été testée sur bases temporaires, avec sauvegarde SQLite et conservation d'une vente synthétique ; aucune base commerciale n'a été migrée. Avant toute migration réelle : arrêter l'application, vérifier la sauvegarde de la base et des images séparément, puis tester migration et restauration sur une copie.

## Version 20 — annulation des retours de vides

Ajoute les tables de contrepassation et de liens aux reprises des remboursements. Aucune écriture antérieure n'est modifiée ; aucune contrepassation n'est créée automatiquement. Avant migration réelle : arrêter l'application, sauvegarder et vérifier la base et les images séparément, puis tester migration et restauration sur une copie. La migration et sa sauvegarde ont été testées sur base synthétique, pas sur une base commerciale.
