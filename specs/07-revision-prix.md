STATUS: DRAFT
SOURCE: GOV 1.1 — comportement fonctionnel approuvé, détail de calcul à valider

# Révision des prix

## Éléments fonctionnels APPROVED

La chaîne conceptuelle est :

```text
StatementItems → agrégation par RevisionGroup
→ ventilation mensuelle → formule du groupe → agrégation
```

| ID | Obligation |
|---|---|
| VEN-001 | Supporter ACTUAL_EXECUTION. |
| VEN-002 | Supporter CALENDAR_DAY_PRORATA. |
| VEN-003 | Prioriser l'exécution réelle disponible. |
| VEN-004 | Utiliser le prorata jours uniquement comme repli justifié. |
| VEN-005 | Conserver méthode, valeurs et justifications. |
| REV-001 | Agréger un calcul multi-formules par RevisionGroup. |
| REV-002 | Contrôler la concordance articles / montant du décompte. |
| REV-003 | Contrôler les montants révisables et hors calcul. |
| REV-004 | Contrôler le total concerné. |
| REV-005 | Appliquer la formule du groupe après ventilation. |
| REV-006 | Utiliser Decimal et NUMERIC/DECIMAL pour les montants. |
| REV-007 | Rendre le résultat explicable par groupe, formule et période. |
| REV-008 | Appliquer automatiquement la révision aux prestations à exécuter. |
| REV-009 | En cas de retard imputable validé, retenir le plus faible des deux coefficients requis. |

La ventilation réelle est prioritaire lorsqu'elle est disponible ; le
prorata calendaire est un repli justifié. Les indices absents ne sont pas
remplacés silencieusement. Les valeurs définitives non publiées suivent
la distinction REG-010/REG-011 ; aucun indice ne devient zéro, valeur
précédente ou extrapolation.

## Éléments DRAFT / TBD

Les équations, arrondis, bornes de périodes, erreurs et format de preuve
restent à détailler dans une spec de calcul validée. Aucun code métier
n'est ajouté par ce document.
