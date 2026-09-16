# Règles permanentes du projet

- `BLUEPRINT.md` est la source fonctionnelle principale.
- Lire `BLUEPRINT.md` avant tout développement métier.
- Lire `DECISIONS.md`.
- Lire `ROADMAP.md`.
- Lire `TRACEABILITY.md`.
- Lire le plan du LOT explicitement autorisé.
- Ne développer que le LOT explicitement autorisé.
- Ne jamais inventer une règle métier ou réglementaire.
- Ne jamais supprimer une exigence pour simplifier le code.
- Signaler toute contradiction avant de décider.
- Utiliser `Decimal` pour les calculs financiers.
- Toute nouvelle règle métier doit avoir des tests.
- Les révisions validées seront immuables.
- Ne jamais exposer PostgreSQL publiquement.
- Ne jamais publier de secret.
- Ne jamais commencer le LOT suivant sans autorisation.
- Avant livraison : tests, healthchecks et `make doctor`.
- Mettre à jour la traçabilité au fur et à mesure du développement.
