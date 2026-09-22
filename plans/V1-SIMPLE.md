STATUS: V1-A IMPLEMENTED LOCALLY — V1-B+ NOT AUTHORIZED
SCOPE: V1 opérationnelle simple
PREREQUIS: validation produit explicite avant développement

# V1 simple — décompte financier sans détail de prestations

## Décision finale de périmètre

```text
V1_MODEL: ONE_MARKET_ONE_FORMULA
STATEMENT_MODEL: SIMPLE_HT_AMOUNT
STATEMENT_DETAIL: NO
WORK_DAYS_BY_MONTH: YES
MONTHLY_AMOUNT_FROM_WORK_DAYS: YES
LOTS: NO
BDP: NO
MULTI_FORMULA: NO
PRICE_ITEMS: NO
```

Cette décision produit réduit le parcours opérationnel V1 à une formule
unique appliquée à une enveloppe financière HT. Elle ne supprime aucune
structure avancée déjà présente dans l'architecture ; elle les retire
uniquement du parcours utilisateur V1.

## Parcours cible

```text
Marché
  → formule unique du marché
  → OS / calendrier
  → décompte financier
  → jours de travaux par mois
  → ventilation du montant HT
  → indices mensuels
  → calcul de révision
  → validation
  → historique / documents
```

## Modèle V1 du décompte

Le décompte V1 est une enveloppe financière HT rattachée directement au
marché. Il contient uniquement :

- numéro du décompte ;
- date du décompte ;
- montant HT en `Decimal` ;
- observation facultative.

Le décompte V1 ne contient aucun article, prix, quantité, unité, lot,
`PriceItem`, `StatementItem`, `RevisionGroup`, affectation ou détail de
prestation. Les dates de période et l'OS/calendrier restent des données du
marché et de son exécution ; elles ne sont pas des champs supplémentaires
du `Statement` V1.

## Jours de travaux par mois

La ventilation temporelle est une donnée du calcul, indépendante du détail
des prestations. Pour chaque mois concerné par la note de calcul, notamment
entre l'OS de commencement et la date de fin du décompte, le décompte
conserve une allocation mensuelle explicite :

- année ;
- mois ;
- nombre de jours de travaux, en entier positif ou nul.

Tous les mois concernés restent visibles, y compris ceux à zéro jour. Le
total des jours doit être contrôlé avant le calcul. La structure conceptuelle
future est :

```text
Statement
  └── MonthlyWorkAllocation
        - year
        - month
        - work_days
```

Cette structure ne doit pas détourner `StatementItem` ou `PriceItem`.

Le montant HT mensuel à réviser est calculé par :

```text
Montant_mois = Montant_HT × Jours_mois / Total_jours
```

Toutes les opérations financières utilisent `Decimal`, sans conversion
silencieuse en float. La somme des montants mensuels doit être exactement
égale au montant HT du décompte. L'écart d'arrondi éventuel est traité
explicitement sur la dernière ligne/mois afin de préserver cette égalité.

Une période mono-mois conserve également sa ligne mensuelle explicite.

## Tableau de calcul V1

La note de calcul V1 doit pouvoir présenter au minimum :

- décompte ;
- montant travaux cumulés HT ;
- montant travaux HT ;
- date ;
- mois ;
- nombre de jours ;
- total des jours ;
- index ;
- ratio `I / I₀` ;
- coefficient `K` ;
- `K - 1` ;
- montant à réviser ;
- montant de la révision.

Un indice manquant est affiché `Index non disponible` et bloque le calcul ;
aucune valeur n'est inventée, reprise silencieusement ou remplacée par le
mois précédent.

Le montant des travaux cumulés HT est calculé à partir des décomptes
successifs ; il n'est pas ressaisi manuellement.

## Référentiel des indices V1

Le parcours formule unique lit `date_limite_remise_offres`, le code du
`FormulaTerm`, puis résout exactement `MonthlyIndexValue(code, année, mois)`.
Les valeurs sont Decimal et liées à `IndexPublication`. L'import local CSV
est idempotent et les ambiguïtés restent `PENDING_VALIDATION`. Le moteur de
révision, les décomptes et les snapshots restent hors périmètre.

## Calcul V1

Le calcul V1 utilise :

```text
Market
  + formule unique
  + décompte montant HT
  + période
  + jours de travaux par mois
  + indices correspondants
```

Pour une formule simple :

```text
K = 0,15 + 0,85 × I / I₀
Montant révisé = P₀ × K
Révision = P₀ × (K - 1)
```

La formule unique reste structurée par `MarketFormula` et `FormulaTerm`.
Le décompte ne dépend pas de `PriceSchedule`, `PriceItem`, `MarketLot` ou
`RevisionGroup`.

## Reporté après stabilisation V1

- plusieurs formules dans un marché ;
- affectation prix par prix ;
- `PriceSchedule` / `PriceItem` dans le parcours décompte ;
- détail de prestations dans le décompte ;
- BDP manuel, Excel ou CSV ;
- quantités, unités et prix unitaires ;
- `StatementItem` détaillé ;
- `PENDING_CLASSIFICATION` et `NON_REVISABLE` au niveau article ;
- formules complexes et termes `SALARY`.

Ces éléments restent conservés dans les modèles, API, migrations et
documents d'architecture existants lorsqu'ils sont déjà présents.

## Lots courts proposés

1. V1-A — marché simple + formule unique ; masquer le parcours
   multi-formules dans le parcours V1. IMPLEMENTED LOCALLY.
2. V1-B — implémenter le décompte simple HT et ses permissions.
3. V1-C — implémenter les allocations `MonthlyWorkAllocation`, mois à zéro
   inclus, contrôle du total, prorata Decimal et correction explicite de
   l'écart d'arrondi sur la dernière ligne.
4. V1-D — implémenter les indices simples base/courants.
5. V1-E — implémenter le calcul Decimal et le contrôle du résultat.
6. V1-F — implémenter validation, historique et snapshots.
7. V1-G — implémenter les documents.
8. V1-H — valider le scénario complet de bout en bout.

## Migrations

La présente décision ne crée aucune migration. Une éventuelle migration
future pour `MonthlyWorkAllocation` devra être additive, non destructive et
présentée avant le développement de V1-C.

```text
FIRST_IMPLEMENTATION_LOT: V1-A — marché simple + formule unique
MONTHLY_WORK_DAYS_IMPLEMENTATION_LOT: V1-C — décompte / allocations mensuelles
```

## API-02 — référentiel externe candidat

La synchronisation de `revisiondesprix.ma` est hors runtime métier. Elle
alimente uniquement `ExternalIndexStaging`, avec comparaison locale et
validation différée. Une valeur externe n'est jamais promue automatiquement
en valeur officielle.
