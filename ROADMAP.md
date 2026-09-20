# Roadmap générale — RevisionPrix

| Phase | Périmètre | Statut |
|---|---|---|
| LOT 0 | Foundation | TERMINE |
| GOV 1.1 + REG V1 | Gouvernance / référentiel traçable et noyau réglementaire | PRÊT À FIGER |
| LOT 1 | Parent historique : identité, sociétés, marchés et structure contractuelle | Découpé en LOT 1A + LOT 1B |
| LOT 1A | Authentification / Utilisateurs / Sociétés | GELÉ — v0.3.0 |
| LOT 1B | Marchés / Lots / Structure contractuelle | IMPLEMENTED — TESTED, AUDIT À FAIRE |
| LOT 1C | Groupements / Autorités / RC City | GELÉ — v0.5.1 |
| LOT 2A | Formules contractuelles | IMPLEMENTED — TESTED — FROZEN v0.6.0 |
| LOT 2A.1 | Bibliothèque des modèles de formules | FROZEN — v0.6.1 |
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

LOT 1C — Groupements / Autorités / RC City est implémenté, testé et gelé
en v0.5.1. Le périmètre couvre les titulaires en groupement, l'interface
de gestion des groupements, les maîtres
d'ouvrage structurés avec conservation du texte historique, la ville du
registre de commerce indépendante de la ville de la société, les formats
d'affichage français et les migrations additives avec preuve pré/post.

LOT 2A est implémenté, testé et gelé en v0.6.0. Le périmètre couvre les groupes
contractuels, les formules versionnées et leurs termes, sans implémenter le
BDP, les indices complets, les décomptes ou le moteur de révision. Le mode
exact d'arrondi de
`PV-REG-001` reste en attente ; il ne bloque pas le stockage, le
versionnage ou l'UI des formules, mais bloque une sortie réglementaire
définitive qui en dépend.

LOT 2A.1 est le lot indépendant de bibliothèque situé entre LOT 2A et LOT
2B, gelé en v0.6.1 après implémentation, tests et réaudit final réussis. Il
couvre uniquement les templates GLOBAL, leur provenance, versionnement,
immutabilité, permissions de lecture et copie vers une `MarketFormula DRAFT`.
Il n'implémente ni templates COMPANY actifs, ni `IndexDefinition`,
`IndexValue`, barèmes, imports BDP ou moteur de révision. La curation
documentaire globale reste distincte et n'est pas déclarée terminée.

## Découpage officiel du LOT 1

LOT 1 reste le lot parent historique du Blueprint. Il est exécuté en deux
sous-lots de gouvernance :

```text
LOT 1
 ├── LOT 1A — Authentification / Utilisateurs / Sociétés
 ├── LOT 1B — Marchés / Lots / Structure contractuelle
 └── LOT 1C — Groupements / Autorités / RC City
```

Le découpage 1A/1B précise le LOT 1 ; il ne le supprime pas et ne
constitue pas un démarrage de développement.

Le passage à l'implémentation exige une autorisation dédiée et le passage
des exigences LOT 1B à `IMPLEMENTED`, `TESTED` puis `VALIDATED` uniquement
avec les preuves correspondantes. La présente phase ne produit aucune de
ces preuves de code.
