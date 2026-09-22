STATUS: APPROVED FOR V1 SCOPE — CALCULATION IMPLEMENTATION NOT AUTHORIZED
SOURCE: décision produit V1 — formule unique et ventilation par jours

# Révision des prix

## Parcours V1

```text
Marché simple → formule unique → OS/calendrier → décompte HT
→ jours de travaux par mois → ventilation du montant HT
→ indices mensuels → calcul → validation → historique → documents
```

Le moteur V1 calcule à partir du marché, de sa formule unique, du montant
HT du décompte, de sa période, de ses allocations mensuelles de jours et
des indices officiels. Aucun article, lot, BDP, quantité, prix unitaire ou
multi-formule n'est requis.

Pour chaque mois, la note de calcul doit pouvoir conserver les jours, le
total des jours, le montant mensuel à réviser, l'index, `I / I₀`, le terme
variable, `K`, `K - 1` et le montant de la révision. Le montant cumulé HT
est calculé depuis les décomptes successifs.

Un index absent est affiché `Index non disponible` et bloque le calcul. Il
ne peut être remplacé par zéro, le mois précédent, une valeur inventée ou
un fallback provisoire non validé.

## Éléments fonctionnels APPROVED — cible historique / hors V1 simple

La chaîne conceptuelle historique avancée est :

```text
StatementItems → agrégation par RevisionGroup
→ ventilation mensuelle → formule du groupe → agrégation
```

Cette chaîne et les obligations multi-formules ci-dessous sont conservées
pour les versions futures. Elles ne font pas partie du parcours V1, qui
utilise un montant HT simple directement rattaché au marché et à sa formule
unique.

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

En V1, la ventilation financière est déterminée par les jours de travaux
mensuels conservés dans `MonthlyWorkAllocation`. La règle d'égalité exacte
des montants mensuels et de correction explicite de l'écart d'arrondi sur
la dernière ligne/mois doit être couverte par V1-C.

Les équations, arrondis, bornes de périodes, erreurs et format de preuve
restent à détailler dans une spec de calcul validée. Aucun code métier
n'est ajouté par ce document.
