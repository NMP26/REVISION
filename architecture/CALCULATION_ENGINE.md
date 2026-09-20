STATUS: DESIGN APPROVED — IMPLEMENTATION NOT AUTHORIZED
IMPLEMENTATION: CONTRACT DOCUMENTED — PURE ENGINE NOT IMPLEMENTED; DEFINITIVE REGULATED CALCULATION NOT IMPLEMENTED

# Moteur de calcul — fondations LOT 2A

Cette page décrit une interface future pure Python. Elle ne crée aucun
code dans cette phase.

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

Le mode exact (`ROUND_HALF_UP`, `ROUND_HALF_EVEN`, `ROUND_DOWN` ou autre)
reste `PENDING_VALIDATION` conformément à `PV-REG-001`. Tant qu'il n'est
pas validé, la valeur Decimal non arrondie peut être conservée et une
sortie réglementaire définitive doit rester bloquée avec
`ROUNDING_POLICY_PENDING`.

## Reproductibilité future

Une révision devra recevoir une copie immuable de la définition et des
valeurs utilisées. L'évaluation ne devra jamais relire la formule ou le
référentiel courant après validation d'une révision.
