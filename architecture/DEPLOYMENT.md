STATUS: DRAFT
SOURCE: pending governance specification

# Déploiement

Gabarit réservé à la description d'architecture validée du déploiement.

## Gouvernance de livraison

GitHub `NMP26/REVISION` est la source officielle du code versionné.
Les lots sont livrés par étapes contrôlées, avec tests, traçabilité,
revue, commit et version. Les secrets, dumps et données persistantes
restent hors dépôt.

## Persistance des données de production

Les données saisies en production sont persistantes. Un déploiement, rebuild,
upgrade ou migration ne doit jamais entraîner leur suppression ou leur
réinitialisation.

PostgreSQL utilise le volume Docker nommé `revision-prix-postgres-data` et
les fichiers médias applicatifs utilisent `revision-prix-media` monté sur
`/app/media`. Le remplacement des conteneurs backend/frontend ne doit jamais
remplacer ces volumes.

Chaque déploiement ou migration suit cette séquence obligatoire : backup
PostgreSQL non vide et vérifié, contrôle des migrations, application
incrémentale, vérification de santé et preuve de persistance. Les scripts
normaux n'exécutent jamais `docker compose down -v`, ne suppriment jamais
automatiquement un volume et ne recréent jamais la base. Toute migration
destructive future exige une validation explicite documentée avant exécution.
