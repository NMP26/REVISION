STATUS: IMPLEMENTED — TESTED — VALIDATED — FROZEN v0.7.1
LOT: LOT 2B — Bordereau des prix et affectation aux formules
DEPENDENCY: LOT 2A v0.6.0; LOT 2A.1 v0.6.1; ADR-LOT2B-001..006 accepted
IMPLEMENTATION: IMPLEMENTED / TESTED / VALIDATED; NO DEPLOYMENT INCLUDED
PRODUCTION: v0.6.1 unchanged

# Plan d'implémentation LOT 2B

Ce document demeure le contrat de périmètre technique. L'implémentation
LOT 2B est gelée dans le candidat v0.7.1 : aucune donnée de production,
migration de production ou mise en production n'est incluse.

## 0 bis. État d'implémentation et validation

Les phases modèle, services/API, UX des formules et matrice BDP prévues
ci-dessous sont implémentées et validées. La migration `0006` est additive et
a été appliquée uniquement à des bases PostgreSQL de test éphémères, depuis
zéro et depuis le schéma `0005`. L'import Excel avancé reste hors périmètre ;
le parcours correctif v0.7.1 fournit la saisie manuelle et l'import CSV du BDP.

## 1. Constat de l'architecture existante

L'application est un monolithe Django/DRF dans `backend/markets`, avec une
interface React dans `frontend/src/markets`.

Les éléments LOT 2A/2A.1 à réutiliser sont :

- `Market`, `MarketLot`, `RevisionGroup`, `MarketFormula`,
  `FormulaTemplate` et `FormulaTerm` dans `backend/markets/models.py` ;
- `copy_formula_template` et les transactions existantes dans
  `backend/markets/services.py` ;
- `can_update_market` et les permissions société/marché existantes ;
- les serializers et vues de formules existants ;
- `RevisionFormulaSection.tsx` et `frontend/src/lib/api.ts` ;
- la suite `RevisionFormulaApiTests`, `FormulaTemplateTests` et les tests
  frontend de `MarketsPage`.

Le modèle interne reste :

```text
Market 1 ─── 0..1 PriceSchedule 1 ─── N PriceItem
MarketLot 1 ─── N PriceItem (optionnel)
PriceItem ─── 0..1 RevisionGroup ─── N MarketFormula
```

`RevisionGroup` est conservé comme rattachement technique stable. Une
formule affichée à l'utilisateur correspond au groupe et à sa formule
contractuelle active/versionnée ; l'interface ne demande pas de créer un
« groupe ».

Le nombre de `MarketFormula` ne détermine pas le mode d'application. Le
marché porte explicitement un `revision_application_mode` :

- `GLOBAL_FORMULA` : une formule couvre toutes les prestations concernées ;
  le BDP détaillé n'est pas requis pour poursuivre vers les décomptes et la
  révision ;
- `PRICE_ASSIGNMENT` : les traitements sont déterminés au niveau des prix ;
  le BDP est requis pour les affectations et les prix sans révision.

Une seule formule avec des prix `NON_REVISABLE` est donc en
`PRICE_ASSIGNMENT`, jamais en `GLOBAL_FORMULA`.

## 2. Séquencement proposé

### LOT 2B.0 — Préparation et contrat d'implémentation

Avant tout développement : confirmer la version de production v0.6.1,
relire les ADR acceptés, figer les contrats API et produire un plan de
migration. Cette phase ne change aucun fichier applicatif.

### LOT 2B.1 — Mode d'application, modèle PriceSchedule/PriceItem et migration additive

La migration additive `0006_priceitem_priceschedule_market_global_revision_group_and_more`
comprend :

- `Market.revision_application_mode`, avec les valeurs explicites
  `GLOBAL_FORMULA` et `PRICE_ASSIGNMENT` ;
- un rattachement global stable vers le `RevisionGroup` du même marché,
  lorsque `GLOBAL_FORMULA` est sélectionné ;

- `PriceSchedule`, lié en `OneToOne` à `Market`, avec statut/source,
  timestamps et version de concurrence ;
- `PriceItem`, lié à `PriceSchedule`, avec lot optionnel ;
- `price_number` en chaîne opaque ;
- désignation, unité, quantité estimée, PU HT, montant estimé HT, notes,
  `active` et `classification_status` ;
- FK nullable `revision_group` ;
- index de recherche et contrainte d'unicité du numéro dans le marché.

`GLOBAL_FORMULA` exige exactement une formule sélectionnée et n'exige pas de
`PriceSchedule`. `PRICE_ASSIGNMENT` exige un BDP avant calcul/validation.
Ces règles ne sont jamais déduites du nombre de formules.

La migration sera additive, sans seed, sans import, sans classement
automatique et sans backfill métier implicite. Aucun numéro, montant ou
formule ne sera créé pour les données existantes.

Précision technique proposée à vérifier dans la revue de migration :
quantité `NUMERIC(18,6)`, PU HT `NUMERIC(18,8)`, montant HT selon la
convention monétaire déjà utilisée (`NUMERIC(18,2)` si confirmée). Cette
précision de stockage ne définit aucune règle d'arrondi réglementaire.

### LOT 2B.2 — Services métier, API et permissions

Implémenter ensuite les services transactionnels et les endpoints CRUD,
lecture de matrice et affectation groupée. Toute mutation passera par un
service qui verrouille les articles concernés (`select_for_update`) et
valide le marché de chaque objet associé.

Les permissions réutilisent `can_update_market` : OWNER/ADMIN peuvent
écrire selon les règles existantes ; MEMBER reste en lecture seule ; toute
lecture est limitée au marché autorisé.

Le service de configuration accepte explicitement la question « La même
formule de révision s'applique-t-elle à l'ensemble des prix du marché ? ».
Il contrôle les transitions de mode et refuse toute incohérence entre mode,
formule globale et BDP existant.

### LOT 2B.3 — UX des formules et copie des templates

Adapter `RevisionFormulaSection` pour que le parcours normal soit :

1. `Ajouter une formule de révision` ;
2. recherche et choix d'un `FormulaTemplate` disponible ;
3. création atomique d'une `RevisionGroup` technique et copie indépendante
   en `MarketFormula` ;
4. affichage de la formule contractuelle du marché.

Le parcours demande d'abord le mode d'application :

- **GLOBAL_FORMULA** : une `MarketFormula` est sélectionnée, le BDP n'est
  pas requis pour la révision et le marché peut poursuivre vers
  OS/calendrier → décomptes → ventilation → révision ;
- **PRICE_ASSIGNMENT** : le parcours continue vers formules → BDP →
  matrice d'affectation → décomptes → ventilation → révision.

Le BDP peut exister en mode global pour d'autres usages, mais sa présence
ne devient pas une condition de calcul. En mode `PRICE_ASSIGNMENT`, il est
la source obligatoire pour identifier les prix révisables et sans révision.

Le nouvel endpoint d'orchestration pourra créer le groupe et copier le
template en une transaction. Les endpoints LOT 2A existants restent
compatibles pour les données déjà présentes, mais ne sont plus le parcours
UI principal.

Pour un template simple mono-indice, la réponse API expose une
présentation métier dérivée : indice implicite, partie fixe saisissable,
partie variable calculée avec Decimal et expression lisible. L'utilisateur
ne choisit donc pas deux fois BAT3 et ne manipule pas `FormulaTerm`, `C`,
`index_code` ou `base_value` dans le parcours normal.

Pour les templates complexes, aucun éditeur mathématique brut ne sera
exposé par défaut. Il faudra un contrat de présentation métier propre au
template ; à défaut, le template ne sera éditable par ce parcours.
Les exemples BAT1/BAT3/etc. ne seront pas créés ni qualifiés
OFFICIAL/VERIFIED sans source vérifiée.

### LOT 2B.4 — Import Excel/CSV

Créer séparément le namespace `imports/price_schedule/` avec :

L'import est disponible uniquement en mode `PRICE_ASSIGNMENT`. Il n'est pas
nécessaire et ne doit pas être imposé en mode `GLOBAL_FORMULA`.

- détection du format et lecture sans conversion en float ;
- mapping des colonnes ;
- normalisation contrôlée des chaînes et conservation des zéros et
  séparateurs du numéro ;
- aperçu avec erreurs par ligne ;
- détection des doublons dans le marché ;
- comparaison `quantité × PU HT` / montant importé ;
- validation explicite puis écriture transactionnelle.

Une session d'import persistée (`uploaded`, `mapped`, `previewed`,
`validated`, `imported`, `failed`) permettra de conserver le fichier,
checksum, mapping, lignes invalides, écarts et décision finale. Aucun
article importé ne sera automatiquement affecté à une formule : son statut
initial sera `PENDING_CLASSIFICATION`.

Un écart de montant sera présenté et devra être résolu/validé explicitement.
Aucun seuil, arrondi ou correction silencieuse ne sera inventé dans LOT 2B.

### LOT 2B.5 — Interface du BDP

Ajouter l'écran de consultation et d'édition du bordereau : pagination ou
virtualisation, recherche par numéro/désignation, filtre lot, statut,
formule et actif/inactif, compteurs par statut et par formule. La saisie
manuelle et l'assistant d'import utiliseront les mêmes validations API.

L'écran est conditionnel au mode `PRICE_ASSIGNMENT`. En mode global,
l'interface affiche que le BDP détaillé n'est pas requis pour la révision et
n'en crée pas silencieusement.

### LOT 2B.6 — Matrice d'affectation

Ajouter une matrice à colonnes de formules : une ligne par `PriceItem`, une
case par formule de révision du marché et aucune case pour un prix
`NON_REVISABLE`.

Les sélections individuelles, `Tout sélectionner` et `Tout désélectionner`
appellent le même endpoint bulk transactionnel. Une sélection remplace
l'affectation précédente ; elle ne crée jamais une relation multiple.

`REVISABLE` doit avoir exactement une formule avant calcul/validation.
`NON_REVISABLE` doit avoir une FK nulle. `PENDING_CLASSIFICATION` ne peut
avoir d'affectation définitive et ne peut entrer silencieusement dans un
calcul.

La matrice n'est pas un prérequis du mode `GLOBAL_FORMULA`, qui référence
directement la formule globale dans les futurs décomptes.

### LOT 2B.7 — Intégration, audit et gel v0.7.0

Exécuter les tests ciblés puis la suite LOT 2A/2A.1, les contrôles de
migration, le build frontend, `git diff --check` et `make doctor`. Vérifier
les parcours Consortium, Sociétés, Groupements, Marchés et les permissions
avant le gel. Le réaudit final est accepté et le candidat est gelé en
v0.7.0. La migration n'est pas appliquée en production et aucun déploiement
n'est compris dans ce gel.

## 3. Plan du modèle de données

### PriceSchedule

- `market`: OneToOne, marché propriétaire, sans bordereau global partagé ;
- statut, source, nom/notes, `created_at`, `updated_at` ;
- `change_version` entier monotone pour détecter une écriture concurrente ;
- absence de route de suppression physique dans l'API métier.

Le `PriceSchedule` est obligatoire seulement pour
`PRICE_ASSIGNMENT`. Il ne sera pas créé pour satisfaire artificiellement
le mode `GLOBAL_FORMULA`.

### Configuration d'application

Le choix métier est porté au niveau du marché, ou par une configuration 1:1
dédiée si la revue du modèle l'impose :

- `revision_application_mode = GLOBAL_FORMULA | PRICE_ASSIGNMENT` ;
- `global_revision_group`, nullable, autorisé seulement en
  `GLOBAL_FORMULA` et appartenant au même marché.

Le rattachement global vise le `RevisionGroup` stable ; la
`MarketFormula` contractuelle active est résolue selon les règles LOT 2A.
En `PRICE_ASSIGNMENT`, le rattachement global est nul et les
`PriceItem.revision_group` portent les affectations. Cette structure
empêche de confondre « une formule existe » avec « elle couvre tout le
marché ».

### PriceItem

- `price_schedule` obligatoire ; le marché est toujours dérivé du
  bordereau ;
- `lot` nullable, appartenant au même marché ;
- `price_number` chaîne opaque et unique dans le marché ;
- `designation`, `unit`, `estimated_quantity`, `unit_price_ht`,
  `estimated_amount_ht`, `notes`, `active` ;
- `classification_status` : `PENDING_CLASSIFICATION`, `REVISABLE`,
  `NON_REVISABLE` ;
- `revision_group` nullable, jamais ManyToMany ;
- timestamps et champs utiles à l'audit.

Le groupe est le rattachement stable à la formule du marché. Le changement
de version de `MarketFormula` ne doit pas réécrire l'historique futur.

### Historique futur

LOT 2B ne crée pas `Statement`/`StatementItem`. Le modèle réserve toutefois
la possibilité de snapshots portant au minimum : numéro, désignation,
quantité, PU, traitement de révision, `RevisionGroup`, formule/version et
valeurs utilisées au calcul. Après validation historique, les routes de
modification/suppression du BDP devront refuser ou archiver sans détruire
les données nécessaires.

## 4. Plan API

Endpoints à implémenter après approbation, sous le périmètre marché :

- `GET/PATCH /api/markets/{market_id}/revision-application/` ;
- `GET/POST /api/markets/{market_id}/price-schedule/` ;
- `GET/POST/PATCH /api/markets/{market_id}/price-schedule/items/` ;
- `GET /api/markets/{market_id}/price-schedule/matrix/` ;
- `POST /api/markets/{market_id}/price-schedule/assignments/` ;
- endpoint d'import réservé au namespace `price-schedule/imports/` ;
- endpoint d'orchestration `revision-formulas/from-template/` pour le
  parcours métier sans groupe technique.

L'API de configuration expose la question métier et son choix. Elle refuse
`GLOBAL_FORMULA` sans formule unique sélectionnée et refuse une transition
vers ce mode lorsqu'une affectation détaillée ou une exception
`NON_REVISABLE` rend la couverture globale fausse. Les endpoints BDP
retournent explicitement `required` ou `not_required` selon le mode.

Les futurs décomptes pourront référencer directement la formule globale en
mode `GLOBAL_FORMULA`. En mode `PRICE_ASSIGNMENT`, ils devront utiliser les
affectations par prix.

Le bulk accepte soit une liste d'IDs, soit un filtre validé côté serveur,
mais jamais une liste de groupes. Il reçoit l'action `assign` ou
`unassign`, le `revision_group_id` pour l'affectation et éventuellement
`expected_version`. La réponse renvoie les compteurs et le nouveau
`change_version`.

Les sérialisations utilisent des chaînes décimales JSON. Les erreurs
retournent explicitement : marché incompatible, lot incompatible, groupe
incompatible, statut incompatible, article introuvable, conflit de version
ou doublon.

## 5. Contraintes PostgreSQL et backend

### Contraintes PostgreSQL possibles

- unicité de `(price_schedule_id, price_number)` ;
- checks de non-négativité des valeurs numériques selon les champs
  autorisés ;
- check local de cohérence statut/FK lorsque PostgreSQL peut l'exprimer ;
- index sur bordereau, statut, groupe, lot et numéro.

### Contraintes obligatoirement backend/service

- `PriceItem.price_schedule.market_id == RevisionGroup.market_id` ;
- `GLOBAL_FORMULA` : une seule formule globale, sans exigence de BDP ;
- `PRICE_ASSIGNMENT` : BDP et affectations cohérentes exigés avant calcul ;
- lot et article appartenant au même marché ;
- groupe existant dans le marché cible ;
- `REVISABLE` exactement une affectation avant calcul/validation ;
- `NON_REVISABLE` sans affectation ;
- `PENDING_CLASSIFICATION` sans affectation définitive ;
- verrouillage et atomicité des opérations bulk ;
- refus de suppression/modification destructive après consommation
  historique.

Aucun trigger ou check PostgreSQL artificiel ne sera ajouté pour simuler
une règle inter-table que la base ne peut pas garantir correctement.

## 6. Plan des permissions

- lecture : utilisateur authentifié autorisé sur la société/marché ;
- écriture BDP, classement, affectation et import : `can_update_market` ;
- MEMBER : lecture seule, y compris matrice et compteurs ;
- contrôle systématique des IDs dans le marché avant toute écriture ;
- aucun endpoint global ne doit révéler les articles d'un autre marché ;
- les templates restent soumis aux règles globales/société existantes.
- le changement de mode suit les permissions du marché et doit être
  contrôlé lorsqu'il existe déjà des données BDP ou historiques.

## 7. Plan frontend

Réutiliser les conventions de `MarketsPage` et de `api.ts`. Évolutions
prévues :

- `RevisionFormulaSection` : recherche de templates, libellés métier,
  ajout naturel de N formules, complément `A = 1 - C` en Decimal ;
- `PriceScheduleSection` : état, compteurs, édition et import ;
- `PriceItemTable` : pagination, filtres et affichage sans float ;
- `PriceAssignmentMatrix` : cases exclusives, actions de colonne et
  retour d'erreur serveur ;
- tests de lecture seule et de permissions conservés et étendus.

Le composant de configuration affiche d'abord la question de couverture.
En `GLOBAL_FORMULA`, il présente la formule choisie et permet de continuer
sans écran BDP. En `PRICE_ASSIGNMENT`, il affiche les étapes formules → BDP
→ affectation et leur état de complétude.

La sélection optimiste ne sera jamais considérée comme suffisante : le
frontend reflète la réponse transactionnelle du backend.

## 8. Plan de tests

### Backend

- OneToOne marché/bordereau et réutilisation du même numéro dans deux
  marchés distincts ;
- formule globale sans BDP autorisée ;
- formule globale avec décompte adressable directement à cette formule ;
- plusieurs formules sans BDP refusées lorsque l'affectation est requise ;
- une formule avec prix `NON_REVISABLE` bascule en `PRICE_ASSIGNMENT` et
  exige le BDP ;
- un prix ne peut appartenir à deux formules ;
- partie fixe + coefficients indicés = 1 avec Decimal ;
- passage de `GLOBAL_FORMULA` vers `PRICE_ASSIGNMENT` sans perte
  silencieuse des données ;
- passage inverse contrôlé si des affectations BDP existent ;
- unicité d'un numéro dans un marché, y compris lots différents ;
- chaînes `00001`, `A-001`, `1.2.3` conservées ;
- Decimal et sérialisation sans float ;
- cohérence des trois traitements et absence d'affectation multiple ;
- refus des rattachements lot/groupe d'un autre marché ;
- bulk atomique, verrouillage, désélection et concurrence ;
- permissions OWNER/ADMIN/MEMBER et absence de fuite inter-marchés ;
- copie indépendante template → formule ;
- formule mono-indice implicite et calcul exact de `A = 1 - C` ;
- absence de classement par désignation ;
- import, doublons, écarts de montant et aucune correction silencieuse ;
- protection des objets consommés historiquement.

### Frontend

- libellé `Ajouter une formule de révision`, sans formulaire normal de
  groupe/FormulaTerm ;
- recherche de template et ajout de 0, 1 puis N formules ;
- BAT3-like : indice implicite, C éditable, A recalculé ;
- absence d'index officiel inventé dans la bibliothèque ;
- matrice exclusive, actions de colonne, filtres et pagination ;
- affichage PENDING/NON_REVISABLE sans affectation ;
- MEMBER sans contrôles de mutation ;
- erreurs de conflit et de validation affichées depuis le backend.

### Régression/intégration

- suite existante `RevisionFormulaApiTests` et `FormulaTemplateTests` ;
- routes Sociétés, Groupements, Marchés et Consortium ;
- immutabilité des formules validées et règles LOT 2A.1 ;
- migration `makemigrations --check`, `migrate --plan`, tests et build ;
- `make doctor` avant approbation de release.

## 9. Risques et mesures

| Risque | Mesure prévue |
|---|---|
| Les FKs ne garantissent pas le même marché | service transactionnel, verrouillage et tests inter-marchés |
| Concurrence sur une affectation bulk | `select_for_update` et `change_version` |
| Templates actuels trop techniques pour l'UX | projection de présentation, aucun éditeur brut par défaut |
| Précision/écart des montants importés | Decimal, aperçu, décision explicite, aucune tolérance inventée |
| Suppression d'un lot ou d'une formule utilisée | PROTECT/archivage et snapshots futurs |
| Régression de LOT 2A.1 | conserver endpoints et tests existants, migration additive |
| Noms BAT1/BAT3 sans source | aucun seed ni statut OFFICIAL/VERIFIED automatique |
| Plusieurs bordereaux d'un même marché | OneToOne décidé ; les sessions d'import sont des sessions, pas des BDP |
| Une formule unique confondue avec une couverture globale | enum explicite au niveau du marché et tests de transition |
| BDP créé inutilement en mode global | API et frontend conditionnels au mode |

## 10. Questions techniques ouvertes

Ces points sont à trancher dans la revue d'implémentation, sans nouvelle
décision métier :

1. confirmer les précisions `NUMERIC` exactes et leur validation avec les
   conventions financières existantes ;
2. confirmer la rétention des fichiers/sessions d'import et le stockage du
   fichier source ;
3. confirmer le format de présentation des templates multi-indices sans
   exposer les termes techniques ;
4. confirmer le nom final de l'endpoint d'orchestration de copie ;
5. confirmer si `change_version` suffit ou si une stratégie de verrouillage
   stricte est retenue seule ;
6. vérifier, par prototype, qu'une contrainte composite inter-table apporte
   une garantie réelle ; sinon rester sur le service backend documenté.
7. définir la politique technique de transition de mode après saisie ou
   consommation historique ; aucune suppression silencieuse n'est permise.

## 11. Décisions humaines et autorisation

Aucune décision métier supplémentaire n'est requise : classification,
cardinalité, unicité marché, UX template, Decimal, snapshots et permissions
sont déjà approuvés par les ADR LOT2B-001 à LOT2B-005.

Le réaudit final est accepté. Le gel v0.7.1 autorise le commit, le tag et le
push contrôlés ; il n'autorise ni migration production ni déploiement et ne
permet pas de commencer LOT 2C, les décomptes, les révisions ou le moteur
final de calcul.

## 12. État de contrôle de cette phase

- code backend LOT 2B : implémenté et validé ;
- code frontend LOT 2B : implémenté et validé ;
- migration 0006 : créée, testée hors production ;
- production modifiée : non ;
- commit/push/tag : autorisés par le gel v0.7.1 ;
- déploiement : non.

Après approbation, chaque sous-phase devra être livrée et contrôlée
séparément avant de passer à la suivante.
