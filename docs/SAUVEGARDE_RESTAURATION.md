# Sauvegarde et restauration — état provisoire

Les scripts actuels sont décrits dans le README. `scripts/create_backup.py` utilise
l'API SQLite et contrôle `integrity_check` ; les sauvegardes incluent les données
validées présentes dans le WAL. Tester régulièrement leur restauration sur une
copie. Ce n'est ni une sauvegarde externe, ni une sauvegarde quotidienne automatique.

La restauration par `scripts/restore_backup.py` exige l'arrêt manuel complet et
une confirmation, contrôle l'intégrité et les noms des tables et colonnes, puis
crée une sauvegarde de sécurité. Ces contrôles ne valident pas l'ensemble des
contraintes ni l'adéquation métier. Elle refuse par défaut les schémas différents. Le retour arrière interversions
est possible avec une option explicite ; voir `docs/MIGRATIONS.md`. Ne pas copier un fichier SQLite à chaud avec son WAL.

Les sauvegardes historiques peuvent contenir les anciens PIN en clair : les
protéger comme des données sensibles. Le PIN ne chiffre pas la base.

Mise à jour phase 1 : le retour arrière interversions est possible uniquement avec
l'option explicite `--schema-different`, après arrêt et sauvegarde. Elle contourne
la comparaison des tables/colonnes ; elle ne valide pas la compatibilité du schéma.
Consultez `docs/MIGRATIONS.md` avant utilisation.

## Images des produits

Les sauvegardes SQLite actuelles ne contiennent **pas** les fichiers d'images du
dossier `~/DepotPro_Data/Images`. Copier séparément ce dossier, application arrêtée,
avec la sauvegarde de la base. Les anciennes images sont conservées lors d'un
remplacement ou d'un retrait pour éviter de casser les anciennes sauvegardes. Une
sauvegarde intégrée base + images reste à développer et tester.
