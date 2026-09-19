# BLUEPRINT GLOBAL - REVISION DES PRIX WEB

**Document maître de développement**\
**Version : 1.0**\
**Date : 16/09/2026**\
**Statut : Source de vérité du projet**

> **Directive à l'agent de développement**\
> Construire l'application conformément à ce Blueprint. Les esquisses UI
> validées constituent la référence visuelle. Le présent document
> constitue la référence fonctionnelle, métier, données, architecture,
> déploiement et tests. Ne pas inventer une règle métier manquante : la
> signaler comme décision à valider.

------------------------------------------------------------------------

## 1. Finalité du produit

Construire une application Web professionnelle permettant de gérer,
calculer, justifier, historiser et éditer les révisions de prix des
marchés publics, avec priorité au cadre marocain et aux barèmes/indices
officiels.

Le cycle métier cible est :

``` text
UTILISATEUR
    |
    v
SOCIETE
    |
    v
MARCHE
    |-- Formule contractuelle
    |-- Epoque de base
    |-- OS de commencement
    |-- Arrêts / reprises
    |-- Décomptes
    |
    `-- REVISIONS
          |-- Décompte(s) concerné(s)
          |-- Ventilation mensuelle
          |-- Jours proposés / retenus
          |-- Indices
          |-- Coefficients
          |-- Montants
          |-- Validation
          |-- Versions
          `-- Régularisations

REFERENTIEL TRANSVERSE
    |-- Indices
    |-- Valeurs mensuelles
    |-- Barèmes officiels
    `-- Bibliothèque de formules
```

L'application n'est pas une GED. Elle conserve principalement les
données structurées nécessaires aux calculs, à leur justification, à
leur reproduction et à leur historique. Les documents générés de
révision sont conservés comme sorties du système.

------------------------------------------------------------------------

## 2. Principes non négociables

1.  Aucun calcul financier critique dans React.
2.  Le backend est la source de vérité.
3.  Le moteur de calcul est indépendant du frontend.
4.  Utiliser `Decimal` côté Python et `NUMERIC/DECIMAL` côté PostgreSQL
    ; ne jamais utiliser `float` pour les calculs financiers.
5.  Aucun indice manquant ne peut être remplacé silencieusement par `0`,
    par une valeur inventée ou par la dernière valeur connue.
6.  Une révision validée est immuable.
7.  Une nouvelle publication d'indice ne modifie jamais silencieusement
    une ancienne révision.
8.  Toute révision validée conserve un snapshot complet des données
    ayant produit le résultat.
9.  BAT3 n'est qu'un indice parmi d'autres : aucun indice particulier ne
    doit être codé en dur.
10. Le système doit accepter les formules mono-index et multi-index.
11. Une révision peut concerner un ou plusieurs décomptes.
12. La bibliothèque de formules et la formule contractuelle d'un marché
    sont deux objets distincts.
13. Les contrôles métier doivent exister côté backend même s'ils sont
    également réalisés côté frontend.
14. Toutes les migrations de base de données sont versionnées.
15. Le déploiement doit être reproductible avec Docker.
16. Les images de production sont versionnées et immuables autant que
    possible.
17. La migration complète vers un nouveau serveur fait partie du
    produit.
18. Les règles réglementaires non encore validées ne doivent jamais être
    inventées par le développeur.
19. Les esquisses validées constituent la référence UI/UX.
20. Une fonctionnalité n'est terminée que lorsque modèle, API, UI,
    règles, tests, migrations et documentation sont cohérents.

------------------------------------------------------------------------

## 3. Stack cible

### Frontend

-   React
-   TypeScript
-   Vite
-   Tailwind CSS

### Backend

-   Python
-   Django LTS
-   API REST/JSON

### Moteur métier

-   Python pur autant que possible
-   `Decimal`
-   modules indépendants pour formules, calendrier, ventilation,
    indices, révision, régularisation et arrondis

### Données

-   PostgreSQL

### Infrastructure

-   Docker
-   Docker Compose
-   Nginx
-   Makefile professionnel
-   `MIGRATE.sh`
-   Registry OCI/Docker
-   Git et versionnement sémantique

Ne pas introduire Kubernetes, Kafka, microservices, Elasticsearch, Redis
ou Celery tant qu'un besoin réel ne le justifie pas.

------------------------------------------------------------------------

## 4. Architecture applicative

``` text
Navigateur
    |
    v
Nginx
    |
    +--> Frontend React/TypeScript
    |
    `--> Django API
             |
             v
        Service Layer
             |
             v
       revision_engine
             |
             v
        Django ORM
             |
             v
        PostgreSQL
```

Le frontend ne communique jamais directement avec PostgreSQL.

Le coeur mathématique doit être testable sans navigateur et, autant que
possible, sans dépendance Django.

Structure cible :

``` text
backend/
  revision_engine/
    formulas/
    parser/
    calendar/
    allocation/
    indices/
    revision/
    regulation/
    rounding/
    validation/
    exceptions/
```

------------------------------------------------------------------------

## 5. Navigation principale

``` text
TABLEAU DE BORD

SOCIETES

MARCHES
  `-- [Marché sélectionné]
       |-- Vue générale
       |-- Formule
       |-- OS / Calendrier
       |-- Décomptes
       |-- Révisions
       `-- Historique

INDICES
BAREMES OFFICIELS
FORMULES

ADMINISTRATION
```

Lorsqu'un utilisateur se trouve dans un marché, ne jamais lui demander
de sélectionner à nouveau ce marché dans ses sous-écrans.

------------------------------------------------------------------------

## 6. Utilisateurs et droits

### Découpage de gouvernance du LOT 1

Le LOT 1 demeure le lot parent historique de ce Blueprint. Pour son
exécution, il est précisé en deux sous-lots :

```text
LOT 1
 ├── LOT 1A — Authentification / Utilisateurs / Sociétés
 └── LOT 1B — Marchés / Lots / Structure contractuelle
```

Cette précision de gouvernance ne supprime pas le LOT 1 historique et
n'autorise encore aucun développement.

Prévoir l'authentification, la déconnexion, la récupération/changement
de mot de passe et la gestion des sessions.

Rôles préparatoires : - Administrateur - Gestionnaire - Calculateur -
Consultation

Les permissions réelles sont contrôlées côté backend. Masquer un bouton
React ne constitue jamais une autorisation.

Pour les marchés et leurs lots, le contrôle métier réutilise `Membership`
du LOT 1A : un `OWNER` ou `ADMIN` actif peut créer et modifier un marché
ou un lot ; un `MEMBER` actif dispose de la lecture ; sans `Membership`
actif, aucun accès métier n'est accordé. Le superuser Django conserve
l'exception administrative système existante. Aucun second RBAC n'est
introduit.

------------------------------------------------------------------------

## 7. Société

### Entité `Company`

``` text
id / UUID
raison_sociale *
forme_juridique
capital_social

ice
if_fiscal
rc
cnss

adresse_complete
ville
telephone
email
site_web

representant_nom
representant_prenom
representant_fonction

logo
notes

status
created_at
updated_at
archived_at
```

Actions : - Créer - Consulter - Modifier - Archiver

Une société possédant des marchés ne doit pas être supprimée
physiquement.

Relation :

``` text
Company 1 ---- N Market
```

------------------------------------------------------------------------

## 8. Marché

### Entité `Market`

``` text
id / UUID
company_id *

market_number *
contracting_authority *
subject *

amount_ht Decimal(18,2), nullable, >= 0
vat_rate Decimal, 0..100, pourcentage humain (20.00 = 20 %)
formula_structure: SINGLE | MULTIPLE

date_limite_remise_offres nullable
date_ouverture_plis nullable
date_signature nullable
date_os_commencement nullable

contract_duration_value nullable, entier strictement positif
contract_duration_unit nullable, DAYS | MONTHS

status: ACTIVE | ARCHIVED, défaut ACTIVE

created_at
updated_at
archived_at
```

`UniqueConstraint(company, market_number)` est la seule contrainte
d'unicité du numéro dans LOT 1B. L'unicité globale n'est pas retenue ;
elle pourra être réévaluée si un cas réel démontre qu'une même société
peut porter deux marchés ayant exactement le même numéro.

Les deux champs de délai sont cohérents : tous deux renseignés ou tous
deux absents. Une valeur `MONTHS` n'est jamais convertie en jours par une
multiplication arbitraire par 30.

Les suspensions et reprises ne sont pas un statut de `Market` : elles
sont enregistrées par des événements `WorkSuspension` distincts.

Dates affichées dans l'interface : `JJ/MM/AAAA`, avec sélecteur de
calendrier.

------------------------------------------------------------------------

## 8.1 Lots de marché

### Entité `MarketLot`

``` text
id / UUID
market_id *
lot_number / code *
title *
description nullable
amount_ht Decimal(18,2), nullable
display_order entier >= 0
active bool, défaut true
notes nullable
created_at
updated_at
```

`UniqueConstraint(market, lot_number)` est obligatoire. `MarketLot` est
indépendant de `MarketFormula` : aucune clé étrangère directe ne relie
les deux. Aucun lot fictif n'est créé automatiquement, aucun champ
persistant `has_lots` n'est ajouté et aucun contrôle automatique
`SUM(lots.amount_ht) = market.amount_ht` n'est imposé.

------------------------------------------------------------------------

## 9. Epoque de base

Les dates enregistrées dans `Market` sont des faits contractuels. Aucune
date ne doit être inventée pour satisfaire le modèle et aucune de ces
dates n'est automatiquement la date réglementaire de référence d'une
révision. Les règles de référence dépendant de la procédure seront
définies et validées dans `regulatory/` et le moteur de calcul.

Principe d'architecture : `FACTS` dans `Market`, `RULES` dans le moteur
réglementaire/calcul. L'absence de `date_limite_remise_offres` ou de
`date_ouverture_plis` est donc valide au niveau de la persistance.

------------------------------------------------------------------------

## 10. Formule contractuelle

LOT 1B conserve uniquement la structure contractuelle du marché via
`formula_structure` (`SINGLE` ou `MULTIPLE`). Ce champ ne crée ni ne
stocke de formule. La définition détaillée de `MarketFormula` et de ses
termes appartient au lot Formules.

Exemple d'affichage :

``` text
K = 0,15 + 0,85 x (BAT3 / BAT3_0)
```

Ne jamais stocker uniquement cette chaîne comme seule représentation
métier.

### `MarketFormula` (lot ultérieur)

``` text
id
market_id *
libelle
expression_affichage
constant_term
version
created_at
effective_from
```

### `MarketFormulaTerm` (lot ultérieur)

``` text
id
formula_id *
position
coefficient
term_type
index_id / index_code
base_year
base_month
base_value
```

Le modèle doit supporter :

``` text
K = a0
  + a1 x I1/I10
  + a2 x I2/I20
  + a3 x I3/I30
  + ...
```

Il doit être extensible aux termes salaires/charges sociales ou autres
termes réglementaires nécessaires.

Les coefficients doivent faire l'objet de contrôles de cohérence.

------------------------------------------------------------------------

## 11. Bibliothèque de formules

### `FormulaTemplate`

La bibliothèque sert uniquement à préremplir.

Workflow :

``` text
Bibliothèque
    |
    v
Sélection
    |
    v
COPIE
    |
    v
MarketFormula propre au marché
    |
    v
Modification éventuelle
```

Une modification future de `FormulaTemplate` ne doit jamais modifier les
marchés existants.

------------------------------------------------------------------------

## 12. OS et calendrier contractuel

L'OS de commencement est enregistré dans `Market`.

### `WorkSuspension`

``` text
id
market_id *
stop_date *
resume_date *
observation
created_at
updated_at
```

Interface : - Date d'arrêt obligatoire - Date de reprise obligatoire -
Observation facultative

Pièce jointe non obligatoire.

Contrôles backend : - `resume_date > stop_date` - absence de
chevauchement - chronologie cohérente

Le moteur calendrier doit pouvoir produire : - période contractuelle
initiale - périodes suspendues - jours/périodes actifs - échéance
contractuelle corrigée

------------------------------------------------------------------------

## 13. Décompte

### `Statement`

``` text
id
market_id *

numero *
statement_date *

period_start *
period_end *

cumulative_ht
period_ht
revision_eligible_ht

is_final

observation

created_at
updated_at
```

Interface adoptée : - N° décompte - Date du décompte - Période Du / Au -
Montant HT avant retenue de garantie - Case "Dernier décompte" -
Observations facultatives

Le modèle doit distinguer le montant cumulatif, le montant propre à la
période et le montant réellement admissible à la révision.

------------------------------------------------------------------------

## 14. Décomptes cumulatifs et delta

Cas de référence :

``` text
DP1 cumul = 437 000
=> montant période = 437 000

DP2 cumul = 782 890
=> montant période = 782 890 - 437 000 = 345 890

DP3 cumul = 1 017 890
=> montant période = 1 017 890 - 782 890 = 235 000
```

Conserver le cumul et le delta calculé pour audit.

Le moteur doit empêcher tout double comptage.

------------------------------------------------------------------------

## 15. Décompte et révision sont indépendants

Créer un décompte ne crée jamais automatiquement une révision.

Une révision peut utiliser un ou plusieurs décomptes admissibles.

### Table associative `RevisionStatement`

``` text
revision_id *
statement_id *
eligible_amount
```

Relation :

``` text
Statement N ---- N Revision
```

Un décompte déjà totalement pris en compte doit générer un
avertissement/blocage adapté pour éviter le double comptage. Une
régularisation doit passer par le mécanisme de version/régularisation,
pas par une duplication silencieuse.

------------------------------------------------------------------------

## 16. Révision

### `Revision`

``` text
id
market_id *

revision_number
version
status

calculation_date

total_base_ht
total_revision_amount

is_regulation
parent_revision_id

notes

created_by
created_at
validated_by
validated_at
```

Statuts minimum : - DRAFT - CALCULATED - VALIDATED - SUPERSEDED si
nécessaire pour la présentation d'une chaîne de versions, sans effacer
l'historique

Une révision `VALIDATED` est immuable.

------------------------------------------------------------------------

## 17. Workflow de création d'une révision

``` text
Marché
  |
  v
Nouvelle révision
  |
  v
Sélection d'un ou plusieurs décomptes
  |
  v
Détermination du montant admissible
  |
  v
Ventilation par mois
  |
  v
Jours proposés automatiquement
  |
  v
Utilisateur valide/modifie les jours retenus
  |
  v
Chargement des indices
  |
  v
Calcul des coefficients
  |
  v
Calcul des montants de révision
  |
  v
Contrôles
  |
  v
Validation
  |
  v
Snapshot immuable + documents
```

------------------------------------------------------------------------

## 18. Ventilation mensuelle

Si une période couvre plusieurs mois, créer automatiquement une ligne
par mois.

Exemple :

``` text
20/04/2026 -> 15/06/2026

Avril 2026
Mai 2026
Juin 2026
```

### `RevisionMonth`

``` text
id
revision_id *

year *
month *

period_start
period_end

proposed_days
retained_days

allocation_ratio
allocated_ht

coefficient_k
revision_amount
```

L'utilisateur peut modifier `retained_days`.

Toujours conserver simultanément : - `proposed_days` - `retained_days`

Le total des jours retenus est recalculé automatiquement.

------------------------------------------------------------------------

## 19. Allocation financière

Principe :

``` text
allocation_ratio_m =
retained_days_m / total_retained_days
```

Puis :

``` text
allocated_ht_m =
eligible_ht x allocation_ratio_m
```

Le total des montants mensuels doit être réconcilié exactement avec le
montant à réviser conformément à la règle d'arrondi centralisée.

------------------------------------------------------------------------

## 20. Calcul de révision

Pour chaque mois :

``` text
K_m = P/P0
```

obtenu à partir de la formule contractuelle complète.

Puis :

``` text
revision_m =
allocated_ht_m x (K_m - 1)
```

Pour une formule multi-index, `K_m` doit être calculé à partir de tous
les termes applicables.

Aucune logique spécifique BAT3 ne doit être intégrée au moteur général.

------------------------------------------------------------------------

## 21. Référentiel des indices

### `IndexDefinition`

``` text
id
code *
designation
famille
domaine
unite
active
```

### `IndexValue`

``` text
id
index_id *

year *
month *

value
status *

publication_date
official_scale_id
source_url

imported_at
validated_at
validated_by
```

Statuts : - NOT_PUBLISHED - PROVISIONAL - FINAL

`NOT_PUBLISHED` n'est jamais représenté par une valeur numérique `0`.

------------------------------------------------------------------------

## 22. Historisation des indices

Une valeur provisoire utilisée dans une ancienne révision doit rester
traçable même lorsqu'une valeur définitive est publiée.

Ne jamais écraser silencieusement l'historique.

Le modèle de données doit permettre de savoir : - quelle valeur
existait, - son statut, - sa source, - quand elle a été
importée/validée, - quelles révisions l'ont utilisée.

------------------------------------------------------------------------

## 23. Indices utilisés dans une révision

### `RevisionMonthIndex`

``` text
id
revision_month_id *
index_id *

index_code_snapshot

base_value
current_value
current_status

source_id
source_url_snapshot
```

Ne jamais ajouter des colonnes métier du type `revision_month.bat3`, car
le système doit rester générique.

------------------------------------------------------------------------

## 24. Barèmes officiels

### `OfficialScale`

``` text
id
year
month
publication_date
official_url

document_hash
detected_at
imported_at

status
validation_status
```

Un barème officiel peut produire plusieurs `IndexValue`.

Le hash doit permettre d'identifier précisément le document source.

------------------------------------------------------------------------

## 25. Import des barèmes et indices

Architecture cible :

``` text
Source officielle
    |
    v
Détection nouveau barème
    |
    v
Téléchargement
    |
    v
Calcul du hash
    |
    v
Extraction
    |
    v
Validation structurelle
    |
    v
Contrôle
    |
    v
Validation métier
    |
    v
Publication dans le référentiel local
    |
    v
Détection des révisions potentiellement concernées
```

Aucune extraction incertaine ne doit être publiée silencieusement comme
donnée officielle validée.

Le système doit fonctionner hors ligne avec le dernier référentiel local
validé.

Prévoir une solution d'import manuel d'un PDF/URL officiel en secours.

------------------------------------------------------------------------

## 26. Indice non publié

Ne jamais inventer une valeur.

Affichage attendu :

``` text
Indice juillet 2026 : NON PUBLIE
```

Le traitement réglementaire applicable est isolé dans regulatory/.
Les règles REG-001 à REG-016 sont vérifiées ; tout comportement non
couvert reste PENDING_VALIDATION.

------------------------------------------------------------------------

## 27. Passage provisoire -\> définitif

Lorsqu'une valeur provisoire devient définitive :

``` text
Nouvel indice définitif
    |
    v
Recherche des révisions validées concernées
    |
    v
Alerte : REGULARISATION DISPONIBLE
```

Ne jamais modifier la révision historique.

L'utilisateur crée une nouvelle version/régularisation liée à la
précédente.

------------------------------------------------------------------------

## 28. Régularisation

Exemple :

``` text
Revision V1
Indice provisoire
    |
    v
Publication définitive
    |
    v
Revision V2 / Régularisation
```

V2 référence V1 via `parent_revision_id`.

L'interface doit permettre de comparer : - valeur(s) V1 - valeur(s) V2 -
écart de coefficient - montant V1 - montant recalculé - montant de
régularisation

V1 reste consultable et inchangée.

------------------------------------------------------------------------

## 29. Snapshot obligatoire

A la validation d'une révision, créer un snapshot complet et immuable
contenant au minimum :

``` text
société
marché
maître d'ouvrage
objet

formule
version de formule
coefficients

époque de base
indices de base

OS de commencement
arrêts/reprises

décomptes concernés
montants cumulés
montants de période
montants admissibles

ventilation mensuelle
jours proposés
jours retenus

indices mensuels
statuts des indices
sources officielles

coefficients calculés
règles d'arrondi
montants mensuels
révisions mensuelles
total
```

Une révision validée en 2026 doit pouvoir être reproduite exactement
plusieurs années plus tard, indépendamment de l'état courant du
référentiel.

------------------------------------------------------------------------

## 30. Audit

### `AuditEvent`

``` text
id
user_id

entity_type
entity_id

action

before_data
after_data

created_at
```

Tracer notamment : - création/modification société -
création/modification marché - changement de formule -
création/modification arrêt/reprise - création/modification décompte -
modification des jours retenus - calcul de révision - validation de
révision - import/validation d'indice - création de régularisation -
génération de document

------------------------------------------------------------------------

## 31. Documents générés

### `GeneratedDocument`

``` text
id
revision_id
document_type
format
revision_version
file_path
checksum
generated_at
generated_by
```

Formats minimum : - PDF - DOCX

PDF et DOCX doivent utiliser exactement la même source de
données/calcul.

Contenu minimum du rapport : - Société - Marché - Maître d'ouvrage -
Objet - Décompte(s) - Formule - Epoque de base - Tableau mensuel -
Indices - Coefficients - Montants - Révisions mensuelles - Total -
Observations

------------------------------------------------------------------------

## 32. Tableau de bord

Prévoir au minimum : - Marchés actifs - Décomptes non révisés -
Révisions en préparation - Révisions validées - Indices provisoires
utilisés - Indices non publiés/manquants - Régularisations disponibles -
Nouveaux barèmes détectés/importés

Chaque indicateur doit permettre d'accéder aux éléments concernés.

------------------------------------------------------------------------

## 33. Recherche

Recherche globale au minimum par : - N° marché - Société - Maître
d'ouvrage - Objet - N° décompte

------------------------------------------------------------------------

## 34. Modèle relationnel condensé

``` text
USER
 |
 +---------------- COMPANY
 |                    |
 |                    `------ MARKET
 |                              |
 |                              +-- MARKET_LOT
 |                              |
 |                              +-- MARKET_FORMULA
 |                              |      |
 |                              |      `-- FORMULA_TERM
 |                              |
 |                              +-- WORK_SUSPENSION
 |                              |
 |                              +-- STATEMENT
 |                              |       \
 |                              |        \ REVISION_STATEMENT
 |                              |        /
 |                              |       /
 |                              `-- REVISION
 |                                   |
 |                                   +-- REVISION_MONTH
 |                                   |       |
 |                                   |       `-- REVISION_MONTH_INDEX
 |                                   |
 |                                   +-- SNAPSHOT
 |                                   +-- GENERATED_DOCUMENT
 |                                   `-- CHILD REVISION / REGULATION
 |
 `---------------- AUDIT_EVENT


FORMULA_TEMPLATE


INDEX_DEFINITION
       |
       `-- INDEX_VALUE
              |
              `-- OFFICIAL_SCALE
```

------------------------------------------------------------------------

## 35. API métier conceptuelle

``` text
/api/auth/
/api/users/

/api/companies/

/api/markets/
/api/markets/{id}/formula/
/api/markets/{id}/calendar/
/api/markets/{id}/statements/
/api/markets/{id}/revisions/

/api/formula-templates/

/api/indices/
/api/index-values/
/api/official-scales/

/api/revisions/{id}/calculate/
/api/revisions/{id}/validate/
/api/revisions/{id}/regulate/

/api/revisions/{id}/pdf/
/api/revisions/{id}/docx/
```

Les URI exactes peuvent évoluer, mais la séparation métier doit être
conservée.

------------------------------------------------------------------------

## 36. UI/UX

Les esquisses validées sont la référence.

Principes : - fond clair - cartes blanches - bleu professionnel -
typographie lisible - formulaires larges - espacement maîtrisé -
tableaux compacts - navigation claire - responsive - priorité
desktop/tablette pour les écrans de calcul - dates avec date picker -
aucun ID technique demandé à l'utilisateur

Ne pas reproduire l'ancienne interface Tkinter.

Ne pas copier une application tierce ; les sites observés servent
uniquement de référence d'ergonomie/architecture.

------------------------------------------------------------------------

## 37. Docker

Docker dès le premier commit.

Architecture :

``` text
Docker Compose
  |-- nginx
  |-- frontend
  |-- backend
  `-- postgres
```

Fichiers :

``` text
compose.yaml
compose.dev.yaml
compose.prod.yaml
```

En production, ne pas monter le code source comme volume modifiable.

Les données PostgreSQL utilisent un volume persistant, mais un volume
n'est pas considéré comme une sauvegarde.

------------------------------------------------------------------------

## 38. Reproductibilité des dépendances

Obligatoire : - version Python figée - version Node figée - version
PostgreSQL figée - version Nginx figée - dépendances Python
verrouillées - dépendances npm verrouillées - aucun `latest` pour une
release de production - version applicative explicite - manifest de
release - digest des images lorsque pertinent

Versionnement sémantique :

``` text
1.0.0
1.1.0
1.2.0
...
```

------------------------------------------------------------------------

## 39. Makefile professionnel

Le Makefile est l'interface standard du développeur et de l'opérateur.

Commandes cibles :

``` text
make help

make install
make dev
make up
make down
make restart

make build
make rebuild

make test
make lint
make check

make migrations
make migrate

make backup
make restore

make status
make logs
make doctor

make build-images
make push-images

make release VERSION=1.0.0

make deploy VERSION=1.0.0
make rollback VERSION=0.9.0
```

Le Makefile orchestre. Les opérations complexes sont placées dans des
scripts versionnés.

------------------------------------------------------------------------

## 40. Build et Push des images

Workflow de release :

``` text
CODE
 |
 v
LINT / TEST
 |
 v
BUILD
 |
 v
TEST DES IMAGES
 |
 v
SECURITY CHECK
 |
 v
TAG VERSION
 |
 v
DIGEST
 |
 v
PUSH REGISTRY
 |
 v
RELEASE MANIFEST
```

La production récupère des images déjà construites et testées ; elle ne
reconstruit pas arbitrairement l'application à partir des dépendances du
moment.

------------------------------------------------------------------------

## 41. Manifest de release

Chaque release doit produire un manifeste contenant au minimum :

``` text
Application
Version applicative
Git commit
Date de build

Image frontend + digest
Image backend + digest
Image nginx/version
Version PostgreSQL

Version du schéma DB
Niveau des migrations
Version du bundle de migration
```

------------------------------------------------------------------------

## 42. MIGRATE.sh

Exigence obligatoire : un seul point d'entrée administrateur doit
permettre d'orchestrer une installation/migration complète vers un
nouveau serveur.

``` bash
sudo ./MIGRATE.sh
```

Fonctions attendues : - identifier OS/architecture - vérifier
CPU/RAM/espace disque - vérifier le réseau - installer/vérifier Docker -
installer/vérifier Docker Compose - préparer l'arborescence -
charger/vérifier la configuration - récupérer ou charger la release -
vérifier checksums/digests - préparer volumes - sauvegarder une DB
existante - restaurer PostgreSQL - exécuter migrations Django - démarrer
les services - attendre les healthchecks - exécuter des smoke tests -
produire un rapport de migration

Modes prévus :

``` text
./MIGRATE.sh --check
./MIGRATE.sh --install
./MIGRATE.sh --migrate
./MIGRATE.sh --verify
./MIGRATE.sh --restore <backup>
./MIGRATE.sh --rollback
```

Les secrets ne doivent jamais être embarqués en clair dans `MIGRATE.sh`.

------------------------------------------------------------------------

## 43. Bundle offline

Le projet doit pouvoir générer :

``` text
RevisionPrix-X.Y.Z-OFFLINE.tar.gz
```

contenant notamment : - `MIGRATE.sh` - fichiers Compose - manifest -
checksums - scripts internes - images Docker exportées - documentation
minimale - éléments nécessaires à l'installation de la release sans
reconstruire les dépendances applicatives

Objectif : une release historique doit rester installable même si
certains dépôts externes deviennent indisponibles.

------------------------------------------------------------------------

## 44. Sauvegardes

Sauvegarder au minimum : - PostgreSQL - configuration nécessaire -
documents générés - logos/fichiers nécessaires - manifest de release

Prévoir une politique de rotation quotidienne/hebdomadaire/mensuelle à
définir avant production.

Une sauvegarde doit être restaurable et testée.

------------------------------------------------------------------------

## 45. Migration PostgreSQL

Ne jamais copier aveuglément le répertoire interne d'un volume
PostgreSQL entre versions majeures.

Approche privilégiée :

``` text
Ancien PostgreSQL
    |
    v
pg_dump
    |
    v
Backup vérifié
    |
    v
Nouvelle instance PostgreSQL
    |
    v
pg_restore
    |
    v
Contrôles
```

Les upgrades majeurs PostgreSQL font l'objet d'une procédure dédiée.

------------------------------------------------------------------------

## 46. Healthchecks

Services critiques :

``` text
Nginx       HEALTHY
Frontend    HEALTHY
Backend     HEALTHY
PostgreSQL  HEALTHY
```

Le backend doit fournir un endpoint de santé vérifiant au minimum : -
application - connexion DB - état des migrations

------------------------------------------------------------------------

## 47. `make doctor`

Commande obligatoire :

``` bash
make doctor
```

Exemple attendu :

``` text
RevisionPrix Diagnostic

Docker.............. OK
Compose............. OK
Frontend............ HEALTHY
Backend............. HEALTHY
PostgreSQL.......... HEALTHY
Migrations.......... CURRENT
Storage............. OK
Last Backup......... OK
App Version......... X.Y.Z
DB Schema........... X.Y

SYSTEM READY
```

------------------------------------------------------------------------

## 48. Déploiement sécurisé

Séquence :

``` text
PRECHECK
  |
  v
BACKUP
  |
  v
PULL/LOAD RELEASE
  |
  v
VERIFY DIGEST
  |
  v
DB MIGRATION
  |
  v
DEPLOY
  |
  v
HEALTHCHECK
  |
  v
SMOKE TEST
  |
  v
SUCCESS
```

Une migration DB irréversible doit être identifiée avant déploiement.

------------------------------------------------------------------------

## 49. Rollback

En cas d'échec :

``` text
FAIL
 |
 v
Arrêt nouvelle version
 |
 v
Analyse compatibilité DB
 |
 +--> retour images précédentes si compatible
 |
 `--> restauration backup si nécessaire
 |
 v
Healthcheck
```

Le rollback doit être testé avant V1.0 production.

------------------------------------------------------------------------

## 50. Sécurité

Minimum production : - HTTPS obligatoire - cookies sécurisés - CSRF -
CORS restrictif - validation backend - permissions backend -
protection/rate limiting de la connexion - secrets externes aux images -
aucun secret dans Git - logs sans mots de passe/tokens - sauvegardes
protégées - headers de sécurité - rotation des secrets selon procédure

------------------------------------------------------------------------

## 51. CI/CD

Pipeline cible :

``` text
Git push
  |
  v
Lint
  |
  v
Tests frontend
  |
  v
Tests backend
  |
  v
Tests moteur
  |
  v
Build Docker
  |
  v
Scan
  |
  v
Images versionnées
  |
  v
Registry
```

La production ne doit jamais compiler directement une branche de
développement non qualifiée.

------------------------------------------------------------------------

## 52. Tests métier obligatoires

### Marchés

``` text
M01 création marché
M02 formule mono-index
M03 formule multi-index
M04 modification formule avant calcul
M05 modification formule après révision validée
```

### OS / calendrier

``` text
O01 aucun arrêt
O02 un arrêt/reprise
O03 plusieurs périodes
O04 chevauchement refusé
O05 reprise antérieure/égale à arrêt refusée
```

### Décomptes

``` text
D01 premier décompte
D02 décompte cumulatif
D03 calcul du delta
D04 dernier décompte
D05 période sur un mois
D06 période sur plusieurs mois
D07 prévention du double comptage
```

### Révisions

``` text
R01 formule mono-index
R02 formule multi-index
R03 indice définitif
R04 indice provisoire
R05 indice non publié
R06 plusieurs décomptes
R07 modification des jours retenus
R08 ventilation multi-mois
R09 validation
R10 modification après validation refusée
R11 réconciliation exacte des montants ventilés
```

### Régularisations

``` text
G01 provisoire -> définitif
G02 plusieurs indices concernés
G03 plusieurs mois concernés
G04 conservation V1
G05 calcul de l'écart V2/V1
```

### Infrastructure

``` text
I01 installation serveur vierge
I02 backup
I03 restore
I04 migration DB
I05 mise à jour application
I06 rollback
I07 migration vers serveur B vierge
I08 installation via bundle offline
I09 make doctor
```

------------------------------------------------------------------------

## 53. Tests de non-régression

Créer :

``` text
tests/fixtures/reference_cases/
```

Chaque cas de référence contient : - inputs - formule - calendrier -
décomptes - indices - résultats attendus - règles d'arrondi - snapshots
attendus si nécessaire

Une modification du code ne doit jamais modifier silencieusement un
résultat financier de référence.

Tolérance sur les résultats financiers lors des tests de
migration/reproduction : **0**.

------------------------------------------------------------------------

## 54. Points réglementaires à isoler

Créer une couche dédiée :

``` text
regulatory_rules/
```

Ne pas figer arbitrairement les points qui nécessitent encore validation,
notamment : le mode informatique exact d'arrondi, les effets détaillés
des arrêts/reprises, l'imputabilité du retard, les exclusions de
catégories, « location = non révisable », les cas d'index provisoire hors
article 12 et toute autre exception non explicitement sourcée.

Marquer ces comportements :

``` text
PENDING_REGULATORY_VALIDATION
```

L'agent doit demander une décision avant implémentation définitive.

------------------------------------------------------------------------

## 55. Avertissements de dépassement

Le système ne doit pas bloquer automatiquement un taux d'exécution
supérieur à 100 % uniquement sur ce critère.

Prévoir : - avertissement au-dessus de 100 % - avertissement renforcé
autour/au-delà de 110 % - indication qu'une vérification
réglementaire/contractuelle peut être nécessaire

Ne pas calculer de pénalités de retard dans le moteur de révision des
prix sauf extension explicitement décidée ultérieurement.

------------------------------------------------------------------------

## 56. Arborescence cible

``` text
revision-prix/
|
|-- BLUEPRINT.md
|-- DECISIONS.md
|-- VERSION
|-- Makefile
|-- MIGRATE.sh
|
|-- compose.yaml
|-- compose.dev.yaml
|-- compose.prod.yaml
|-- .env.example
|
|-- frontend/
|   |-- Dockerfile
|   |-- package.json
|   |-- lockfile
|   `-- src/
|
|-- backend/
|   |-- Dockerfile
|   |-- config/
|   |-- accounts/
|   |-- companies/
|   |-- markets/
|   |-- work_orders/
|   |-- statements/
|   |-- revisions/
|   |-- indices/
|   |-- regulatory_rules/
|   `-- revision_engine/
|
|-- nginx/
|
|-- scripts/
|   |-- install.sh
|   |-- build.sh
|   |-- deploy.sh
|   |-- backup.sh
|   |-- restore.sh
|   |-- migrate.sh
|   |-- healthcheck.sh
|   `-- rollback.sh
|
|-- tests/
|   `-- fixtures/
|       `-- reference_cases/
|
|-- docs/
|-- deployment/
`-- backups/
```

------------------------------------------------------------------------

## 57. Ordre de développement

### LOT 0 - Fondation

-   Repository
-   Docker
-   Compose
-   Makefile
-   `MIGRATE.sh` initial
-   PostgreSQL
-   Django
-   React
-   Tailwind
-   Nginx
-   CI
-   Healthchecks

### LOT 1 - Identité métier

-   Authentification
-   Utilisateurs
-   Sociétés
-   Marchés

### LOT 2 - Contrat

-   Formules
-   Bibliothèque de formules
-   Epoque de base
-   OS
-   Arrêts/reprises
-   Calendrier

### LOT 3 - Exécution

-   Décomptes
-   Cumul
-   Delta
-   Périodes

### LOT 4 - Moteur de révision

-   Ventilation
-   Jours
-   Indices
-   Formules
-   Coefficients
-   Calcul

### LOT 5 - Validation

-   Snapshots
-   Immutabilité
-   Historique
-   Audit

### LOT 6 - Régularisations

-   Provisoire/définitif
-   Détection
-   V2
-   Comparaison/différence

### LOT 7 - Documents

-   PDF
-   DOCX

### LOT 8 - Référentiel officiel

-   Indices complets
-   Barèmes
-   Sources
-   Import
-   Validation
-   Graphiques

### LOT 9 - Production

-   Backups
-   Restore
-   Registry
-   Build/Push
-   Release
-   `MIGRATE.sh` complet
-   Bundle offline
-   Rollback
-   Sécurité
-   Test réel de migration

------------------------------------------------------------------------

## 58. Livraison attendue à chaque lot

L'agent doit fournir systématiquement :

1.  Ce qui a été développé.
2.  Modèle de données concerné.
3.  Migrations créées.
4.  API créées/modifiées.
5.  Interface créée/modifiée.
6.  Règles métier implémentées.
7.  Tests ajoutés.
8.  Résultats des tests.
9.  Risques, TODO et décisions en attente.
10. Instructions précises de test utilisateur.

Ne pas passer au lot suivant lorsqu'un défaut bloquant connu subsiste
dans le lot courant.

------------------------------------------------------------------------

## 59. Définition de "terminé"

Une fonctionnalité n'est terminée que lorsque :

``` text
[ ] modèle DB
[ ] migration DB
[ ] règles backend
[ ] API
[ ] UI conforme à l'esquisse
[ ] validations
[ ] permissions
[ ] audit si nécessaire
[ ] tests unitaires
[ ] tests métier
[ ] gestion des erreurs
[ ] documentation
[ ] Docker build
[ ] tests de non-régression
```

------------------------------------------------------------------------

## 60. Interdictions architecturales

``` text
INTERDIT :
- BAT3 codé en dur
- float pour les finances
- calcul métier uniquement dans React
- indice absent = zéro
- report silencieux de la dernière valeur connue
- écrasement d'un indice provisoire
- modification d'une révision validée
- recalcul silencieux de l'historique
- suppression de snapshots
- dépendance vivante marché -> template de formule
- supposer 1 décompte = 1 révision
- latest pour une release production
- secrets dans Git/Dockerfile/Makefile/MIGRATE.sh
- migration serveur manuelle non documentée
- modification directe de DB en production
- règle réglementaire inventée par le développeur
- dépendance de reproduction historique à l'état actuel du référentiel
```

------------------------------------------------------------------------

## 61. Critère final de qualification V1.0

Avant production, effectuer un test réel :

``` text
SERVEUR A
Application + données de qualification
        |
        v
Backup + Release
        |
        v
NOUVEAU SERVEUR B VIERGE
        |
        v
./MIGRATE.sh
        |
        v
Application HEALTHY
```

Comparer automatiquement A et B :

``` text
Sociétés             identiques
Marchés              identiques
Formules             identiques
OS/calendriers       identiques
Décomptes            identiques
Indices              identiques
Révisions            identiques
Snapshots            identiques
Documents            présents/cohérents
Résultats financiers identiques
```

**Tolérance sur les résultats financiers : 0.**

------------------------------------------------------------------------

## 62. Directive finale à l'agent

> Ce fichier `BLUEPRINT.md` est la source de vérité du projet Révision
> des Prix Web. Commencer par le LOT 0. Ne pas simplifier le modèle
> métier pour accélérer la réalisation des écrans. Les esquisses
> validées sont la référence UI. Le moteur de calcul doit rester
> indépendant, déterministe et entièrement testable. Toute ambiguïté
> réglementaire ou métier doit être signalée avant implémentation.
> Chaque lot doit être livré avec migrations, tests et procédure de
> validation. Docker, le Makefile, les images versionnées, les
> sauvegardes, le rollback et `MIGRATE.sh` font partie intégrante du
> produit.

------------------------------------------------------------------------

## 63. Gouvernance du Blueprint

-   Toute modification structurante du présent fichier doit être
    versionnée.
-   Les décisions prises après le Blueprint sont consignées dans
    `DECISIONS.md`.
-   Une décision validée qui modifie une règle de référence doit ensuite
    être répercutée dans `BLUEPRINT.md`.
-   Le code ne doit pas devenir la seule documentation d'une règle
    métier.
-   En cas de contradiction entre une ancienne note de développement et
    ce Blueprint, l'agent doit signaler la contradiction avant de
    poursuivre.
-   Les règles juridiques officiellement vérifiées doivent mentionner
    leur source dans la documentation réglementaire du projet.
