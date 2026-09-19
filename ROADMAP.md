# Roadmap générale — RevisionPrix

| Phase | Périmètre | Statut |
|---|---|---|
| LOT 0 | Foundation | TERMINE |
| GOV 1.1 + REG V1 | Gouvernance / référentiel traçable et noyau réglementaire | PRÊT À FIGER |
| LOT 1 | Parent historique : identité, sociétés, marchés et structure contractuelle | Découpé en LOT 1A + LOT 1B |
| LOT 1A | Authentification / Utilisateurs / Sociétés | GELÉ — v0.3.0 |
| LOT 1B | Marchés / Lots / Structure contractuelle | IMPLEMENTED — TESTED, AUDIT À FAIRE |
| LOT 2A | Formules | BLOQUE |
| LOT 2B | Bordereau | BLOQUE |
| LOT 3 | Exécution / Décomptes | BLOQUE |
| LOT 4 | Moteur de révision | BLOQUE |
| LOT 5 | Validation / Snapshots | BLOQUE |
| LOT 6 | Régularisation | BLOQUE |
| LOT 7 | Documents | BLOQUE |
| LOT 8 | Référentiel officiel | BLOQUE |
| LOT 9 | Production | BLOQUE |

Les composants LOT 1B non couverts par Market et MarketLot restent hors
périmètre jusqu'à une autorisation distincte.

Après le gel de GOV V1.1 + REG V1, LOT 1A — Authentification /
Utilisateurs / Sociétés est le prochain lot autorisable.

LOT 1B — Marchés / Lots / Structure contractuelle est implémenté et testé
pour Market et MarketLot. La validation finale reste soumise à l'audit,
conformément à ADR-LOT1B-001.

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

Le passage à l'implémentation exige une autorisation dédiée et le passage
des exigences LOT 1B à `IMPLEMENTED`, `TESTED` puis `VALIDATED` uniquement
avec les preuves correspondantes. La présente phase ne produit aucune de
ces preuves de code.
