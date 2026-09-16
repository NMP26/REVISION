# Migration

`MIGRATE.sh` est le point d'entrée prévu pour une migration complète.

- `--check` vérifie les prérequis.
- `--install` démarre les services, applique les migrations et vérifie la santé.
- `--migrate` applique les migrations.
- `--verify` lance le diagnostic.
- `--restore` exige un backup explicite et reste bloqué en LOT 0.
- `--rollback` reste explicitement non opérationnel jusqu'à la première release qualifiée.
