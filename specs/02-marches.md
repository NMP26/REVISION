STATUS: APPROVED — DESIGN / IMPLEMENTED
IMPLEMENTATION: IMPLEMENTED — TESTED, NON VALIDATED
SOURCE: ADR-LOT1B-001, décisions LOT 1B approuvées

# Marchés et lots

## 1. Market

`Market` est rattaché obligatoirement à `Company` par `company`.
Pour sécuriser l'isolation et simplifier PATCH, `company` est immuable
après la création du marché.

Champs obligatoires :

- `market_number` ;
- `contracting_authority` ;
- `subject`.

`amount_ht` est un `Decimal(18,2)` nullable à la création et doit être
supérieur ou égal à zéro lorsqu'il est renseigné. `vat_rate` est un
Decimal stocké en pourcentage humain (`20.00` signifie `20 %`) avec la
contrainte métier `0 <= vat_rate <= 100`; aucun taux n'est hardcodé.

Les dates factuelles suivantes sont nullables :

- `date_limite_remise_offres` ;
- `date_ouverture_plis` ;
- `date_signature` ;
- `date_os_commencement`.

Aucune date ne doit être inventée. Aucune de ces dates n'est
automatiquement la date réglementaire de référence de la révision.
`Market` conserve les faits ; les règles dépendantes de la procédure
appartiennent à `regulatory/` et au moteur de calcul.

Le délai est porté par `contract_duration_value` et
`contract_duration_unit`, dont l'unité vaut `DAYS` ou `MONTHS`. Les deux
champs sont renseignés ensemble ou tous deux absents. La valeur est un
entier strictement positif lorsqu'elle existe. `MONTHS` n'est jamais
converti en jours par multiplication par 30.

`formula_structure` vaut `SINGLE` ou `MULTIPLE` et décrit uniquement la
structure contractuelle. Il ne crée ni ne contient une formule.

`status` vaut `ACTIVE` ou `ARCHIVED`, avec `ACTIVE` par défaut. Il n'y a
pas de statut `SUSPENDED`; les suspensions/reprises futures sont des
événements `WorkSuspension` distincts.

Le numéro est unique par société uniquement :
`UniqueConstraint(company, market_number)`. L'unicité globale n'est pas
retenue dans LOT 1B et pourra être réévaluée sur preuve d'un cas réel.

## 2. MarketLot

`MarketLot` possède une FK obligatoire vers `Market` et les champs :

- `lot_number` / `code`, obligatoire ;
- `title`, obligatoire ;
- `description`, optionnelle ;
- `amount_ht Decimal(18,2)`, nullable ;
- `display_order`, entier supérieur ou égal à zéro ;
- `active`, booléen, défaut `true` ;
- `notes`, optionnelles ;
- timestamps.

La contrainte est `UniqueConstraint(market, lot_number)`. Aucun lot
fictif n'est créé automatiquement. Aucun champ persistant `has_lots` n'est
prévu. Aucun contrôle automatique ne compare la somme des montants de
lots au montant du marché. `MarketLot` n'a aucune FK vers
`MarketFormula`.

## 3. Permissions

Le contrôle réutilise `Membership` du LOT 1A :

- `OWNER` et `ADMIN` actifs : création et modification de `Market` et
  `MarketLot` ;
- `MEMBER` actif : lecture ;
- sans `Membership` actif : aucun accès métier ;
- superuser Django : exception administrative système existante.

Aucun second système RBAC n'est créé.

## 4. Compatibilité inter-lots

Le design reste compatible avec `RevisionGroup`, `PriceSchedule`,
`PriceItem` et les formules futures, sans introduire ces relations dans
le modèle LOT 1B. La séparation `MarketLot != MarketFormula` est
obligatoire.

## 5. État et périmètre

Les champs, cardinalités, contraintes et permissions ci-dessus sont
APPROVED au niveau design. L'implémentation backend, les migrations,
l'API réelle, le frontend et les tests LOT 1B sont PLANNED et ne sont pas
créés dans cette phase.
