STATUS: LOT 1B APPROVED — LOT 2A/2A.1 FROZEN — LOT 2B DESIGN APPROVED
IMPLEMENTATION: LOT 1B IMPLEMENTED ; LOT 2A/2A.1 IMPLEMENTED — TESTED ; LOT 2B NOT AUTHORIZED
SOURCE: ADR-LOT1B-001, ADR-LOT2A-001, ADR-LOT2B-001..005, specs/02-marches.md, specs/03-formules.md, specs/04-bordereau-prix.md

# Modèle de données LOT 1B

Cette description est architecturale. Elle n'est ni un modèle Django ni
une migration.

## Market

```text
Market
  company: FK Company, obligatoire
  market_number: obligatoire
  contracting_authority: obligatoire
  subject: obligatoire
  amount_ht: Decimal(18,2), nullable, >= 0
  vat_rate: Decimal, 0..100, pourcentage humain
  formula_structure: SINGLE | MULTIPLE
  date_limite_remise_offres: nullable
  date_ouverture_plis: nullable
  date_signature: nullable
  date_os_commencement: nullable
  contract_duration_value: entier > 0, nullable
  contract_duration_unit: DAYS | MONTHS, nullable
  status: ACTIVE | ARCHIVED, défaut ACTIVE
  timestamps
```

Contraintes : `UniqueConstraint(company, market_number)` et cohérence
des deux champs de délai (tous deux présents ou tous deux absents).
`MONTHS` n'est pas converti en jours par une constante arbitraire.

Les dates sont des FACTS. La date réglementaire de référence, si elle
est requise par une procédure validée, relève des RULES de
`regulatory/` et du moteur de calcul ; elle n'est pas déduite ou imposée
par le modèle LOT 1B.

## MarketLot

```text
MarketLot
  market: FK Market, obligatoire
  lot_number / code: obligatoire
  title: obligatoire
  description: nullable
  amount_ht: Decimal(18,2), nullable
  display_order: entier >= 0
  active: bool, défaut true
  notes: nullable
  timestamps
```

Contrainte : `UniqueConstraint(market, lot_number)`. Aucune FK vers
`MarketFormula`, aucun `has_lots` persistant, aucun lot fictif
automatique et aucun contrôle automatique de somme avec
`Market.amount_ht`.

## Relations inter-lots

```text
Company 1 ─── N Market 1 ─── N MarketLot
                         ├── N RevisionGroup       (lot ultérieur)
                         ├── N MarketFormula       (lot ultérieur)
                         └── N WorkSuspension      (événements futurs)

MarketLot ─── N PriceItem ─── RevisionGroup ─── MarketFormula
                                      (lots ultérieurs)
```

`MarketLot` est une structure contractuelle indépendante d'une formule.
Les relations vers `RevisionGroup`, `PriceSchedule`, `PriceItem` et
`MarketFormula` restent compatibles avec les lots futurs, sans être
créées par cette phase.

## Décompte V1 et ventilation temporelle

Le décompte V1 est une enveloppe HT simple portant seulement le numéro, la
date, le montant HT et l'observation facultative. Il ne doit pas détourner
`StatementItem` ou `PriceItem` pour représenter la ventilation temporelle.
La structure conceptuelle dédiée est :

```text
Statement
  └── MonthlyWorkAllocation
        year
        month
        work_days
```

`MonthlyWorkAllocation` conserve aussi les mois à zéro jour. Les montants
mensuels dérivés sont calculés en `Decimal` et leur somme doit égaler
exactement le montant HT du `Statement`, avec correction explicite de
l'écart d'arrondi sur la dernière ligne si nécessaire. Cette description
est architecturale uniquement ; elle ne crée ni modèle Django ni migration.

## Conception LOT 2A — formules contractuelles

Cette section est une proposition de conception ; elle n'est ni un modèle
Django ni une migration.

```text
Market 1 ─── N RevisionGroup
RevisionGroup 1 ─── N MarketFormula
MarketFormula 1 ─── N FormulaTerm
MarketLot 1 ─── N PriceItem (LOT 2B)
PriceItem N ─── 1 RevisionGroup (LOT 2B)
```

`RevisionGroup` appartient directement au marché afin qu'un lot puisse
contenir plusieurs groupes. Le rattachement des articles du BDP sera
explicitement réalisé par `PriceItem.revision_group` dans un lot
ultérieur. `MarketLot` n'a pas de FK obligatoire vers une formule.

### RevisionGroup proposé

```text
id UUID
market FK Market
code unique par market
name
description nullable
sort_order
active
notes nullable
timestamps
```

### MarketFormula proposé

```text
id UUID
revision_group FK RevisionGroup
version_number unique par revision_group
label
expression_display
constant_term NUMERIC(18,8)/Decimal
status DRAFT | VALIDATED | INACTIVE
valid_from nullable
valid_to nullable
validated_at nullable
reference_period_year nullable
reference_period_month nullable
reference_rule_code nullable
reference_source nullable
created_by
timestamps
```

La relation versionnée est 1→N. Une formule validée ne doit pas être
réécrite. L'invariant approuvé est qu'aucune date ne puisse avoir deux
versions `VALIDATED` applicables de manière ambiguë ; la règle détaillée
de sélection temporelle sera finalisée avec le moteur de révision.

### FormulaTerm proposé

```text
id UUID
formula FK MarketFormula
position unique par formula
coefficient NUMERIC(18,8)/Decimal
term_type
index_code
base_period_year nullable
base_period_month nullable
base_value NUMERIC(18,8)/Decimal nullable
base_source nullable
reference_note nullable
timestamps
```

Les champs d'indices, coefficients et calculs utilisent Decimal/NUMERIC,
avec une précision de stockage de base `NUMERIC(18,8)` documentée. Aucun
float n'est autorisé et cette précision de stockage ne constitue pas la
règle réglementaire d'arrondi : aucune troncature prématurée ne doit être
introduite. Les futures révisions copieront les données du
groupe, de la formule, des termes et des indices utilisés dans un
snapshot immuable ; une FK vivante vers la formule courante ne suffit pas.
Une formule `VALIDATED` est fonctionnellement immuable ; une formule
utilisée ou référencée n'est jamais supprimée physiquement. Les modèles LOT
2A refusent les opérations ORM bulk (`bulk_create`, `bulk_update` et
`update`) qui ne peuvent pas appliquer les validations de domaine ; les
créations et mutations passent par le service métier. Cette protection est
applicative/ORM contrôlée, pas une garantie contre du SQL direct ou un
administrateur de base.

Les index LOT 2A sont limités aux requêtes observées : les contraintes
d'unicité fournissent les index de recherche par marché/code,
groupe/version et formule/position ; l'index composite
`MarketFormula(revision_group, status)` accélère le contrôle des versions
`VALIDATED` applicables. Aucun index supplémentaire n'est ajouté sans
requête métier correspondante.

## LOT 2A.1 — bibliothèque de modèles implémentée

LOT 2A.1 sépare strictement le modèle partagé de la formule contractuelle.
`FormulaTemplate` est une version de famille identifiée par
`family_key + version_number`; `FormulaTemplateTerm` porte ses termes
ordonnés. La portée `GLOBAL` est implémentée en priorité. Un champ de portée
et une société propriétaire nullable réservent `COMPANY` sans l'activer.

Une version `VERIFIED` est immuable. Une copie transactionnelle vers un
`MarketFormula DRAFT` du marché recopie les valeurs et les termes. La
formule marché ne dépend ensuite plus du template ; seuls
`source_template_id` et `source_template_version` servent à la traçabilité.
`DEPRECATED` conserve l'historique et n'est plus proposé par défaut.

Les templates portent une provenance `OFFICIAL`, `CONTRACT_EXAMPLE` ou
`INTERNAL`, sans confondre `OFFICIAL` et `VERIFIED`. Aucun template officiel
n'est préchargé sans vérification documentaire.

## Référentiel V1 des indices

Le référentiel partagé est additif et indépendant des marchés :

```text
IndexDefinition 1 ─── N MonthlyIndexValue N ─── 1 IndexPublication
```

`IndexDefinition` porte le code, la désignation, la famille et l'état actif.
`IndexPublication` trace le barème mensuel source. `MonthlyIndexValue` porte
une valeur `NUMERIC(18,8)`/Decimal, son statut (`DEFINITIVE`, `PROVISIONAL`
ou `PENDING_VALIDATION`) et la publication source. La contrainte unique est
`(index_definition, year, month)`. La résolution recherche exactement le
code et le mois demandés : aucun mois précédent/suivant n'est utilisé.
L'import local est idempotent et toute ambiguïté reste en validation différée.

## Permissions

La persistance et l'API réutiliseront `Membership` actif du LOT 1A :
`OWNER`/`ADMIN` pour create/update, `MEMBER` pour read, aucun accès sans
membership actif, avec l'exception superuser Django existante.
## Évolution LOT 1C — référentiel et groupements

Les modèles `ContractingAuthority`, `AuthorityAlias`, `CompanyAuthority`, `Consortium` et `ConsortiumMember` sont additifs et désactivables logiquement. `Market.company` reste la société de dossier pendant la migration progressive ; `holder_type` et le couple `holder_company`/`consortium` portent le titulaire avec une contrainte DB exclusive. Les futures révisions devront copier les noms, membres, mandataire et quotes-parts dans un snapshot immuable ; elles ne devront pas dépendre des FK vivantes.

## Conception LOT 2B — bordereau et affectation

Cette section est documentaire uniquement. Aucun modèle Django, aucune
migration et aucune table n'est créée par la présente phase.

```text
Market 1 ─── 0..1 PriceSchedule 1 ─── N PriceItem ─── 0..1 RevisionGroup
RevisionGroup 1 ─── N MarketFormula (versions)
MarketLot 1 ─── N PriceItem (optionnel)
```

`PriceSchedule` est le bordereau explicite d'un marché. `PriceItem` conserve
`price_number` comme chaîne opaque, sa désignation, unité, quantité estimée,
PU HT, montant estimé HT, lot optionnel, statut de classification, groupe
optionnel, actif et notes. Quantités et montants sont Decimal/NUMERIC ;
aucun float n'est autorisé.

Le rattachement à une formule est une FK nullable vers `RevisionGroup`, pas
vers `MarketFormula` et pas vers une table de liaison. Le groupe reste le
concept technique stable ; l'interface utilise « Formule de révision ». Une
ligne sans FK n'est pas automatiquement révisable ou non révisable.
`PENDING_CLASSIFICATION`, `REVISABLE` et `NON_REVISABLE` sont obligatoires :
`REVISABLE` exige un groupe avant calcul/validation, `NON_REVISABLE` interdit
un groupe et `PENDING_CLASSIFICATION` interdit toute affectation définitive.

Les lots ne possèdent aucune formule. Le service/backend validera que le lot
et le groupe appartiennent au marché du bordereau. Une contrainte PostgreSQL
inter-tables ne sera ajoutée que si une implémentation correcte est démontrée
; aucune contrainte artificielle ou partielle ne doit être présentée comme
une garantie.

`UNIQUE(price_schedule, price_number)` est la contrainte proposée : les
numéros `00001`, `A-001` et `1.2.3` restent des chaînes. Les doublons
d'import sont rejetés avant écriture, sans suffixe ni écrasement.

Une formule utilisée n'est pas supprimée physiquement. Une version validée
reste immuable et une évolution crée une nouvelle `MarketFormula` dans le
même groupe. Les futurs `StatementItem` copieront, au moment de la
validation, les données du prix, son statut, son groupe et la formule/version
applicable dans un snapshot ; LOT 2B ne crée pas ces modèles.

## API-02 — staging des indices externes

`ExternalIndexStaging` est séparé du référentiel officiel. Il conserve le
fournisseur, l'endpoint, la récupération, le code, la période, la valeur
brute, sa normalisation Decimal, un hash du payload, la comparaison locale et
l'état de validation. La clé métier est
`(source_provider, source_endpoint, external_code, year, month)`.

`revisiondesprix.ma` reste une source candidate : elle ne crée pas
automatiquement d'`IndexDefinition`, ne modifie pas `MonthlyIndexValue` et ne
rend jamais une valeur `DEFINITIVE`. `SYNC` et `VALIDATION` sont distincts.

IDX-01 ajoute `IndexPublication.source_type` (`OFFICIAL`,
`EXTERNAL_SECONDARY`, `MANUAL_VALIDATED`). Une promotion externe crée une
publication `EXTERNAL_SECONDARY` en `PENDING_VALIDATION`, jamais une fausse
publication officielle.
