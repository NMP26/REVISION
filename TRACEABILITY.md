# Référentiel de traçabilité — RevisionPrix

Ce registre relie chaque exigence à sa source, son ADR, sa spécification,
son implémentation, sa migration, ses tests et sa version. Une valeur `—`
signifie qu'aucun élément n'existe encore ; `TBD` signifie qu'il reste à
définir ou à produire. Les exigences métier ne sont pas déclarées
implémentées sans preuve.

## Chaîne officielle

```text
Exigence → ADR → Spec → Code → Migration → Test → Version
```

## Familles d'identifiants

| Préfixe | Famille |
|---|---|
| PROD-xxx | Produit |
| AUTH-xxx | Authentification |
| SOC-xxx | Sociétés |
| MKT-xxx | Marchés |
| LOT-xxx | Lots |
| FRM-xxx | Formules |
| BDP-xxx | Bordereau des prix |
| OS-xxx | OS / calendrier |
| DEC-xxx | Décomptes |
| VEN-xxx | Ventilation mensuelle |
| REV-xxx | Révision des prix |
| IDX-xxx | Indices |
| HIS-xxx | Historique / versions |
| DOC-xxx | PDF/DOCX |
| IMP-xxx | Import/export |
| REG-xxx | Réglementation |
| SEC-xxx | Sécurité |
| OPS-xxx | Exploitation / migration |

## Statuts autorisés

`DRAFT`, `APPROVED`, `PLANNED`, `IN_PROGRESS`, `IMPLEMENTED`, `TESTED`,
`VALIDATED`, `BLOCKED`, `SUPERSEDED`.

## Registre

| ID | Exigence | Source | ADR | Spec | Code | Migration | Test | Statut | Version |
|---|---|---|---|---|---|---|---|---|---|
| LOT-000 | Fondation technique LOT 0 | Blueprint §§56–59 | ADR-LOT0-001 | specs/00-product.md | code LOT 0 | backend/core/migrations/0001_initial.py | make test; make doctor | VALIDATED | v0.1.0 |
| PROD-001 | Le Blueprint est la vision fonctionnelle globale du produit. | Blueprint | ADR-LOT0-001 | specs/00-product.md | — | — | revue documentaire | APPROVED | GOV-1.1 |
| AUTH-001 | Une fonction privée exige un accès authentifié. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/core/authentication.py; backend/accounts/views.py; backend/companies/views.py | backend/accounts/migrations/0001_initial.py; backend/companies/migrations/0001_initial.py | backend/accounts/test_api.py::test_login_me_logout; backend/companies/tests.py::test_anonymous_is_refused | TESTED | UNRELEASED |
| AUTH-002 | Les sessions suivent l'architecture d'authentification retenue. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/core/authentication.py; backend/config/settings.py | — | backend/accounts/test_api.py::test_login_me_logout; backend/accounts/test_api.py::test_csrf_endpoint_returns_token; backend/accounts/test_api.py::test_csrf_is_required_for_authenticated_mutation | TESTED | UNRELEASED |
| AUTH-003 | Un accès non authentifié est refusé. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/core/authentication.py; backend/companies/views.py | — | backend/companies/tests.py::test_anonymous_is_refused | TESTED | UNRELEASED |
| AUTH-004 | Aucune donnée sensible n'est exposée par l'authentification ou l'API. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/accounts/serializers.py; backend/accounts/views.py; backend/core/exceptions.py; backend/core/middleware.py | — | backend/accounts/test_api.py::test_invalid_login_is_generic; backend/accounts/test_api.py::test_login_me_logout; backend/core/tests.py::test_unhandled_api_error_is_uniform_and_does_not_expose_detail | TESTED | UNRELEASED |
| SOC-001 | Une société peut être créée avec les champs obligatoires définis par la spec. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/serializers.py; backend/companies/views.py | backend/companies/migrations/0001_initial.py | backend/companies/tests.py::test_create_assigns_owner; frontend/src/companies/CompanyForm.test.tsx | TESTED | UNRELEASED |
| SOC-002 | Une société peut être consultée par un utilisateur autorisé. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/views.py; frontend/src/companies/CompaniesPage.tsx | — | backend/companies/tests.py::test_list_is_limited_to_active_memberships; backend/companies/tests.py::test_user_without_membership_gets_not_found | TESTED | UNRELEASED |
| SOC-003 | Une société peut être modifiée par un utilisateur autorisé. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/permissions.py; backend/companies/views.py; frontend/src/companies/CompanyForm.tsx | — | backend/companies/tests.py::test_admin_and_owner_can_update; backend/companies/tests.py::test_member_can_read_but_cannot_update | TESTED | UNRELEASED |
| SOC-004 | Les validations de société refusent les données non conformes. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/serializers.py | — | backend/companies/tests.py::test_logo_size_limit; backend/companies/tests.py::test_logo_valid_image_is_accepted; backend/companies/tests.py::test_logo_extension_and_content_are_validated; backend/companies/tests.py::test_logo_path_traversal_is_never_persisted; backend/companies/tests.py::test_logo_replacement_updates_the_stored_path | TESTED | UNRELEASED |
| SOC-005 | Les champs de société sont ceux définis dans la spec société. | Blueprint §7 | ADR-GOV-001 | specs/01-societes.md | backend/companies/models.py; backend/companies/serializers.py; frontend/src/companies/CompanyForm.tsx | backend/companies/migrations/0001_initial.py | backend/companies/tests.py::test_company_defaults_active_and_identifiers_are_not_unique; frontend/src/companies/CompanyForm.test.tsx | TESTED | UNRELEASED |
| SOC-006 | Une société est persistée dans PostgreSQL. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/models.py; backend/companies/views.py | backend/companies/migrations/0001_initial.py | backend/companies/tests.py::test_create_assigns_owner | TESTED | UNRELEASED |
| SOC-007 | La société est exposée par une API. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/views.py; backend/core/urls.py | — | backend/companies/tests.py::test_create_assigns_owner; backend/companies/tests.py::test_anonymous_is_refused | TESTED | UNRELEASED |
| SOC-008 | L'interface société respecte les sketches et specs validés. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | frontend/src/App.tsx; frontend/src/companies/CompaniesPage.tsx; frontend/src/companies/CompanyForm.tsx; frontend/src/lib/api.ts; frontend/nginx.conf | — | frontend/src/companies/CompanyForm.test.tsx; frontend/src/companies/CompaniesPage.test.tsx; npm run test; npm run build | TESTED | UNRELEASED |
| SOC-009 | Les règles société disposent de tests backend. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/models.py; backend/companies/serializers.py; backend/companies/views.py | — | backend/companies/tests.py | TESTED | UNRELEASED |
| SOC-010 | Les parcours société disposent de tests API pertinents. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/views.py; backend/core/urls.py | — | backend/companies/tests.py; make test | TESTED | UNRELEASED |
| SOC-011 | Le rattachement utilisateur/société est contrôlé et testable via Membership. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | backend/companies/models.py; backend/companies/permissions.py | backend/companies/migrations/0001_initial.py | backend/companies/tests.py::test_membership_roles_and_unique_pair; backend/companies/tests.py::test_list_is_limited_to_active_memberships | TESTED | UNRELEASED |
| SOC-012 | Les parcours société disposent de tests frontend pertinents. | Cahier cumulatif §1 | ADR-GOV-001 | specs/01-societes.md | frontend/src/companies/CompanyForm.tsx; frontend/src/companies/CompanyForm.test.tsx; frontend/src/companies/CompaniesPage.test.tsx | — | frontend/src/companies/CompanyForm.test.tsx; frontend/src/companies/CompaniesPage.test.tsx; npm run test | TESTED | UNRELEASED |
| MKT-001 | Un marché porte la structure contractuelle mono-formule. | Cahier cumulatif §2 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_formula_structure_and_archived_status; frontend/src/markets/MarketForm.test.tsx | TESTED | v0.3.0+LOT1B |
| MKT-002 | Un marché porte la structure contractuelle multi-formules. | Cahier cumulatif §2 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_create_returns_decimal_values_and_defaults_active | TESTED | v0.3.0+LOT1B |
| MKT-003 | Un marché peut contenir zéro à plusieurs lots. | Cahier cumulatif §6 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/views.py; frontend/src/markets/MarketsPage.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::MarketLotApiTests; frontend/src/markets/MarketsPage.test.tsx | TESTED | v0.3.0+LOT1B |
| MKT-004 | La structure contractuelle est distincte de la création d'une formule. | Cahier cumulatif §§2,9 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_formula_structure_and_archived_status | TESTED | v0.3.0+LOT1B |
| MKT-005 | Un marché est rattaché obligatoirement à une société. | Cahier cumulatif §1 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_create_returns_decimal_values_and_defaults_active | TESTED | v0.3.0+LOT1B |
| MKT-006 | Un marché conserve la date d'ouverture des plis, nullable. | Cahier cumulatif §2 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx; frontend/src/markets/MarketsPage.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_dates_are_nullable; frontend/src/markets/MarketForm.test.tsx | TESTED | v0.3.0+LOT1B |
| MKT-007 | Les dates factuelles du marché sont conservées sans devenir automatiquement une date réglementaire de référence. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_dates_are_nullable | TESTED | v0.3.0+LOT1B |
| MKT-008 | Un marché conserve la date d'OS de commencement, nullable. | Cahier cumulatif §2 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_dates_are_nullable | TESTED | v0.3.0+LOT1B |
| MKT-009 | Le délai est une paire cohérente valeur/unité DAYS ou MONTHS, sans conversion arbitraire. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py; backend/markets/migrations/0002_market_invariants.py | backend/markets/tests.py::test_duration_requires_pair_and_positive_value; backend/markets/tests.py::test_database_constraints_reject_invalid_market_values | TESTED | v0.3.0+LOT1B |
| MKT-010 | Un marché conserve la TVA comme pourcentage Decimal borné de 0 à 100. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_amount_and_vat_boundaries_are_validated; backend/markets/tests.py::test_decimal_round_trip_including_maximum_amount; backend/markets/tests.py::test_database_constraints_reject_invalid_market_values | TESTED | v0.3.0+LOT1B |
| MKT-011 | Un marché conserve un montant HT Decimal(18,2) nullable et >= 0. | Cahier cumulatif §2 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_amount_and_vat_boundaries_are_validated; backend/markets/tests.py::test_decimal_round_trip_including_maximum_amount; backend/markets/tests.py::test_database_constraints_reject_invalid_market_values | TESTED | v0.3.0+LOT1B |
| MKT-012 | Les règles de référence des indices sont portées par le moteur réglementaire selon la procédure validée. | Arrêté 3-302-15, art. 4 et 7 | ADR-REG-001; ADR-LOT1B-001 | specs/02-marches.md | — | — | TBD | APPROVED | REG-1.0 |
| MKT-013 | `market_number`, `contracting_authority` et `subject` sont obligatoires. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py | backend/markets/migrations/0001_initial.py; backend/markets/migrations/0002_market_invariants.py | backend/markets/tests.py::test_required_market_text_fields_reject_empty_and_whitespace; backend/markets/tests.py::test_database_constraints_reject_invalid_market_values | TESTED | v0.3.0+LOT1B |
| MKT-014 | Le statut est ACTIVE ou ARCHIVED, ACTIVE par défaut ; SUSPENDED n'est pas un statut de Market. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_formula_structure_and_archived_status | TESTED | v0.3.0+LOT1B |
| MKT-015 | Le numéro de marché est unique par société, jamais globalement dans LOT 1B. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/views.py | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_number_unique_per_company_but_reusable_in_other_company | TESTED | v0.3.0+LOT1B |
| MKT-016 | La structure `formula_structure` vaut SINGLE ou MULTIPLE et ne crée aucune formule. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_formula_structure_and_archived_status | TESTED | v0.3.0+LOT1B |
| V1A-001 | Un marché `SINGLE` présente directement une formule unique et ne présente pas le choix mono/multi-formules. | Décision produit V1-A | — | specs/02-marches.md; plans/V1-SIMPLE.md | frontend/src/markets/MarketsPage.tsx; frontend/src/markets/RevisionApplicationSection.tsx | — | frontend/src/markets/V1SimpleFormulaFlow.test.tsx | IMPLEMENTED | V1-A |
| V1A-002 | Le catalogue V1 est visible à l'ouverture du sélecteur sans recherche préalable et peut être filtré. | Décision produit V1-A | — | specs/03A-formula-template-library.md | frontend/src/markets/FormulaCatalogSelector.tsx; backend/markets/views.py | backend/markets/migrations/0007_product_owner_formula_catalog.py | frontend/src/markets/V1SimpleFormulaFlow.test.tsx; backend/markets/tests.py::V1SimpleFormulaApiTests | IMPLEMENTED | V1-A |
| V1A-003 | BAT3 et les autres formules simples autorisées affichent code, désignation et expression, sans valeur d'indice inventée. | Décision produit V1-A | — | specs/03-formules.md; specs/03A-formula-template-library.md | frontend/src/markets/FormulaCatalogSelector.tsx; frontend/src/markets/RevisionApplicationSection.tsx | backend/markets/migrations/0007_product_owner_formula_catalog.py | frontend/src/markets/V1SimpleFormulaFlow.test.tsx; backend/markets/tests.py::V1SimpleFormulaApiTests | IMPLEMENTED | V1-A |
| V1A-004 | Le parcours V1 ne requiert ni BDP, ni lot, ni `RevisionGroup` exposé ; l'architecture LOT 2B est conservée. | Décision produit V1-A | ADR-LOT2B-006 | specs/02-marches.md; architecture/DATA_MODEL.md | frontend/src/markets/MarketsPage.tsx; backend/markets/services.py | — | frontend/src/markets/V1SimpleFormulaFlow.test.tsx; backend/markets/tests.py::V1SimpleFormulaApiTests; suite LOT 2B | IMPLEMENTED | V1-A |
| MKT-017 | Les permissions Market réutilisent Membership actif du LOT 1A. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/permissions.py; backend/markets/views.py | — | backend/markets/tests.py::test_owner_admin_can_create_and_update_member_can_read_only; backend/markets/tests.py::test_inactive_or_missing_membership_cannot_read_or_create | TESTED | v0.3.0+LOT1B |
| MKT-018 | `date_limite_remise_offres`, `date_ouverture_plis`, `date_signature` et `date_os_commencement` sont nullables. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; frontend/src/markets/MarketForm.tsx | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_dates_are_nullable; frontend/src/markets/MarketForm.test.tsx | TESTED | v0.3.0+LOT1B |
| MKT-019 | Les règles réglementaires sont séparées des faits persistés du marché. | Décision LOT 1B | ADR-LOT1B-001 | architecture/DATA_MODEL.md | backend/markets/models.py; backend/markets/serializers.py | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_dates_are_nullable | IMPLEMENTED | v0.3.0+LOT1B |
| MKT-020 | La conception LOT 1B est approuvée et son implémentation Market/MarketLot est réalisée. | Décision LOT 1B | ADR-LOT1B-001 | plans/LOT-01.md | backend/markets/; frontend/src/markets/ | backend/markets/migrations/0001_initial.py | backend/markets/tests.py; frontend/src/markets/*.test.tsx | TESTED | v0.3.0+LOT1B |
| LOT-001 | Un lot peut contenir plusieurs articles de prix dans les lots futurs. | Cahier cumulatif §6 | ADR-LOT1B-001 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1B |
| LOT-002 | Un lot n'est pas assimilé à une formule. | Cahier cumulatif §6 | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; architecture/DATA_MODEL.md | backend/markets/migrations/0001_initial.py | backend/markets/tests.py::test_nested_url_cannot_access_lot_from_other_market | IMPLEMENTED | v0.3.0+LOT1B |
| LOT-003 | MarketLot porte ses champs obligatoires, optionnels, montants et timestamps définis. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/serializers.py; frontend/src/markets/MarketLotForm.tsx | backend/markets/migrations/0001_initial.py; backend/markets/migrations/0002_market_invariants.py | backend/markets/tests.py::MarketLotApiTests; backend/markets/tests.py::test_required_lot_text_fields_reject_empty_and_whitespace; backend/markets/tests.py::test_database_constraints_reject_invalid_lot_values; frontend/src/markets/MarketLotForm.test.tsx | TESTED | v0.3.0+LOT1B |
| LOT-004 | MarketLot est unique par marché et numéro/code, sans FK vers MarketFormula ni lot automatique. | Décision LOT 1B | ADR-LOT1B-001 | specs/02-marches.md | backend/markets/models.py; backend/markets/views.py | backend/markets/migrations/0001_initial.py; backend/markets/migrations/0002_market_invariants.py | backend/markets/tests.py::test_unique_within_market_and_reusable_in_other_market; backend/markets/tests.py::test_nested_url_rejects_lot_from_other_accessible_market_on_read_and_patch; frontend/src/markets/MarketsPage.test.tsx | TESTED | v0.3.0+LOT1B |
| FRM-001 | Un RevisionGroup porte une ou plusieurs MarketFormula. | Cahier cumulatif §3 | ADR-LOT2A-001 | specs/03-formules.md | backend/markets/models.py; backend/markets/views.py | backend/markets/migrations/0004_revisiongroup_marketformula_formulaterm_and_more.py | backend/markets/tests.py::RevisionFormulaApiTests | TESTED | v0.6.0 |
| FRM-002 | Une MarketFormula peut utiliser plusieurs FormulaTerm et indices. | Cahier cumulatif §§3,11 | ADR-LOT2A-001 | specs/03-formules.md | backend/markets/models.py; backend/markets/serializers.py | backend/markets/migrations/0004_revisiongroup_marketformula_formulaterm_and_more.py | backend/markets/tests.py::RevisionFormulaApiTests::test_create_group_formula_and_terms_uses_decimal_strings | TESTED | v0.6.0 |
| FRM-003 | Le futur moteur de formule n'a pas de dépendance structurelle à BAT3. | Cahier cumulatif §11 | ADR-LOT2A-001 | architecture/CALCULATION_ENGINE.md | — | — | hors périmètre LOT 2A ; contrôle de symboles | APPROVED | moteur futur |
| BDP-001 | La présence d'un BDP est activable selon le marché. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-002 | PriceSchedule regroupe les PriceItem d'un marché. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-003 | PriceItem porte un numéro de prix. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-004 | PriceItem porte une désignation. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-005 | PriceItem porte une unité. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-006 | PriceItem porte les quantités. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-007 | PriceItem porte un prix unitaire HT. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-008 | PriceItem porte un montant estimatif. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-009 | PriceItem peut être rattaché à un lot. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-010 | PriceItem peut être rattaché à un RevisionGroup. | Cahier cumulatif §4 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-011 | Un article peut être traité comme REVISABLE. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-012 | Un article peut être traité comme NON_REVISABLE. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-013 | Un article non classé reste PENDING_CLASSIFICATION. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-014 | PENDING_CLASSIFICATION bloque la validation du calcul concerné. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-015 | NON_REVISABLE est distinct d'une formule K=1. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-016 | La classification ne se déduit pas automatiquement du nom. | Cahier cumulatif §5 | ADR-GOV-006 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| BDP-017 | Une prestation reste compatible avec une décomposition approvisionnement/mise en œuvre. | Cahier cumulatif §7 | ADR-GOV-005 | specs/04-bordereau-prix.md | — | — | TBD | PLANNED | GOV-1.1 |
| BDP-018 | Une prestation d'approvisionnement conserve sa date effective d'approvisionnement. | Arrêté 3-302-15, art. 16 | ADR-REG-001 | specs/04-bordereau-prix.md | — | — | TBD | PLANNED | REG-1.0 |
| OS-001 | Une révision conserve son OS, suspensions et reprises dans son périmètre historisé. | Cahier cumulatif §13 | ADR-GOV-010 | specs/05-os-calendrier.md | — | — | TBD | PLANNED | GOV-1.1 |
| OS-002 | L'imputabilité d'un retard au titulaire est une donnée/validation explicite. | Arrêté 3-302-15, art. 18 | ADR-REG-001 | specs/05-os-calendrier.md | — | — | TBD | PLANNED | REG-1.0 |
| DEC-001 | Statement porte numéro, date, période et montants HT. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-002 | Statement conserve cumul, dernier décompte et observations. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-003 | StatementItem référence un PriceItem et ses quantités/montants. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-004 | StatementItem conserve les snapshots de groupe et de traitement. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-005 | Le montant de période peut être obtenu par cumul courant moins cumul précédent. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-006 | Le delta détaillé est calculable par article puis agrégé par RevisionGroup. | Cahier cumulatif §8 | ADR-GOV-008 | specs/06-decomptes.md | — | — | TBD | APPROVED | GOV-1.1 |
| DEC-007 | Le décompte définitif fait ressortir le total de révision et un état récapitulatif. | Arrêté 3-302-15, art. 15 | ADR-REG-001 | specs/06-decomptes.md | — | — | TBD | PLANNED | REG-1.0 |
| DEC-008 | En V1, le décompte est une enveloppe HT simple sans article, quantité, prix, lot, BDP ou détail de prestation. | Décision produit V1 | — | specs/06-decomptes.md; plans/V1-SIMPLE.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| DEC-009 | En V1, Statement porte uniquement numéro, date, montant HT Decimal et observation facultative ; les dates de période restent dans l'OS/calendrier et l'exécution. | Décision produit V1 — périmètre final | — | specs/06-decomptes.md; architecture/DATA_MODEL.md; plans/V1-SIMPLE.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| VEN-001 | La ventilation supporte ACTUAL_EXECUTION. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-002 | La ventilation supporte CALENDAR_DAY_PRORATA. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-003 | ACTUAL_EXECUTION est prioritaire si les montants réels sont disponibles. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-004 | CALENDAR_DAY_PRORATA est un repli justifié si la répartition réelle est impossible. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-005 | Méthode, valeurs proposées/retenues et justification sont conservées pour audit. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-006 | En V1, un décompte conserve une allocation dédiée par année, mois et jours de travaux, sans détourner StatementItem ou PriceItem. | Décision produit V1 — jours de travaux par mois | — | specs/06-decomptes.md; architecture/DATA_MODEL.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| VEN-007 | Les mois à zéro jour restent conservés et visibles dans la note de calcul. | Décision produit V1 — jours de travaux par mois | — | specs/06-decomptes.md; specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| VEN-008 | Le montant mensuel est calculé par prorata des jours avec Decimal et la somme est exactement égale au montant HT, l'écart d'arrondi étant traité explicitement sur la dernière ligne/mois. | Décision produit V1 — jours de travaux par mois | — | specs/06-decomptes.md; specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| REV-001 | Un calcul multi-formules agrège les StatementItems par RevisionGroup. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-002 | Le système contrôle la concordance entre les articles et le montant du décompte. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-003 | Le système contrôle la concordance des montants révisables et hors calcul. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-004 | Le système contrôle la concordance avec le total concerné. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-005 | Le calcul applique la formule du groupe après ventilation. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-006 | Les calculs financiers utilisent Decimal côté Python et NUMERIC/DECIMAL côté PostgreSQL. | Blueprint §2 | ADR-GOV-007 | architecture/CALCULATION_ENGINE.md | socle partiel | — | TBD | APPROVED | GOV-1.1 |
| REV-007 | Le résultat de révision est explicable par groupe, formule et période. | Cahier cumulatif §§9,14 | ADR-GOV-011 | specs/07-revision-prix.md | — | — | TBD | PLANNED | GOV-1.1 |
| REV-008 | Une révision est appliquée aux prestations à exécuter sans demande spéciale du titulaire. | Arrêté 3-302-15, art. 9 | ADR-REG-001 | specs/07-revision-prix.md | — | — | TBD | PLANNED | REG-1.0 |
| REV-009 | En cas de retard imputable, le calcul compare le coefficient du mois réel au coefficient du dernier mois contractuel et retient le plus faible. | Arrêté 3-302-15, art. 18 | ADR-REG-001 | specs/07-revision-prix.md | — | — | TBD | PLANNED | REG-1.0 |
| REV-010 | Le cumul HT est calculé à partir des décomptes successifs et n'est pas ressaisi manuellement. | Décision produit V1 — note de calcul SRM-SM | — | specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| REV-011 | Un index manquant est affiché « Index non disponible » et bloque le calcul sans zéro, reprise du mois précédent ou fallback silencieux. | Décision produit V1 — note de calcul SRM-SM | — | specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| REV-012 | Le parcours V1 suit Marché simple → formule unique → OS/calendrier → décompte → jours mensuels → ventilation HT → indices → calcul → validation → historique → documents. | Décision produit V1 — périmètre final | — | plans/V1-SIMPLE.md; ROADMAP.md; specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| IDX-001 | Le référentiel distingue IndexDefinition et IndexValue. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-002 | IndexValue conserve code, désignation, mois et valeur. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-003 | IndexValue conserve statut, publication, source et historique. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-006 | En V1, un indice mensuel absent est affiché « Index non disponible » et bloque le calcul sans valeur de remplacement. | Décision produit V1 — note de calcul SRM-SM | — | specs/08-indices-baremes.md; specs/07-revision-prix.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| IDX-004 | Une valeur d'indice absente ne devient ni zéro, ni valeur précédente, ni extrapolation. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-005 | Les indices utilisés et leur provenance sont historisés avec la révision. | Cahier cumulatif §§12,13 | ADR-GOV-010 | specs/08-indices-baremes.md | — | — | TBD | PLANNED | GOV-1.1 |
| HIS-001 | Une révision validée fige le marché et ses données contractuelles. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-002 | Une révision validée fige les lots, articles et montants. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-003 | Une révision validée fige groupes, formules et termes. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-004 | Une révision validée fige indices et sources. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-005 | Une révision validée fige OS, suspensions et reprises. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-006 | Une révision validée fige décompte, ventilation et méthode. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-007 | Une révision validée fige coefficients, arrondis et résultat. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| HIS-008 | Une modification future ne réécrit jamais silencieusement une révision validée. | Cahier cumulatif §13 | ADR-GOV-010 | specs/09-historique-regulation.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-001 | Le système génère un PDF de révision. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-002 | Le système génère un DOCX de révision. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-003 | PDF et DOCX utilisent la même donnée calculée. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-004 | La note de calcul expose le total du décompte et les montants soumis/hors calcul. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-008 | La note de calcul V1 expose les mois à zéro jour, les jours, le total, la ventilation HT, les indices, coefficients et montants dérivés. | Décision produit V1 — note de calcul SRM-SM | — | specs/10-documents.md; plans/V1-SIMPLE.md | — | — | revue documentaire | APPROVED | V1-SIMPLE |
| DOC-005 | La note de calcul expose formules et ventilation mensuelle. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-006 | La note de calcul expose indices et coefficients. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| DOC-007 | La note de calcul expose groupes et total de révision. | Cahier cumulatif §14 | ADR-GOV-011 | specs/10-documents.md | — | — | TBD | APPROVED | GOV-1.1 |
| IMP-001 | Les imports sont séparés entre price_schedule et statements. | Cahier cumulatif §15 | ADR-GOV-012 | architecture/API.md | — | — | TBD | PLANNED | GOV-1.1 |
| IMP-002 | Le mapping de colonnes d'import est configurable et indépendant d'Excel. | Cahier cumulatif §15 | ADR-GOV-012 | specs/04-bordereau-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REG-001 | Le CPS peut prévoir une ou plusieurs formules et associe chaque prestation à la formule applicable. | Arrêté 3-302-15, art. 3, 4, 9 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-002 | La formule supporte P=P0[k+a(X/X0)+b(Y/Y0)+…], avec k≥0,15 et somme des coefficients égale à 1. | Arrêté 3-302-15, art. 4 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-003 | La règle de référence des indices distingue appel à concurrence et marché négocié. | Arrêté 3-302-15, art. 4, 7 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-004 | Les coefficients et la nature des index sont ceux des cahiers applicables et la formule est contractuelle par marché. | Arrêté 3-302-15, art. 5 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-005 | Une formule d'un marché révisable ≤ 1 000 000 DH comporte au plus cinq index. | Arrêté 3-302-15, art. 6 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-006 | La forme à index global P=P0[k+a(I/I0)] est supportée par le moteur générique, avec k+a=1. | Arrêté 3-302-15, art. 7 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-007 | Le coefficient final et les rapports intermédiaires sont arrêtés à la quatrième décimale ; le mode informatique exact reste à valider. | Arrêté 3-302-15, art. 8 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-008 | La révision s'applique automatiquement aux prestations à exécuter, sans demande spéciale ni avenant spécifique de révision. | Arrêté 3-302-15, art. 9 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-009 | Les valeurs d'index sont publiées mensuellement par le ministre chargé de l'équipement. | Arrêté 3-302-15, art. 10 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-010 | Pour un décompte provisoire ordinaire, des valeurs définitives non publiées entraînent un paiement sans révision puis une régularisation au décompte provisoire suivant. | Arrêté 3-302-15, art. 12 ; Avis CNCP 192/2025 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-011 | Pour le dernier décompte provisoire, les valeurs publiées disponibles à sa date d'établissement sont utilisées. | Arrêté 3-302-15, art. 12 ; Avis CNCP 192/2025 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-012 | Chaque révision d'un décompte provisoire est accompagnée d'une note de calcul justificative. | Arrêté 3-302-15, art. 13 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-013 | Sur plusieurs mois, la ventilation réelle est prioritaire et le prorata des jours calendaires est le repli. | Arrêté 3-302-15, art. 14 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-014 | Le décompte définitif fait ressortir le total de révision et un état récapitulatif. | Arrêté 3-302-15, art. 15 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-015 | L'approvisionnement et la mise en œuvre peuvent avoir des prix et formules distincts, avec prise en compte de la date effective d'approvisionnement. | Arrêté 3-302-15, art. 16 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| REG-016 | En cas de retard imputable, le plus faible des coefficients du mois réel et du dernier mois contractuel est appliqué après validation explicite de l'imputabilité. | Arrêté 3-302-15, art. 18 | ADR-REG-001 | regulatory/RULES.md | — | — | TBD | VERIFIED | REG-1.0 |
| SEC-001 | Aucun secret n'est versionné et PostgreSQL n'est pas exposé publiquement. | Blueprint §50 | ADR-LOT0-001 | architecture/SECURITY.md | LOT 0 | — | make doctor | VALIDATED | v0.1.0 |
| OPS-001 | GitHub NMP26/REVISION est la source officielle du code versionné. | Décision publication LOT 0 | ADR-GOV-014 | architecture/DEPLOYMENT.md | dépôt Git | — | revue Git | APPROVED | GOV-1.1 |
| OPS-002 | Aucun lot suivant ne démarre sans autorisation explicite et traçabilité. | Cahier cumulatif §18 | ADR-GOV-015 | plans/MASTER_PLAN.md | gouvernance | — | revue documentaire | APPROVED | GOV-1.1 |
| OPS-003 | Les données saisies en production sont persistantes. Un déploiement, rebuild, upgrade ou migration ne doit jamais entraîner leur suppression ou leur réinitialisation. | Exigence audit persistance production | ADR-GOV-016 | architecture/DEPLOYMENT.md; docs/OPERATIONS.md; docs/MIGRATION.md; docs/BACKUP_RESTORE.md | compose.yaml; scripts/backup.sh; Makefile | — | make backup; make doctor; vérification volumes; test down/up documenté | VALIDATED | v0.4.1 |

## LOT 2B — exigences validées et gel v0.7.1

Ces exigences sont implémentées, testées et validées dans le candidat
v0.7.1. La preuve de migration couvre une base vide et une base au schéma
`0005`, exclusivement dans PostgreSQL de test isolé. Les lignes de
conception ci-dessous sont complétées par la preuve d'implémentation locale
et le réaudit final.

| ID | Exigence | Source | ADR | Spec | Code | Migration | Test | Statut | Version |
|---|---|---|---|---|---|---|---|---|---|
| BDP-019 | `PriceSchedule` est optionnel, unique par `Market` et regroupe les `PriceItem` du marché. | Décision produit LOT 2B §4 | ADR-LOT2B-001/004 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-020 | Un `PriceItem` porte un numéro opaque, désignation, unité, quantités et montants Decimal, lot optionnel, statut, notes et groupe optionnel. | Décision produit LOT 2B §§1,3,7 | ADR-LOT2B-001/004 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-021 | Un `PriceItem` appartient à zéro ou une formule via une FK nullable vers `RevisionGroup`, jamais plusieurs. | Principe cardinalité | ADR-LOT2B-001 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-022 | Aucun traitement révisable/non révisable n'est déduit de la désignation. | Décision produit LOT 2B §1 | ADR-LOT2B-002 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-023 | `PENDING_CLASSIFICATION`, `REVISABLE` et `NON_REVISABLE` imposent une cohérence stricte de l'affectation. | Décision produit LOT 2B §§1,2 | ADR-LOT2B-002 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-024 | L'affectation individuelle et bulk remplace l'ancien groupe dans une transaction. | Décision produit LOT 2B §§2,6 | ADR-LOT2B-003 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-025 | `Tout sélectionner` et `Tout désélectionner` n'introduisent aucune affectation multiple. | Décision produit LOT 2B §3 | ADR-LOT2B-003 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-026 | La cohérence inter-marchés est garantie par le backend/service ; une contrainte PostgreSQL n'est ajoutée que si elle est techniquement correcte. | Décision produit LOT 2B §5 | ADR-LOT2B-001/004 | architecture/DATA_MODEL.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-027 | Le numéro de prix est unique au niveau du marché via le `PriceSchedule OneToOne` et les doublons d'import sont rejetés avant écriture. | Décision produit LOT 2B §4 | ADR-LOT2B-004 | specs/04-bordereau-prix.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-028 | Les futurs décomptes copieront les données BDP et formule dans des snapshots sans être créés par LOT 2B. | Décision produit LOT 2B §6 | ADR-LOT2B-004 | architecture/DATA_MODEL.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| BDP-029 | Les imports futurs sont isolés sous `imports/price_schedule/`, avec écarts de montant signalés et jamais corrigés silencieusement. | Décision produit LOT 2B §7 | ADR-GOV-012, ADR-LOT2B-004 | architecture/API.md | — | — | revue documentaire | APPROVED | LOT2B-DESIGN |
| FRM-016 | Pour une formule simple mono-index `K=C+A×INDEX/INDEX0`, `A=1-C` est calculé avec Decimal ; cette règle ne s'applique pas automatiquement aux multi-index. | Décision produit LOT 2B §8 | ADR-LOT2B-005 | specs/03-formules.md; BLUEPRINT.md | — | — | revue documentaire | APPROVED | v0.6.1-DESIGN |
| BDP-030 | Le marché porte explicitement le mode `GLOBAL_FORMULA` ou `PRICE_ASSIGNMENT`; ce mode n'est pas déduit du nombre de formules. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-031 | `GLOBAL_FORMULA` permet une formule globale sans `PriceSchedule`/`PriceItem` obligatoire pour la révision. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-032 | `PRICE_ASSIGNMENT` rend le BDP nécessaire pour distinguer les formules et les prix sans révision. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-033 | Une seule formule avec des prix `NON_REVISABLE` reste en `PRICE_ASSIGNMENT`. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-034 | Les montants des futurs décomptes peuvent référencer directement la formule globale. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-035 | Les changements de mode sont contrôlés et ne suppriment aucune donnée silencieusement. | Décision métier finale LOT 2B | ADR-LOT2B-006 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |
| BDP-036 | La formule simple conserve la contrainte Decimal partie fixe + coefficients indicés = 1. | Décision métier finale LOT 2B | ADR-LOT2B-006, ADR-LOT2B-005 | plans/LOT-02B.md | — | — | revue documentaire | APPROVED | LOT2B-PLAN |

Les exigences `APPROVED` et `PLANNED` ne signifient pas que le code
correspondant existe. Aucun élément n'est marqué `IMPLEMENTED`, `TESTED`
ou `VALIDATED` sans preuve.
## LOT 1C — autorités, groupements et RC

Statut global : VALIDATED — v0.5.1. Preuve de migration pré/post validée ;
tests backend/frontend, build et diagnostic d'exploitation passés. v0.5.1
ajoute l'interface de gestion des groupements sans nouvelle migration DB.

| Exigence | Implémentation | Vérification |
|---|---|---|
| RC et ville du RC distincts | `Company.rc`, `Company.rc_city`, migration additive | tests Company + formulaire/détail frontend |
| Autorité structurée et autocomplete | `ContractingAuthority`, alias, lien CompanyAuthority, API | tests API de création, recherche et doublon |
| Titulaire individuel ou groupement | `Market.holder_type`, `holder_company`, `consortium` | tests migration et API |
| Groupement INGC/NAXU | Company réelles, MANDATAIRE/MEMBER, 50/50 Decimal | tests permissions NAXU |
| Isolation | accès via Membership active d’une société membre | tests absence/inactivation Membership |
| Historique futur | architecture snapshot prévue, moteur Revision hors périmètre | revue de conception — hors périmètre v0.5.0 |

## Interface Consortium v0.5.1

| Exigence | Implémentation | Vérification |
|---|---|---|
| Navigation et routes Groupements | `frontend/src/App.tsx`, `/app/consortia`, `/new`, `/:id`, `/:id/edit` | `frontend/src/App.test.tsx`, `frontend/src/consortia/ConsortiaPage.test.tsx` |
| Création et modification d'un groupement avec Company existantes | `frontend/src/consortia/ConsortiaPage.tsx`, API Consortium v0.5.0 | tests création INGC/NAXU, détail et modification |
| Membres, mandataire, retrait dynamique et quotes-parts | formulaire Consortium avec validation décimale sans float | tests frontend et validations backend existantes |
| Libellé Société gestionnaire | `frontend/src/markets/MarketForm.tsx` | `frontend/src/markets/MarketForm.test.tsx` |
| Conservation du schéma et des données historiques | aucune migration ajoutée | `makemigrations --check --dry-run`, `migrate --plan`, `make test` |

## Correctif d'affichage titulaire marché v0.5.2

| Exigence | Implémentation | Vérification |
|---|---|---|
| Distinguer titulaire contractuel et société gestionnaire | `frontend/src/markets/MarketsPage.tsx` utilise `holder_type`, `consortium_detail` et `holder_company_detail` ; `Market.company` reste affiché comme société gestionnaire | `frontend/src/markets/MarketsPage.test.tsx` — cas `SOLE_COMPANY` et `CONSORTIUM` |
| Afficher le Consortium titulaire sans le reconstruire depuis `Market.company` | Libellé `Titulaire : Groupement …` basé sur `consortium_detail` | tests frontend de non-confusion titulaire/gestionnaire |
| Préserver le comportement société seule | Titulaire basé sur `holder_company_detail` avec repli API existant | test frontend `SOLE_COMPANY` |

## Conception LOT 2A — formules contractuelles validée

Statut de conception : `APPROVED` après validation humaine. Cette section
conserve le référentiel de conception ; l'implémentation est tracée ci-dessous.

| Exigence | Conception validée | Code | Migration | Test prévu | Statut |
|---|---|---|---|---|---|
| FRM-004 | Une formule validée est immuable et une modification crée une nouvelle version | — | — | modification après validation, versionnage | APPROVED |
| FRM-005 | `MarketLot` reste indépendant de `RevisionGroup`; le futur `PriceItem` sera rattaché à un groupe en LOT 2B | — | — | plusieurs groupes dans un lot | APPROVED |
| FRM-006 | Index de base, provenance et période sont explicitement enregistrés | — | — | absence de base, provenance, aucune déduction | APPROVED |
| FRM-007 | Coefficients, indices et ratios utilisent Decimal avec stockage NUMERIC(18,8), sans float ni troncature prématurée | — | — | Decimal, précision et absence de float | APPROVED |
| FRM-008 | Le mode exact d'arrondi reste PENDING_VALIDATION et bloque seulement la sortie réglementaire définitive | — | — | politique centralisée, état bloquant | APPROVED |
| FRM-009 | Aucun `PriceItem` n'est créé en LOT 2A; la relation future est `PriceItem N → 1 RevisionGroup` | — | — | séparation LOT 2A/LOT 2B | APPROVED |

Les exigences réglementaires d'arrondi, d'index non publié et de date de
référence restent soumises aux statuts de `regulatory/`.

## Implémentation LOT 2A — formules contractuelles

Statut : `IMPLEMENTED — TESTED — FROZEN v0.6.0`. La migration est additive et
aucune donnée métier existante n'est créée automatiquement. Le moteur ne
produit pas encore de coefficient réglementaire définitif.

| Exigence | Implémentation | Migration | Tests | Statut |
|---|---|---|---|---|
| FRM-010 | `RevisionGroup` rattaché à `Market`, code unique par marché | `markets/0004...` | `RevisionFormulaApiTests` | IMPLEMENTED / TESTED |
| FRM-011 | `MarketFormula` versionnée avec DRAFT/VALIDATED/INACTIVE et bulk ORM contrôlé | `markets/0004...`; `backend/markets/models.py`; `backend/markets/serializers.py` | `RevisionFormulaApiTests::test_validated_formula_and_terms_are_immutable_through_orm`; `RevisionFormulaApiTests::test_draft_terms_remain_mutable_through_normal_orm_operations`; `FormulaVersionConcurrencyTests` | IMPLEMENTED / TESTED |
| FRM-012 | `FormulaTerm` multi-index ordonné, Decimal `NUMERIC(18,8)` et bulk ORM contrôlé | `markets/0004...`; `backend/markets/models.py` | `RevisionFormulaApiTests::test_validated_formula_and_terms_are_immutable_through_orm`; `test_domain_invariants_are_enforced_without_serializer` | IMPLEMENTED / TESTED |
| FRM-013 | API imbriquée et isolation par Market | `markets/urls.py`, `markets/views.py` | permissions OWNER/ADMIN/MEMBER, isolation | IMPLEMENTED / TESTED |
| FRM-014 | Section Formules de révision dans le détail marché | `frontend/src/markets/RevisionFormulaSection.tsx` | `frontend/src/markets/MarketsPage.test.tsx`; `npm run test`; `npm run build` | IMPLEMENTED / TESTED |
| FRM-015 | Aucun `PriceItem`, import BDP ou moteur réglementaire définitif | — | contrôle de périmètre | VALIDATED |

## Conception LOT 2A.1 — bibliothèque des modèles de formules

Statut : `IMPLEMENTED — TESTED — FROZEN v0.6.1`. La curation des templates
GLOBAL et la publication de sources officielles restent hors périmètre.

| Exigence | Décision / preuve attendue | Implémentation | Tests | Statut |
|---|---|---|---|---|
| TPL-001 | Séparation stricte template / formule marché | `specs/03A-formula-template-library.md`; `backend/markets/services.py` | `FormulaTemplateTests.test_copy_is_transactional_independent_and_preserves_traceability` | IMPLEMENTED / TESTED |
| TPL-002 | Famille stable et version unique | `backend/markets/models.py`; migration 0005 | tests modèle et migration | IMPLEMENTED / TESTED |
| TPL-003 | Cycle DRAFT/VERIFIED/DEPRECATED | `backend/markets/models.py` | tests modèle/API | IMPLEMENTED / TESTED |
| TPL-004 | Immutabilité d'une version VERIFIED | `DECISIONS.md`, ADR-LOT2A1-002 | `FormulaTemplateTests.test_verified_template_and_terms_are_immutable_through_orm` | IMPLEMENTED / TESTED |
| TPL-005 | GLOBAL prioritaire, COMPANY réservé ; lecture derrière une Membership active ou superuser | `backend/companies/permissions.py`; `backend/markets/views.py` | `FormulaTemplateTests.test_global_template_read_requires_active_membership_or_superuser` | IMPLEMENTED / TESTED |
| TPL-006 | Provenance et vérification explicites | `backend/markets/models.py`; API read-only | `FormulaTemplateTests.create_verified_template` | IMPLEMENTED / TESTED |
| TPL-007 | OFFICIAL n'implique pas VERIFIED | `backend/markets/models.py` | validation modèle et absence de seed | IMPLEMENTED / TESTED |
| TPL-008 | Termes simples/multi-index en Decimal | `backend/markets/models.py`; migration 0005 | tests Decimal templates/formules | IMPLEMENTED / TESTED |
| TPL-009 | Copie transactionnelle vers MarketFormula DRAFT | `backend/markets/services.py`; API | `FormulaTemplateTests.test_copy_is_transactional_independent_and_preserves_traceability` | IMPLEMENTED / TESTED |
| TPL-010 | Copie de structure, ordre, bases et provenance | `backend/markets/services.py` | test de contenu copié | IMPLEMENTED / TESTED |
| TPL-011 | Indépendance après copie | `backend/markets/services.py` | test d'indépendance | IMPLEMENTED / TESTED |
| TPL-012 | Aucune déduction métier/BAT3 en dur | aucun seed/moteur ajouté | contrôle de périmètre | IMPLEMENTED / TESTED |
| TPL-013 | IndexDefinition futur, aucun IndexValue/barème | aucun modèle correspondant | contrôle de périmètre | IMPLEMENTED / TESTED |
| TPL-014 | Historique conservé et DEPRECATED non par défaut | `backend/markets/models.py`; API | tests de suppression protégée | IMPLEMENTED / TESTED |

## Implémentation LOT 2B — validation et gel v0.7.0

Statut : `IMPLEMENTED — TESTED — VALIDATED — FROZEN`. Le commit, le tag et le
push du candidat v0.7.0 sont autorisés. Aucun déploiement, migration ou
changement de données de production n'est inclus.

| Exigence | Implémentation | Migration | Tests / preuve | Statut |
|---|---|---|---|---|
| BDP-019..BDP-022 | Modes explicites `GLOBAL_FORMULA` / `PRICE_ASSIGNMENT`, traitement et affectation contrôlés | `markets/0006...` | `Lot2BApiTests`, tests de transition, migration from zero/from 0005 | IMPLEMENTED / TESTED / VALIDATED |
| BDP-023..BDP-026 | `PriceSchedule`, `PriceItem`, statuts de classification, Decimal et numéro opaque | `markets/0006...` | `Lot2BApiTests`, suite backend | IMPLEMENTED / TESTED / VALIDATED |
| BDP-027..BDP-029 | Exclusivité d'affectation et opérations bulk transactionnelles | — | réaffectation F1→F2, sans révision, isolation | IMPLEMENTED / TESTED / VALIDATED |
| BDP-030..BDP-036 | API autoritaire, permissions et matrice métier | — | suite API et tests frontend marchés | IMPLEMENTED / TESTED / VALIDATED |
| FRM-016 | UX formules basée sur les templates, partie variable Decimal dérivée | — | `MarketsPage.test.tsx`, build frontend | IMPLEMENTED / TESTED / VALIDATED |

L'import Excel/CSV complet, les snapshots `StatementItem` et le moteur de
révision restent hors périmètre et ne sont pas introduits par LOT 2B.

## Référentiel V1 des indices

| Exigence | Implémentation | Preuve | Statut |
|---|---|---|---|
| IDX-001 | `IndexDefinition`, `IndexPublication`, `MonthlyIndexValue` | migration 0008, tests repository | IMPLEMENTED |
| IDX-002 | Decimal et unicité code/année/mois | contrainte DB et tests | IMPLEMENTED |
| IDX-003 | Import local idempotent avec `PENDING_VALIDATION` | `import_index_publication` | IMPLEMENTED |
| IDX-004 | Résolution exacte sans fallback mensuel | `resolve_index`, `resolve_base_index` | IMPLEMENTED |
| IDX-005 | API et écran Indices / Barèmes | routes markets et `IndicesPage` | IMPLEMENTED |

## API-02 — staging externe

| Exigence | Implémentation | Migration | Tests / preuve | Statut |
|---|---|---|---|---|
| IMP-API-001 | Client read-only et normalisation Decimal | — | tests client mockés | IMPLEMENTED / TESTED |
| IMP-API-002 | `ExternalIndexStaging`, provenance, hash, changement de source et statuts | `markets/0010_externalindexstaging.py`, `0011_externalindexstaging_change_trace.py` | tests staging/idempotence | IMPLEMENTED / TESTED |
| IMP-API-003 | Synchronisation explicite staging-only | — | commande dry-run, zéro écriture `MonthlyIndexValue` | IMPLEMENTED / TESTED |
| IMP-API-004 | Comparaison catalogue, local et évolution | — | rapports `MATCHED`, `CONFLICT`, `MISSING_LOCAL` | IMPLEMENTED / TESTED |
| IMP-API-005 | Consultation authentifiée filtrée | — | API staging et écran Indices | IMPLEMENTED / TESTED |

## IDX-01 — promotion contrôlée

| Exigence | Implémentation | Migration | Tests / preuve | Statut |
|---|---|---|---|---|
| Promotion explicite et idempotente | `markets/promotion.py`, `promote_revision_indices` | — | dry-run, apply ciblé, relance sans doublon | IMPLEMENTED / TESTED |
| Source externe distincte de l'officiel | `IndexPublication.source_type` | `markets/0012_indexpublication_source_type.py` | publication `EXTERNAL_SECONDARY` pending | IMPLEMENTED / TESTED |
| Protection des valeurs locales | aucune mise à jour automatique des conflits | — | tests conflit et valeur validée | IMPLEMENTED / TESTED |

Règle d'architecture : `EXTERNAL API != OFFICIAL LOCAL VALUE` et
`SYNC != VALIDATION`.

## IDX-02 — validation documentaire officielle

| Exigence | Implémentation | Migration | Tests / preuve | Statut |
|---|---|---|---|---|
| Hiérarchie OFFICIAL / EXTERNAL_SECONDARY / MANUAL_VALIDATED | `IndexPublication.source_type`, écran et serializers | 0012 | promotion + API/frontend | IMPLEMENTED |
| Document officiel, SHA256 et extraction revue | `IndexSourceDocument`, `RawIndexExtraction`, `OfficialExtractedValue` | 0013 | hash, extraction Decimal, document ambigu | IMPLEMENTED / TESTED |
| Comparaison OFFICIAL/API/local | `OfficialIndexValidationService`, `IndexValidationComparison` | 0013 | classifications triple, conflits | IMPLEMENTED / TESTED |
| Validation contrôlée et idempotente | `validate_official_indices --dry-run/--apply`, audit append-only | 0013 | duplicate, PENDING→DEFINITIVE, local protégé | IMPLEMENTED / TESTED |
| Résolution exacte sans fallback | `resolve_index`, `resolve_base_index` | — | base marché / mois absent | IMPLEMENTED / TESTED |
| Contrôle des six barèmes ciblés | dry-run ciblé des six PDF, archive non traitée en masse | — | BAT3 assertions de contrôle | READY FOR REVIEW |
## IDX-05 — Calcul limité aux indices définitifs

La politique V1 `CALCULATION_INDEX_POLICY=DEFINITIVE_ONLY` est gelée : seul
`MonthlyIndexValue.DEFINITIVE` alimente le calcul. Les statuts
`PROVISIONAL`, `PENDING_VALIDATION` et les mois absents restent traçables mais
sont exclus du resolver de calcul, sans fallback mensuel.

Implémentation : `markets.services.resolve_calculation_index`,
`resolve_base_index` et `markets.statement_services`.

## IDX-06 / CALC-01 — correction contrôlée du calcul SRM-SM

La formule simple est évaluée exclusivement en `Decimal` avec troncature
`ROUND_DOWN` à quatre décimales après chaque étape intermédiaire : `I/I₀`,
terme variable, `P/P₀`, puis `P/P₀ - 1`. Le résultat reste une PREVIEW
recalculable ; aucune révision définitive, promotion d'indice ou écriture de
production n'est effectuée par cette correction.

Implémentation : `markets.calculation_engine` et
`markets.statement_services`.
Preuves : `markets.test_calculation_engine` (golden BAT3) et
`markets.test_statements` (scénario SRM-SM, mois à zéro, août absent et
statuts non définitifs).
