STATUS: IMPLEMENTED — TESTED — FROZEN v0.6.1
LOT: LOT 2A.1 — Bibliothèque des modèles de formules
DEPENDENCY: LOT 2A gelé en v0.6.0
NEXT: LOT 2B — Bordereau des prix

# Plan LOT 2A.1

## Objectif

Fournir une bibliothèque de modèles GLOBAL permettant de créer une
`MarketFormula DRAFT` indépendante et traçable, sans créer de moteur de
révision ni de référentiel de valeurs mensuelles.

## Périmètre

- `FormulaTemplate` versionné par `family_key` et `version_number` ;
- `FormulaTemplateTerm` ordonné et Decimal ;
- statuts DRAFT/VERIFIED/DEPRECATED ;
- provenance OFFICIAL/CONTRACT_EXAMPLE/INTERNAL ;
- consultation et sélection de templates GLOBAL ;
- copie transactionnelle vers une formule marché DRAFT ;
- traçabilité `source_template_id` / `source_template_version` ;
- UX de recherche, aperçu et avertissement CPS.

## Hors périmètre

- templates COMPANY effectivement utilisables ;
- `IndexDefinition` et `IndexValue` implémentés ;
- barèmes, scraping et imports ;
- formule officielle BAT3 préchargée ;
- PriceSchedule, PriceItem, imports BDP ;
- décomptes, ventilation, calcul réglementaire, PDF/DOCX.

## Exigences

- `TPL-001` à `TPL-014` dans `TRACEABILITY.md`.

## Dépendances

- modèles, permissions et versionnage LOT 2A ;
- PostgreSQL et Decimal ;
- processus documentaire de vérification des sources ;
- décision de maintenance des templates GLOBAL, initialement réservée à
  l'administration système/curation approuvée.

## Critères d'acceptation

1. Un template GLOBAL VERIFIED peut être consulté selon les permissions.
2. La sélection crée une MarketFormula DRAFT indépendante.
3. Les termes sont copiés avec leur ordre et leurs Decimal.
4. La modification ultérieure du template ne modifie aucun marché existant.
5. Une version VERIFIED est immuable.
6. Une version DEPRECATED reste consultable mais n'est pas proposée par défaut.
7. La provenance et l'avertissement CPS sont affichés.
8. Aucun template n'est déclaré OFFICIAL/VERIFIED sans preuve documentaire.
9. Aucun IndexValue, barème ou moteur de révision n'est créé.
10. Tests backend/frontend, migration additive et traçabilité sont validés.
