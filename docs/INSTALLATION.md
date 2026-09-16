# Installation LOT 0

1. Générer `.env` à partir de `.env.example` avec des valeurs secrètes locales.
2. Exécuter `./MIGRATE.sh --check`.
3. Exécuter `make build`, puis `make up` et `make migrate`.
4. Vérifier avec `make doctor`.

Le frontend est publié uniquement sur `127.0.0.1:12701`. Le backend et
PostgreSQL ne publient aucun port hôte. Nginx système et Certbot ne sont
pas modifiés par le LOT 0.
