STATUS: IMPLEMENTED — TESTED — VALIDATED — FROZEN v0.7.0
SOURCE: ADR-GOV-005, ADR-GOV-006, ADR-LOT2B-001..005, Blueprint §§2, 4, 15

# LOT 2B — Bordereau des prix et affectation aux formules

Cette spécification décrit l'implémentation validée du périmètre LOT 2B.
Cette livraison est gelée en v0.7.0 ; aucun déploiement
ni changement de données de production n'est inclus.

## 1. Périmètre et vocabulaire

Un marché peut ne pas avoir de bordereau détaillé, ou posséder un
`PriceSchedule` contenant ses `PriceItem`. Un article peut être affecté à
zéro ou une formule de révision. Il ne peut jamais être affecté à plusieurs
formules.

Dans l'interface, `RevisionGroup` est toujours présenté comme **Formule de
révision**. Le groupe reste l'intermédiaire technique stable entre l'article
et les versions de `MarketFormula`.

La désignation, l'unité ou toute autre information textuelle ne déduit
jamais le traitement de l'article. Aucun mot-clé (`location`, `fourniture`,
`main d'œuvre`, etc.) ne déclenche une classification automatique.

## 2. Modèle proposé

### PriceSchedule

```text
id UUID
market OneToOne Market
status ACTIVE | ARCHIVED
source_type MANUAL | CSV | XLSX | OTHER
source_name nullable
notes nullable
created_at / updated_at
```

L'existence d'un `PriceSchedule` actif représente la présence activée du
BDP. Il n'y a pas de faux bordereau ni de ligne automatique. Un marché peut
rester sans `PriceSchedule`. Le modèle approuvé retient au plus un
`PriceSchedule` canonique par `Market` (`OneToOne`). Un import futur est une
opération/version d'import de ce bordereau, pas un second bordereau actif.

### PriceItem

```text
id UUID
price_schedule FK PriceSchedule
lot FK MarketLot nullable
price_number VARCHAR — chaîne conservée telle que saisie
designation TEXT
unit VARCHAR
estimated_quantity NUMERIC/Decimal nullable
unit_price_ht NUMERIC/Decimal nullable
estimated_amount_ht NUMERIC/Decimal nullable
revision_group FK RevisionGroup nullable
classification_status PENDING_CLASSIFICATION | REVISABLE | NON_REVISABLE
active BOOLEAN
notes TEXT nullable
created_at / updated_at
```

`market` est la relation dérivée `price_item.price_schedule.market` et est
exposée en lecture seule dans l'API. Le marché ne doit pas être dupliqué sur
la ligne, afin d'éviter une seconde source de vérité. Le lot et le groupe
doivent appartenir au même marché que le `PriceSchedule`.

Les quantités et montants sont toujours `Decimal` côté Python et
`NUMERIC/DECIMAL` côté PostgreSQL. Aucune conversion en `float` n'est
autorisée. Les précisions exactes et la politique de réconciliation entre
quantité × PU et montant importé sont à fixer avant implémentation ; aucune
règle d'arrondi réglementaire ne doit être inventée ici.

`price_number` est une chaîne opaque : `00001`, `A-001` et `1.2.3` restent
exactement des chaînes. Il ne faut ni trim destructif, ni conversion en
entier, ni normalisation qui supprimerait des zéros significatifs.

## 3. Cardinalité et classification

La relation persistée est :

```text
PriceSchedule 1 ─── N PriceItem ─── 0..1 RevisionGroup
RevisionGroup 1 ─── N MarketFormula (versions)
```

Elle doit être une FK nullable `PriceItem.revision_group_id`, et jamais une
table de liaison ou un ManyToMany. Une absence de FK signifie qu'aucune
formule n'est affectée ; elle ne crée pas `K=1` et ne crée pas une formule
« Sans révision ».

La représentation retenue pour distinguer les deux cas sans formule
est `classification_status` :

| État | `revision_group` | Signification |
|---|---|---|
| `PENDING_CLASSIFICATION` | NULL | l'utilisateur n'a pas encore arrêté le traitement |
| `REVISABLE` | obligatoire avant calcul/validation | l'utilisateur a déclaré l'article révisable et l'a affecté à une formule |
| `NON_REVISABLE` | NULL | l'utilisateur a explicitement déclaré l'article hors révision |

Un état `PENDING_CLASSIFICATION` peut être autorisé à la saisie, mais ne
peut recevoir aucune affectation définitive et ne peut pas être utilisé
silencieusement dans un calcul. Il bloque toute validation future exigeant
la classification complète. L'absence de formule reste légitime pour
`NON_REVISABLE` et n'est pas une erreur systématique.

## 4. Contraintes d'intégrité

Les contraintes prévues sont doubles :

- backend : validation du marché, du lot, du groupe, de l'état de
  classification et des permissions avant chaque mutation ;
- PostgreSQL : FK nullable vers `RevisionGroup`, contraintes d'unicité et
  contraintes de domaine lorsque PostgreSQL peut les exprimer correctement.

La cohérence inter-tables entre `revision_group.market_id`,
`lot.market_id` et `price_schedule.market_id` est obligatoirement contrôlée
par le service/backend avant toute mutation. Une contrainte PostgreSQL
supplémentaire (FK composite ou trigger) ne sera ajoutée que si son
implémentation est démontrée correcte et maintenable ; aucune contrainte
artificielle ou partielle ne doit donner une fausse garantie.

Les contraintes supplémentaires prévues sont :

- `UNIQUE(price_schedule, price_number)` ; comme `PriceSchedule` est
  `OneToOne` avec `Market`, cette contrainte réalise l'unicité du numéro dans
  le périmètre du marché, sans imposer une unicité globale ;
- quantité, PU et montant non négatifs lorsqu'ils sont présents ;
- `REVISABLE` exige un groupe ; `NON_REVISABLE` et `PENDING_CLASSIFICATION`
  n'en ont pas ;
- groupe et prix ne sont jamais supprimés physiquement lorsqu'ils sont
  utilisés ; désactivation logique et `PROTECT` sont préférés ;
- `MarketLot` reste indépendant des formules : aucun FK lot → formule.

## 5. Matrice d'affectation

L'écran du marché présente une matrice lisible :

```text
N° prix | Désignation        | Formule de révision 1 | Formule de révision 2 | ...
--------|--------------------|-----------------------|-----------------------|----
00001   | Câble HTA          |          ☑            |          ☐            |
00002   | Pose câble         |          ☐            |          ☑            |
00003   | Prix hors révision |          ☐            |          ☐            |
```

Visuellement, une ligne peut afficher des cases ; sémantiquement, la
sélection est exclusive comme un groupe de boutons radio. Cocher une autre
formule désaffecte l'ancienne. Le frontend met à jour l'état local, mais le
backend reste l'autorité et refuse tout état multiple.

Chaque colonne propose `Tout sélectionner` et `Tout désélectionner`.
L'opération reçoit un ensemble explicite d'articles ou un filtre serveur,
verrouille les lignes concernées dans une transaction, puis affecte toutes
les lignes au même `RevisionGroup` ou les désaffecte. Elle ne peut jamais
créer plusieurs relations. Tout désélectionner laisse la classification
dans l'état choisi par l'utilisateur et n'affecte aucune autre formule.

La matrice doit supporter plusieurs centaines de lignes : recherche par
numéro et désignation, filtre par lot, formule, sans formule et, si retenu,
`PENDING_CLASSIFICATION`, pagination ou virtualisation et sélection
multiple. L'en-tête affiche les compteurs par formule, hors révision et à
classer.

Les libellés « Ajouter un groupe » deviennent « Ajouter une formule de
révision » dans ce contexte. `RevisionGroup` reste réservé aux détails
techniques, API interne et traçabilité.

## 6. Politique des formules

L'affectation vise le `RevisionGroup`, pas une version individuelle de
`MarketFormula`. Le groupe est le rattachement contractuel stable ; la
version validée applicable est sélectionnée selon les règles futures de
calcul et copiée dans le snapshot de révision. Cela évite de réaffecter tous
les articles lors de chaque nouvelle version de formule.

Une formule possédant des articles ne doit pas être supprimée. Une formule
validée reste immuable ; une évolution crée une nouvelle version dans le
même groupe. La désactivation d'un groupe ou d'une formule doit bloquer une
nouvelle affectation et afficher un avertissement, sans casser les données
historiques. La politique exacte de réaffectation d'un groupe devenu
INACTIVE est une décision humaine préalable à l'implémentation.

## 7. Import futur

L'espace prévu est `imports/price_schedule/`, séparé de
`imports/statements/`. L'import n'est pas implémenté dans cette phase.

Pipeline proposé : upload → détection CSV/XLSX → mapping configurable des
colonnes → aperçu → validation des types et contraintes → détection des
doublons → import transactionnel → affectation séparée aux formules.

Colonnes candidates : `N° Prix`, `Désignation`, `Unité`, `Quantité`, `PU HT`,
`Montant HT`, avec mapping indépendant du nom de fichier ou du moteur Excel.
Les doublons de numéro dans le même marché/bordereau sont rejetés dans l'aperçu
avec lignes en erreur ; aucun suffixe, écrasement ou choix arbitraire n'est
automatique. Comme un marché ne possède qu'un bordereau canonique, cette
unicité couvre le marché ; `MarketLot` ne crée pas un nouvel espace de
numérotation.

Si le fichier fournit un montant HT, le système pourra comparer
`quantité × PU HT` à ce montant. Un écart est signalé dans l'aperçu et doit
être résolu ou validé par l'utilisateur selon une politique d'import future.
Le montant n'est jamais corrigé silencieusement et aucun seuil de tolérance
ou mode d'arrondi n'est inventé dans LOT 2B.

## 8. Historique futur

LOT 2B ne crée pas `Statement` ni `StatementItem`. Il doit toutefois
préserver leur future compatibilité : un futur `StatementItem` référencera
un `PriceItem` et copiera au moment de la validation le numéro, la
désignation, le lot, les montants, le statut de classification, le groupe,
la formule/version et les termes applicables. Une révision validée ne devra
plus lire ces valeurs vivantes.

La modification d'une affectation est autorisée avant toute utilisation
dans un élément historique validé, selon OWNER/ADMIN. Après utilisation
validée, la donnée vivante peut être corrigée pour les périodes futures,
mais les snapshots restent inchangés ; le détail de cette frontière sera
arrêté avec LOT 3/5.

## 9. Permissions et validation

OWNER/ADMIN actifs du marché peuvent créer, modifier, importer et affecter
les articles selon les règles existantes. MEMBER peut consulter le BDP, la
matrice et les compteurs, mais ne peut pas muter. L'API doit vérifier
l'appartenance active avant de charger les IDs fournis ; un ID d'un autre
marché ne doit jamais être accepté.

## 10. Questions résolues par cette conception

| Question | Réponse proposée |
|---|---|
| A. Cardinalité | FK nullable `PriceItem.revision_group_id`, donc 0..1 ; jamais M2M. |
| B. RevisionGroup | Oui, il reste l'intermédiaire technique stable vers les versions de formule. |
| C. Sans formule | `NULL` + statut explicite : `NON_REVISABLE` ou `PENDING_CLASSIFICATION`. |
| D. Tout sélectionner | Mutation bulk transactionnelle vers un seul groupe, désaffectation explicite, sans table de liaison. |
| E. Formule utilisée | Pas de suppression physique ; groupe/formule désactivé, nouvelle version pour évoluer. |
| F. Snapshots | LOT 2B conserve des références stables et réserve la copie complète à `StatementItem`/révision validée. |
| G. Doublons import | Rejet dans l'aperçu et correction utilisateur ; pas d'écrasement ni de suffixe automatique. |
| H. Unicité | `price_number` unique dans le marché via le `PriceSchedule OneToOne`; `MarketLot` n'est pas un espace de numérotation. |

## 11. Hors périmètre

L'import Excel/CSV complet, `Statement`/`StatementItem`, le calcul de
révision, les valeurs d'indices, les snapshots et toute formule officielle
fictive restent hors périmètre. La migration `0006` fait partie du candidat
mais n'est pas appliquée en production. La règle `C + A = 1` des formules
simples est documentée dans
`specs/03-formules.md`; elle ne s'étend pas automatiquement aux formules
multi-indices.
