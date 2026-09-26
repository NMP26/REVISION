STATUS: DESIGN APPROVED — CALC-01 IMPLEMENTED LOCALLY FOR V1 PREVIEW
IMPLEMENTATION: PURE DECIMAL PREVIEW IMPLEMENTED; DEFINITIVE REGULATED OUTPUT REMAINS BLOCKED

# Moteur de calcul — fondations LOT 2A

## Règle SRM-SM CALC-01

Le moteur utilise exclusivement `Decimal`. Pour la formule simple, chaque
étape contractuelle est tronquée à quatre décimales avant d'être transmise à
l'étape suivante : ratio `I/I₀`, terme variable, coefficient `P/P₀`, puis
variation `P/P₀ - 1`. La politique est centralisée dans
`markets.calculation_engine.round_regulatory_4`, avec le mode Decimal
`ROUND_DOWN` (troncature vers zéro). Ainsi `348,7 / 337,8 = 1,0322`,
`0,85 × 1,0322 = 0,8773`, `P/P₀ = 1,0273` et la variation vaut `0,0273`.

Le cœur pur Python est implémenté pour la PREVIEW V1. Cette correction ne
valide ni une révision définitive ni une promotion d'indice en production.

## Séparation des responsabilités

```text
MarketFormula + FormulaTerm
        |
        v
evaluate_formula(...) -> coefficient Decimal ou état bloquant
        |
        v
ventilation / révision / montants — lots ultérieurs
```

La formule contractuelle n'est pas une formule calculée. Django ne doit
pas être requis par le cœur d'évaluation, et React ne doit jamais porter
le calcul métier.

## Interface proposée

```python
evaluate_formula(
    constant: Decimal,
    terms: Sequence[FormulaTermInput],
    current_indices: Mapping[str, Decimal],
    *,
    rounding_policy: RoundingPolicy | None = None,
) -> FormulaEvaluation
```

Entrées : constante Decimal ; termes ordonnés avec coefficient Decimal,
`term_type`, code d'index et valeur de base Decimal ; valeurs courantes
explicitement disponibles par code ; politique d'arrondi explicitement
fournie, jamais implicite.

Sortie conceptuelle :

```text
FormulaEvaluation
  raw_coefficient: Decimal
  rounded_coefficient: Decimal | None
  status: CALCULABLE | PENDING_INDEX | ROUNDING_POLICY_PENDING
  used_indices: ordered metadata
```

Erreurs bloquantes : terme inconnu, coefficient non Decimal, base absente,
base nulle, index courant absent, formule incohérente ou politique
d'arrondi indisponible.

Une valeur d'index manquante ne devient jamais zéro, valeur précédente,
extrapolation ou valeur provisoire silencieuse.

## Précision et arrondi

Les opérations utilisent `Decimal` et une précision de contexte
explicitement configurée. La précision de stockage de base est
`NUMERIC(18,8)` pour les valeurs persistées ; elle ne constitue pas la
règle réglementaire d'arrondi et ne doit pas provoquer de troncature
prématurée. La politique d'arrondi est centralisée et explicite, sans
utiliser l'arrondi Python implicite ni disperser la règle dans les
serializers, vues ou frontend.

Le mode implémenté pour la PREVIEW CALC-01 est `ROUND_DOWN`, soit une
troncature vers zéro à quatre décimales. La sortie réglementaire définitive
reste bloquée tant que `PV-REG-001` n'est pas clôturé ; le moteur expose donc
explicitement le statut de PREVIEW et ne crée aucun snapshot validé.

## Reproductibilité future

Une révision devra recevoir une copie immuable de la définition et des
valeurs utilisées. L'évaluation ne devra jamais relire la formule ou le
référentiel courant après validation d'une révision.
