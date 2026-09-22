STATUS: DESIGN APPROVED — LOT 2A FROZEN v0.6.0
IMPLEMENTATION: LOT 2A IMPLEMENTED — TESTED — FROZEN v0.6.0
SOURCE: BLUEPRINT §§10–11, ADR-GOV-003, ADR-GOV-005, ADR-GOV-007, ADR-REG-001, ADR-LOT2B-005

# Formules contractuelles — LOT 2A

Cette spécification conserve le contrat de conception et les garanties du
lot LOT 2A implémenté en v0.6.0. La bibliothèque de modèles est spécifiée
séparément dans `specs/03A-formula-template-library.md` et n'est pas
incluse dans l'implémentation LOT 2A.

## 1. Principes métier

### Parcours V1-A — formule unique

Dans le parcours V1, un marché `SINGLE` sélectionne une seule formule
contractuelle simple depuis le catalogue. Le code, la désignation et
l'expression sont affichés ; l'utilisateur ne choisit pas entre une et
plusieurs formules et ne manipule ni `RevisionGroup` ni `FormulaTerm` comme
objets métier. La structure interne versionnée existante est conservée pour
la compatibilité et l'historique futurs.

Un marché ne porte pas nécessairement une seule formule. La structure
existante `Market.formula_structure` (`SINGLE` ou `MULTIPLE`) ne constitue
pas une formule et ne doit pas être remplacée par une chaîne calculable.

Les relations proposées sont :

```text
Market
 ├── RevisionGroup 1 ─── N MarketFormula (versions)
 ├── MarketLot 0..N
 └── PriceItem 0..N (futur LOT 2B)

PriceItem N ─── 1 RevisionGroup (futur LOT 2B)
MarketFormula 1 ─── N FormulaTerm
```

`RevisionGroup` représente un groupe contractuel de prestations soumis à
la même formule. Il appartient directement au marché et n’appartient pas
à un lot. Un lot peut donc contenir plusieurs groupes, et un groupe peut
regrouper des articles de plusieurs lots si le futur BDP le permet.
`MarketLot` reste indépendant de toute formule.

## 2. RevisionGroup

Champs proposés :

| Champ | Type proposé | Règle |
|---|---|---|
| `id` | UUID | Identité stable. |
| `market` | FK `Market` | Obligatoire ; le groupe ne change pas de marché. |
| `code` | chaîne | Obligatoire dans le marché, unique par marché. |
| `name` | chaîne | Libellé contractuel lisible. |
| `description` | texte | Optionnelle. |
| `sort_order` | entier | Ordre d’affichage non métier. |
| `active` | booléen | Désactivation logique, jamais suppression physique si référencé. |
| `notes` | texte | Optionnelles. |

Un groupe doit avoir au moins une formule validée pour être utilisable
dans un futur calcul. Un groupe DRAFT peut exister sans formule validée.
Un groupe ne reçoit pas de FK obligatoire vers `MarketLot`.

## 3. MarketFormula et versionnage

La cardinalité retenue est `RevisionGroup 1 → N MarketFormula`, et non
`1 → 1`. Une nouvelle modification contractuelle crée une nouvelle
version ; elle ne réécrit pas une formule déjà utilisée.

Champs proposés :

| Champ | Type proposé | Règle |
|---|---|---|
| `id` | UUID | Identité immuable de la version. |
| `revision_group` | FK `RevisionGroup` | Obligatoire. |
| `version_number` | entier positif | Unique par groupe, croissant. |
| `label` | chaîne | Nom de la formule. |
| `expression_display` | chaîne | Représentation lisible, jamais source unique du calcul. |
| `constant_term` | NUMERIC(18,8)/Decimal | Constante `C`. Précision de stockage acceptée ; elle ne constitue pas la règle réglementaire d’arrondi. |
| `status` | enum | `DRAFT`, `VALIDATED`, `INACTIVE`. |
| `valid_from` | date nullable | Début de validité contractuelle explicite si connu. |
| `valid_to` | date nullable | Fin de validité explicite si le contrat la prévoit ; aucune sélection temporelle automatique n’est construite dans LOT 2A. |
| `reference_period_year` | entier nullable | Année de référence enregistrée explicitement. |
| `reference_period_month` | entier nullable | Mois 1–12 si la période est mensuelle. |
| `reference_rule_code` | chaîne nullable | Provenance/règle contractuelle, sans dérivation implicite. |
| `reference_source` | texte nullable | Source CPS, contrat ou décision. |
| `validated_at` | datetime nullable | Horodatage du passage à `VALIDATED`. |
| `created_by`, `created_at`, `updated_at` | audit | Création et suivi de la définition. |

Une formule `VALIDATED` est immuable. Toute correction produit une
nouvelle version. La version utilisée par une future `Revision` devra
être référencée par UUID puis copiée dans son snapshot ; elle ne devra
jamais être relue seulement comme « dernière formule active ».

Les chemins ORM bulk qui contournent `save()` et `full_clean()` sont refusés
pour les modèles de formule et de terme. La garantie est applicative et
ORM contrôlée ; elle ne prétend pas intercepter du SQL direct.

La sélection de la version courante doit être explicite. L’invariant
immédiat est : au plus une version `VALIDATED` applicable à une date
donnée ; les conflits de périodes bloquent la validation. `valid_from` /
`valid_to` sont préparés comme métadonnées lorsque nécessaires, sans
construire prématurément un moteur temporel. La règle détaillée de
sélection automatique sera arrêtée avec le moteur de révision.

## 4. FormulaTerm

Champs proposés :

| Champ | Type proposé | Règle |
|---|---|---|
| `id` | UUID | Identité stable du terme. |
| `formula` | FK `MarketFormula` | Obligatoire. |
| `position` | entier positif | Unique dans la formule et stable pour l’affichage. |
| `coefficient` | NUMERIC(18,8)/Decimal | Aucun float ; précision de stockage acceptée, sans troncature prématurée. |
| `term_type` | chaîne contrôlée | LOT 2A autorise `INDEX_RATIO` ; extensions futures explicites. |
| `index_code` | chaîne | Code contractuel de l’index, par exemple `BAT3`. |
| `base_period_year` | entier nullable | Année de `I0` enregistrée explicitement. |
| `base_period_month` | entier nullable | Mois de `I0` si applicable. |
| `base_value` | NUMERIC(18,8)/Decimal nullable | Valeur de base connue, jamais inventée. |
| `base_source` | texte nullable | Provenance de la valeur de base. |
| `reference_note` | texte nullable | Référence contractuelle complémentaire. |

`index_code` est une référence contractuelle, pas une valeur d’indice
courante. Le futur référentiel `IndexDefinition`/`IndexValue` pourra
être relié ultérieurement sans rendre LOT 2A dépendant d’une implémentation
complète des indices.

## 5. Représentation mathématique

La forme minimale supportée est :

```text
K = C + Σ(ai × Ii / I0i)
```

Exemples conceptuels :

```text
K = 0,15 + 0,85 × BAT3 / BAT3₀

K = C
  + a × I1 / I10
  + b × I2 / I20
  + c × I3 / I30
```

La définition ne doit jamais être stockée uniquement dans
`expression_display`. Chaque terme, coefficient, code d’index et valeur
de base doit être persisté séparément.

LOT 2A ne définit pas le traitement réglementaire d’une composante autre
que `INDEX_RATIO`. Les extensions salaire, charges ou autres familles
contractuelles devront recevoir un type et une règle validés avant leur
implémentation.

## 6. Cohérence des coefficients

Pour la formule canonique couverte par REG-002, une formule `VALIDATED`
doit satisfaire :

```text
C + Σ(ai) = 1
```

et la contrainte réglementaire vérifiée `C >= 0,15` lorsqu’elle
s’applique au contrat concerné. Une formule DRAFT peut être incomplète,
mais elle ne peut pas être utilisée pour un calcul.

La validation utilise exclusivement Decimal. La précision de stockage
`NUMERIC(18,8)` ne force ni quantification ni troncature avant les étapes
contractuelles de calcul. Une tolérance Decimal ne pourra être introduite
que si elle est nécessaire et explicitement documentée ; elle ne doit
jamais provenir du comportement float. La règle `C + Σ(ai) = 1` ne
s’applique que lorsque la structure contractuelle/réglementaire concernée
l’impose.

Messages fonctionnels proposés : `FORMULA_INCOMPLETE`,
`FORMULA_COEFFICIENT_SUM_INVALID`, `FORMULA_CONSTANT_BELOW_MINIMUM`,
`FORMULA_TERM_DUPLICATE_POSITION` et `FORMULA_TERM_INVALID`.

La validation bloque le passage à `VALIDATED`, jamais la simple sauvegarde
DRAFT, sauf violation structurelle impossible à stocker.

### 6.1 Formule simple mono-index — constante et partie variable

Pour une structure contractuelle explicitement simple de la forme :

```text
K = C + A × INDEX / INDEX0
```

la règle métier approuvée est `C + A = 1`. Si `C` est fourni, `A` est
calculé déterministiquement comme `1 - C` ; l'utilisateur ne doit pas saisir
deux valeurs redondantes. Par exemple `C = 0,15` donne `A = 0,85`, et
`C = 0,10` donne `A = 0,90`.

Cette détermination utilise `Decimal` et conserve la précision contractuelle
jusqu'à la politique d'arrondi validée. L'interface future affichera la
partie fixe, l'indice choisi et la partie variable calculée, sans exposer
inutilement `RevisionGroup` ou `FormulaTerm`.

Cette règle ne se généralise pas aux formules multi-indices. Pour
`K = C + a × I1/I10 + b × I2/I20 + …`, la structure et les coefficients
doivent être vérifiés par rapport au contrat/CPS ; aucune complémentarité
automatique entre les termes ne doit être appliquée.

## 7. Définition, indices et calcul

LOT 2A sépare quatre niveaux :

1. définition contractuelle (`MarketFormula`, `FormulaTerm`) ;
2. valeurs d’indices et leur statut (`IndexValue`, lot ultérieur) ;
3. évaluation d’un coefficient `K` pour une période ;
4. utilisation de `K` dans une révision et ses montants.

Le lot 2A définit les fondations des niveaux 1 et 3, sans implémenter le
moteur complet de révision, la ventilation, les décomptes ou les
snapshots.

Une valeur d’index absente rend l’évaluation `PENDING_INDEX` et non
calculable. Il est interdit de mettre zéro, de reprendre le mois
précédent, d’extrapoler ou d’utiliser silencieusement une valeur
provisoire.

La date de référence et `I0` sont enregistrés explicitement avec leur
provenance. Aucune règle universelle ne doit être hardcodée dans LOT 2A.
La distinction appel à concurrence / procédure négociée de REG-003 reste
une dépendance du modèle `Market` ou du moteur réglementaire, à décider
avant toute automatisation.

## 8. Arrondis

REG-007 vérifie l’arrêt à la quatrième décimale, mais `PV-REG-001` ne
permet pas encore de déterminer le mode informatique exact. LOT 2A ne
choisit donc ni `ROUND_HALF_UP`, ni `ROUND_HALF_EVEN`, ni une autre règle.

La conception sépare la précision de stockage Decimal, la précision de
calcul intermédiaire, l’arrondi des rapports intermédiaires, l’arrondi du
coefficient final `K` et l’arrondi des montants financiers.

Tant que le mode n’est pas validé, l’évaluateur doit conserver la valeur
Decimal non arrondie et exposer l’état `ROUNDING_POLICY_PENDING` lorsque
la sortie réglementaire arrondie est demandée.

## 9. Approvisionnement et mise en œuvre

Lorsque le CPS distingue approvisionnement, mise en œuvre ou une autre
famille de prestations, le futur BDP peut affecter ces articles à des
`RevisionGroup` distincts, chacun portant sa formule contractuelle.

LOT 2A ne déduit aucune règle depuis le nom de la prestation et ne crée
aucun traitement spécial. Les règles de date effective et de calcul
relèvent des lots BDP/révision et de REG-015.

## 10. États et immutabilité

Cycle proposé : `DRAFT → VALIDATED → INACTIVE`.

Une formule DRAFT est éditable par OWNER/ADMIN. Une formule VALIDATED
est immuable. Une formule INACTIVE reste lisible pour l’historique et ne
peut plus être choisie pour une nouvelle révision. Une formule utilisée ou
référencée ne doit jamais être supprimée physiquement.

Le futur snapshot doit copier au minimum : groupe, formule, version,
constante, termes, coefficients, codes d’indices, valeurs de base,
périodes, références et provenance. Il ne doit pas dépendre des FK
vivantes après validation.

## 11. Hors périmètre LOT 2A

- `PriceSchedule` et `PriceItem` complets ;
- import Excel/CSV ;
- `WorkSuspension` et calendrier ;
- `Statement` et `StatementItem` ;
- référentiel officiel des indices ;
- ventilation mensuelle ;
- calcul des montants révisés ;
- snapshots et immutabilité de `Revision` ;
- régularisations ;
- documents PDF/DOCX.

## 12. Décisions requises

La conception est approuvée pour la gestion, le versionnage, les
validations structurelles et les fondations d’évaluation de LOT 2A. Restent
à valider avant une sortie réglementaire définitive : le mode informatique
d’arrondi de `PV-REG-001` et, avec le futur moteur, la règle détaillée de
sélection temporelle selon la date. Ces points ne bloquent pas le stockage
ou l’UI des formules, mais bloquent tout coefficient réglementaire final
qui en dépend.
