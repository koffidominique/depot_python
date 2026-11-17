# Sécurité locale

Le PIN à six chiffres est haché avec bcrypt et aucun PIN par défaut n'est créé.
Trois essais erronés déclenchent une temporisation progressive persistée en base
(jusqu'à cinq minutes) ; les essais réussis remettent le compteur à zéro. Les
paramètres permettent de changer le PIN avec le PIN actuel et de régler l'inactivité
entre 1 minute et 24 heures. Le verrouillage d'inactivité dépend des événements
transmis par l'interface ; il ne remplace pas le verrouillage du système d'exploitation.
Le PIN protège l'accès à l'interface et **ne chiffre pas SQLite**. Protégez le compte
système, les sauvegardes et l'accès physique ; les sauvegardes anciennes peuvent
encore contenir des PIN historiques en clair.

## PIN oublié

Aucun code maître ou procédure de contournement n'est fourni. Arrêter l'application,
préserver une sauvegarde vérifiée et contacter la personne chargée de l'assistance
locale. Une procédure sûre de vérification d'identité du propriétaire n'a pas encore
été définie ; aucune réinitialisation ne doit être effectuée avant cette décision.
