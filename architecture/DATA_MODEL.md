STATUS: APPROVED — IMPLEMENTED
IMPLEMENTATION: IMPLEMENTED — TESTED, NON VALIDATED
SOURCE: ADR-LOT1B-001, specs/02-marches.md

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

## Permissions

La persistance et l'API réutiliseront `Membership` actif du LOT 1A :
`OWNER`/`ADMIN` pour create/update, `MEMBER` pour read, aucun accès sans
membership actif, avec l'exception superuser Django existante.
## Évolution LOT 1C — référentiel et groupements

Les modèles `ContractingAuthority`, `AuthorityAlias`, `CompanyAuthority`, `Consortium` et `ConsortiumMember` sont additifs et désactivables logiquement. `Market.company` reste la société de dossier pendant la migration progressive ; `holder_type` et le couple `holder_company`/`consortium` portent le titulaire avec une contrainte DB exclusive. Les futures révisions devront copier les noms, membres, mandataire et quotes-parts dans un snapshot immuable ; elles ne devront pas dépendre des FK vivantes.
