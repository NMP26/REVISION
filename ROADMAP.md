# Roadmap générale — RevisionPrix

| Phase | Périmètre | Statut |
|---|---|---|
| LOT 0 | Foundation | TERMINE |
| GOV 1.1 + REG V1 | Gouvernance / référentiel traçable et noyau réglementaire | PRÊT À FIGER |
| LOT 1 | Parent historique : identité, sociétés, marchés et structure contractuelle | Découpé en LOT 1A + LOT 1B |
| LOT 1A | Authentification / Utilisateurs / Sociétés | EN COURS — implémentation autorisée |
| LOT 1B | Marchés / Lots / Structure contractuelle | BLOQUE |
| LOT 2A | Formules | BLOQUE |
| LOT 2B | Bordereau | BLOQUE |
| LOT 3 | Exécution / Décomptes | BLOQUE |
| LOT 4 | Moteur de révision | BLOQUE |
| LOT 5 | Validation / Snapshots | BLOQUE |
| LOT 6 | Régularisation | BLOQUE |
| LOT 7 | Documents | BLOQUE |
| LOT 8 | Référentiel officiel | BLOQUE |
| LOT 9 | Production | BLOQUE |

Aucun lot bloqué ne peut être commencé sans autorisation explicite.

Après le gel de GOV V1.1 + REG V1, LOT 1A — Authentification /
Utilisateurs / Sociétés est le prochain lot autorisable.

LOT 1B — Marchés / Lots / Structure contractuelle ne démarre qu'après
validation de LOT 1A, sauf décision de gouvernance ultérieure
explicitement documentée.

## Découpage officiel du LOT 1

LOT 1 reste le lot parent historique du Blueprint. Il est exécuté en deux
sous-lots de gouvernance :

```text
LOT 1
 ├── LOT 1A — Authentification / Utilisateurs / Sociétés
 └── LOT 1B — Marchés / Lots / Structure contractuelle
```

Le découpage 1A/1B précise le LOT 1 ; il ne le supprime pas et ne
constitue pas un démarrage de développement.

Le passage d'un lot exige la validation de ses exigences, specs,
implémentation, migrations éventuelles, tests, contrôles,
traçabilité et documentation.
