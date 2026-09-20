STATUS: LOT 1B APPROVED — LOT 2A FROZEN v0.6.0
IMPLEMENTATION: LOT 1B IMPLEMENTED ; LOT 2A IMPLEMENTED — TESTED — FROZEN v0.6.0
SOURCE: specs/02-marches.md, specs/03-formules.md, ADR-LOT2A-001

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

## API LOT 2A — contrat implémenté et gelé en v0.6.0

Les routes LOT 2A suivantes sont disponibles dans l'implémentation courante :

- `GET/POST /api/markets/{market_id}/revision-groups/`
- `GET/PATCH /api/markets/{market_id}/revision-groups/{group_id}/`
- `GET/POST /api/markets/{market_id}/revision-groups/{group_id}/formulas/`
- `GET/PATCH /api/markets/{market_id}/revision-groups/{group_id}/formulas/{formula_id}/`

Les mutations seront réservées aux OWNER/ADMIN actifs de la société du
marché. MEMBER pourra lire selon les permissions du marché. Un groupe ou
une formule d'une autre société ne doit jamais être exposé.

Une formule VALIDATED est immuable par API et par les chemins ORM contrôlés
des modèles LOT 2A. `save()`, `update()`, `bulk_update()`, `bulk_create()`
et les suppressions applicables refusent les opérations qui contourneraient
cet invariant ; les créations et mutations passent par le service métier.
Cette garantie est applicative et ORM : elle ne constitue pas une protection
absolue contre du SQL direct ou une connexion administrateur PostgreSQL.
Une nouvelle modification créera une version ; aucune route ne devra
réécrire silencieusement une version déjà utilisée par une future révision.

Les réponses exposeront les valeurs Decimal sous forme de chaînes JSON,
les termes dans leur ordre, `version_number`, `status`, `valid_from`,
`valid_to`, `created_at` et `validated_at` lorsque présents, ainsi que la
provenance de la valeur de base. Les états explicites `PENDING_INDEX` ou
`ROUNDING_POLICY_PENDING` seront utilisés lorsque le calcul n'est pas
disponible. LOT 2A ne crée ni `PriceItem` ni API d'import BDP.

## API LOT 2A.1 — bibliothèque des modèles implémentée

Les routes suivantes sont implémentées pour la consultation et la copie :

- `GET /api/formula-templates/` : liste filtrable des templates `GLOBAL` visibles ; les `DEPRECATED` restent consultables mais ne sont pas proposés par défaut.
- `GET /api/formula-templates/{template_id}/` : détail, version, provenance et aperçu des termes.
- `POST /api/markets/{market_id}/revision-groups/{group_id}/formulas/from-template/` : copie transactionnelle d'un template `VERIFIED` vers une `MarketFormula DRAFT` indépendante.

La copie exige les permissions d'écriture déjà prévues pour le marché et ne
crée aucun lien fonctionnel de calcul avec le template. Les valeurs Decimal
sont sérialisées comme chaînes JSON. L'administration des templates et la
portée `COMPANY` nécessitent une décision de permissions dédiée dans un lot
ultérieur ; aucune route ne doit exposer une modification d'une version
`VERIFIED`.
## API LOT 1C

- `GET/POST /api/authorities/` : autocomplétion et création explicite d’un maître d’ouvrage, limitée à une société accessible et administrable.
- `PATCH /api/authorities/<id>/` : désactivation ou correction sans suppression historique.
- `GET/POST /api/consortia/` : lecture des groupements accessibles et création par un OWNER/ADMIN de la société dossier.
- `GET/PATCH /api/consortia/<id>/` : lecture et gestion contrôlée des membres actifs.
- `Market` expose `holder_type`, `holder_company`, `consortium` et les résumés associés ; `contracting_authority` reste disponible pendant la transition.
