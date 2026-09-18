STATUS: APPROVED
SOURCE: GOV 1.1 — découpage et critères documentaires

# Plan directeur

Le cycle de gouvernance est :

```text
Besoin
→ exigence
→ validation
→ spec
→ plan du LOT
→ développement
→ migration
→ tests
→ traçabilité
→ revue
→ commit
→ version
→ déploiement
```

Chaque étape doit être documentée avant de permettre l'étape suivante.

## Garde-fous

Le plan du lot autorisé, les exigences approuvées et les critères de
validation doivent exister avant tout développement. Toute ambiguïté
est bloquante jusqu'à décision documentée.

## LOT 1 — lot parent historique

Le LOT 1 reste le lot parent historique du Blueprint. Son exécution est
organisée ainsi :

```text
LOT 1
 ├── LOT 1A — Authentification / Utilisateurs / Sociétés
 └── LOT 1B — Marchés / Lots / Structure contractuelle
```

Le découpage est une précision de gouvernance. Il ne retire aucune
capacité du LOT 1 historique et aucun sous-lot n'est démarré par ce plan.

Les critères détaillés sont dans `plans/LOT-01.md`. Avant les migrations
définitives du LOT 1B, l'agent doit présenter le schéma de données proposé
pour validation.
