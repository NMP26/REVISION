# Backup et restauration

`make backup` crée un répertoire horodaté dans `backups/` avec un dump
`pg_dump` au format custom, les migrations, les métadonnées de version et
les sommes SHA-256.

Le backup doit être exécuté avant chaque déploiement ou migration. Le script
échoue si le dump PostgreSQL est vide; vérifier ensuite `sha256sum -c
backups/<timestamp>/SHA256SUMS` et conserver le répertoire hors du cycle de
vie des conteneurs. Les médias persistants (`revision-prix-media`) doivent
également être sauvegardés selon la politique d'exploitation de l'hôte.

La restauration est bloquée par défaut dans le LOT 0 et doit faire l'objet
d'une procédure approuvée avec contrôle d'impact. Elle n'est jamais exécutée
automatiquement et aucune restauration n'est effectuée pendant un déploiement
normal.

## Procédure documentée et testable

1. Identifier le backup approuvé et vérifier son `SHA256SUMS`.
2. Arrêter l'application selon la fenêtre d'exploitation approuvée, sans
   supprimer le volume PostgreSQL.
3. Restaurer dans une base de restauration isolée avec `pg_restore` pour
   tester le dump; ne jamais écraser la production sans validation explicite.
4. Pour une restauration production autorisée, utiliser uniquement
   `make restore BACKUP=backups/<timestamp>` après validation écrite et
   contrôle d'impact; le script reste bloqué par défaut dans le LOT 0.
5. Relancer les services, vérifier les migrations, la santé et les comptages
   métier attendus, puis consigner le résultat.
