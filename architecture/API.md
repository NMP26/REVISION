STATUS: APPROVED — IMPLEMENTED
IMPLEMENTATION: IMPLEMENTED — TESTED, NON VALIDATED
SOURCE: specs/02-marches.md, ADR-LOT1B-001

# API LOT 1B — contrat implémenté

Cette page décrit le contrat implémenté pour LOT 1B. Les règles
réglementaires de référence restent hors de ce périmètre.

## Ressources prévues

- `GET /api/markets/` : marchés accessibles via Membership actif ;
- `POST /api/markets/` : OWNER/ADMIN actifs uniquement ;
- `GET /api/markets/{id}/` : lecture autorisée ;
- `PATCH /api/markets/{id}/` : OWNER/ADMIN actifs uniquement ;
- `GET /api/markets/{id}/lots/` : lots du marché ;
- `POST /api/markets/{id}/lots/` : OWNER/ADMIN actifs uniquement ;
- `PATCH /api/markets/{id}/lots/{lot_id}/` : OWNER/ADMIN actifs uniquement.

La validation API devra vérifier les champs obligatoires, `amount_ht >= 0`,
`0 <= vat_rate <= 100`, la paire de délai cohérente, les unités
`DAYS`/`MONTHS`, les statuts autorisés et les contraintes d'unicité par
société/marché et par marché/lot. Elle ne devra inventer aucune date ni
appliquer de conversion `MONTHS × 30`.

La société est sélectionnable uniquement à la création et devient
immuable lors des PATCH ; le contrôle d'accès porte ensuite sur la société
du marché existant.

Les règles de date réglementaire de référence ne sont pas une dérivation
automatique de l'API LOT 1B ; elles seront exposées par le moteur
réglementaire lorsqu'elles seront validées.

Les endpoints futurs de formules, groupes, bordereaux, articles,
décomptes, ventilations, indices et documents restent séparés. Les
imports prévus conservent les espaces `imports/price_schedule/` et
`imports/statements/`.
