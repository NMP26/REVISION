# Décisions techniques — RevisionPrix

## 2026-09-16 — LOT 0 / PHASE 1

- Le Blueprint local `/opt/revision-prix/BLUEPRINT.md` est la source de vérité.
- La fondation est limitée à Django, React/Vite/Tailwind, Nginx applicatif et PostgreSQL.
- Aucun modèle métier de révision des prix n'est implémenté dans ce lot.
- Le projet Compose est nommé `revision-prix`.
- Le réseau Docker dédié est `revision-prix-internal`; aucun conteneur existant n'y est connecté. Il n'est pas marqué `internal` car Docker 29.6.1 sur ce serveur ne publie pas correctement un port loopback depuis un bridge `internal`; l'isolation est assurée par l'absence de connexions externes et l'absence de ports publiés pour le backend/PostgreSQL.
- PostgreSQL utilise le volume `revision-prix-postgres-data` et aucun port hôte publié.
- Le frontend est le seul service publié, exclusivement sur `127.0.0.1:12701`.
- Le backend est accessible par DNS Docker (`revision-prix-backend`) et n'a pas de port hôte publié.
- Le proxy `/api/` est assuré par le Nginx applicatif vers `http://revision-prix-backend:8000`.
- Les versions d'images et de dépendances sont explicitement verrouillées; aucun tag `latest` n'est utilisé.
- Les secrets résident dans `.env`, non versionné; `.env.example` ne contient que des placeholders.
- `make push-images`, `make release`, `make deploy` et `make rollback` échouent explicitement tant qu'un registry et une procédure de release ne sont pas configurés.
- Les règles réglementaires et le métier de calcul sont reportés aux lots ultérieurs.
