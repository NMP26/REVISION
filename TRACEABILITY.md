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
| MKT-001 | Un marché supporte une formule unique. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-002 | Un marché supporte plusieurs formules. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-003 | Un marché peut contenir zéro à plusieurs lots. | Cahier cumulatif §6 | ADR-GOV-004 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-004 | Un marché permet de choisir le mode de gestion de la révision. | Cahier cumulatif §§2,9 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-005 | Un marché est rattaché à une société. | Cahier cumulatif §1 | ADR-GOV-001 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-006 | Un marché conserve la date d'ouverture des plis. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-007 | Un marché conserve l'époque de base. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-008 | Un marché conserve l'OS de commencement. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-009 | Un marché conserve le délai contractuel. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-010 | Un marché conserve la TVA. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-011 | Un marché conserve le montant HT. | Cahier cumulatif §2 | ADR-GOV-002 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| MKT-012 | Un marché conserve la règle et la date de référence des indices selon sa procédure. | Arrêté 3-302-15, art. 4 et 7 | ADR-REG-001 | specs/02-marches.md | — | — | TBD | APPROVED | REG-1.0 |
| LOT-001 | Un lot peut contenir plusieurs articles de prix. | Cahier cumulatif §6 | ADR-GOV-004 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| LOT-002 | Un lot n'est pas assimilé à une formule. | Cahier cumulatif §6 | ADR-GOV-004 | specs/02-marches.md | — | — | TBD | APPROVED | GOV-1.1 |
| FRM-001 | Un RevisionGroup pointe vers une MarketFormula. | Cahier cumulatif §3 | ADR-GOV-003 | specs/03-formules.md | — | — | TBD | APPROVED | GOV-1.1 |
| FRM-002 | Une MarketFormula peut utiliser plusieurs FormulaTerm et indices. | Cahier cumulatif §§3,11 | ADR-GOV-007 | specs/03-formules.md | — | — | TBD | APPROVED | GOV-1.1 |
| FRM-003 | Le moteur de formule n'a pas de dépendance structurelle à BAT3. | Cahier cumulatif §11 | ADR-GOV-007 | architecture/CALCULATION_ENGINE.md | — | — | TBD | APPROVED | GOV-1.1 |
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
| VEN-001 | La ventilation supporte ACTUAL_EXECUTION. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-002 | La ventilation supporte CALENDAR_DAY_PRORATA. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-003 | ACTUAL_EXECUTION est prioritaire si les montants réels sont disponibles. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-004 | CALENDAR_DAY_PRORATA est un repli justifié si la répartition réelle est impossible. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| VEN-005 | Méthode, valeurs proposées/retenues et justification sont conservées pour audit. | Cahier cumulatif §10 | ADR-GOV-009 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-001 | Un calcul multi-formules agrège les StatementItems par RevisionGroup. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-002 | Le système contrôle la concordance entre les articles et le montant du décompte. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-003 | Le système contrôle la concordance des montants révisables et hors calcul. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-004 | Le système contrôle la concordance avec le total concerné. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-005 | Le calcul applique la formule du groupe après ventilation. | Cahier cumulatif §9 | ADR-GOV-002 | specs/07-revision-prix.md | — | — | TBD | APPROVED | GOV-1.1 |
| REV-006 | Les calculs financiers utilisent Decimal côté Python et NUMERIC/DECIMAL côté PostgreSQL. | Blueprint §2 | ADR-GOV-007 | architecture/CALCULATION_ENGINE.md | socle partiel | — | TBD | APPROVED | GOV-1.1 |
| REV-007 | Le résultat de révision est explicable par groupe, formule et période. | Cahier cumulatif §§9,14 | ADR-GOV-011 | specs/07-revision-prix.md | — | — | TBD | PLANNED | GOV-1.1 |
| REV-008 | Une révision est appliquée aux prestations à exécuter sans demande spéciale du titulaire. | Arrêté 3-302-15, art. 9 | ADR-REG-001 | specs/07-revision-prix.md | — | — | TBD | PLANNED | REG-1.0 |
| REV-009 | En cas de retard imputable, le calcul compare le coefficient du mois réel au coefficient du dernier mois contractuel et retient le plus faible. | Arrêté 3-302-15, art. 18 | ADR-REG-001 | specs/07-revision-prix.md | — | — | TBD | PLANNED | REG-1.0 |
| IDX-001 | Le référentiel distingue IndexDefinition et IndexValue. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-002 | IndexValue conserve code, désignation, mois et valeur. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
| IDX-003 | IndexValue conserve statut, publication, source et historique. | Cahier cumulatif §12 | ADR-GOV-007 | specs/08-indices-baremes.md | — | — | TBD | APPROVED | GOV-1.1 |
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

Les exigences `APPROVED` et `PLANNED` ne signifient pas que le code
correspondant existe. Aucun élément n'est marqué `IMPLEMENTED`, `TESTED`
ou `VALIDATED` sans preuve.
