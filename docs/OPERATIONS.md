# Opérations

Commandes usuelles : `make status`, `make logs`, `make doctor`, `make test`,
`make backup`, `make down`, `make up`.

Le projet utilise le réseau Docker `revision-prix-internal` et le volume
PostgreSQL `revision-prix-postgres-data`, ainsi que le volume média
`revision-prix-media` monté sur `/app/media` dans le backend. Un volume n'est
pas une sauvegarde.

## Règle de gouvernance production

Les données saisies en production sont persistantes. Un déploiement, rebuild,
upgrade ou migration ne doit jamais entraîner leur suppression ou leur
réinitialisation.

Les opérations normales utilisent `docker compose down` sans `-v`; aucune
commande normale ne supprime un volume, ne recrée la base ou ne réinitialise
les données. Avant chaque migration ou déploiement, un backup PostgreSQL
non vide et vérifié est obligatoire. Les migrations Django sont appliquées
incrémentalement avec `make migrate`. Toute migration destructive future
requiert une validation explicite documentée avant exécution.

Un test de persistance autorisé et non destructif consiste à relever les
comptages/identifiants, exécuter `docker compose down` puis `docker compose up
-d`, et vérifier les mêmes valeurs. Ne jamais utiliser `docker compose down -v`
en production.
