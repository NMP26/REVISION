# Migration

`MIGRATE.sh` est le point d'entrée prévu pour une migration complète.

- `--check` vérifie les prérequis.
- `--install` démarre les services, applique les migrations et vérifie la santé.
- `--migrate` applique les migrations.
- `--verify` lance le diagnostic.
- `--restore` exige un backup explicite et reste bloqué en LOT 0.
- `--rollback` reste explicitement non opérationnel jusqu'à la première release qualifiée.

## Règles production

`make migrate` crée d'abord un backup PostgreSQL non vide, puis exécute
`python manage.py migrate --noinput`. Les migrations Django sont donc
appliquées incrémentalement; aucune commande de migration ne doit supprimer
ou recréer la base.

Une migration destructive (suppression de table/colonne, perte de données,
ou transformation irréversible) est interdite sans validation explicite
préalable, analyse d'impact, backup vérifié et plan de restauration approuvé.
Les scripts normaux n'utilisent jamais `docker compose down -v` et ne
suppriment jamais automatiquement le volume `revision-prix-postgres-data`.
