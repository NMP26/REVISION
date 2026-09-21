# Décisions techniques — RevisionPrix

## Format ADR

Toute nouvelle décision doit utiliser les champs suivants :

```text
ADR-ID:
Date:
Sujet:
Contexte:
Décision:
Motif:
Impact:
Exigences liées:
Statut: PROPOSED | ACCEPTED | SUPERSEDED | REJECTED
```

Les décisions existantes ci-dessous sont conservées comme référence
historique du LOT 0.

## ADR-LOT0-001 — 2026-09-16 — LOT 0 / PHASE 1

ADR-ID: ADR-LOT0-001
Date: 2026-09-16
Sujet: Fondation technique RevisionPrix
Contexte: Mise en place du socle LOT 0.
Décision: Voir les décisions validées ci-dessous.
Motif: Établir la fondation technique et ses limites.
Impact: Cadre technique, sécurité d'exécution et périmètre LOT 0.
Exigences liées: LOT-000
Statut: ACCEPTED

- Le Blueprint local `/opt/revision-prix/BLUEPRINT.md` est la source de vérité.
- La fondation est limitée à Django, React/Vite/Tailwind, Nginx applicatif et PostgreSQL.
- Aucun modèle métier de révision des prix n'est implémenté dans ce lot.
- Le projet Compose est nommé `revision-prix`.
- Le réseau Docker dédié est `revision-prix-internal`; aucun conteneur existant n'y est connecté. Il n'est pas marqué `internal` car Docker 29.6.1 sur ce serveur ne publie pas correctement un port loopback depuis un bridge `internal`; l'isolation est assurée par l'absence de connexions externes et l'absence de ports publiés pour le backend/PostgreSQL.
- PostgreSQL utilise le volume `revision-prix-postgres-data` et aucun port hôte publié.
- Le frontend est le seul service publié, exclusivement sur `127.0.0.1:12701`.
- Le backend est accessible par DNS Docker (`revision-prix-backend`) et n'a pas de port hôte publié.
- Le proxy `/api/` est assuré par le Nginx applicatif vers `http://revision-prix-backend:8000`.
- Les versions d'images et de dépendances sont explicitement verrouillées; aucun tag `latest` n'est utilisé.
- Les secrets résident dans `.env`, non versionné; `.env.example` ne contient que des placeholders.
- `make push-images`, `make release`, `make deploy` et `make rollback` échouent explicitement tant qu'un registry et une procédure de release ne sont pas configurés.
- Les règles réglementaires et le métier de calcul sont reportés aux lots ultérieurs.

## ADR-LOT1B-001 — 2026-09-19 — Gouvernance du modèle Marché et Lots

ADR-ID: ADR-LOT1B-001
Date: 2026-09-19
Sujet: Faits contractuels, règles réglementaires et structure des marchés
Contexte: La conception du LOT 1B est approuvée. Les dates contractuelles
peuvent être absentes lors de la création et les règles de référence
dépendent de la procédure applicable. Le modèle doit aussi représenter
les lots sans les confondre avec les formules et conserver la sémantique
du délai exprimé en jours ou en mois.
Décision: Les faits contractuels sont stockés dans `Market` sans inventer
de date ; les règles réglementaires de référence appartiennent à
`regulatory/` et au moteur de calcul. `MarketLot` est une entité autonome
reliée obligatoirement à `Market`, sans FK vers `MarketFormula`. Le délai
est stocké par paire cohérente `contract_duration_value` /
`contract_duration_unit` (`DAYS` ou `MONTHS`) ; aucune conversion
`MONTHS × 30` n'est autorisée. La structure contractuelle est portée par
`formula_structure` (`SINGLE` ou `MULTIPLE`) et ne crée aucune formule.
Les permissions réutilisent `Membership` du LOT 1A.
Motif: Préserver les faits saisis, éviter d'encoder une règle
réglementaire non validée, séparer lot et formule, et ne pas altérer la
durée par une conversion arbitraire.
Impact: `Market` accepte les dates factuelles nullables et les statuts
`ACTIVE`/`ARCHIVED`. `MarketLot` porte sa contrainte d'unicité par marché.
Les règles métier et réglementaires dépendantes de la procédure restent
hors du modèle de persistance. La présente décision approuve la
documentation et la préparation du plan ; elle n'autorise ni modèles
Django, ni migration, ni code LOT 1B.
Exigences liées: MKT-001..MKT-020, LOT-001..LOT-004
Statut: ACCEPTED

## ADR-GOV-001 — Périmètre LOT 1A

ADR-ID: ADR-GOV-001
Date: 2026-09-16
Sujet: Authentification, utilisateurs et sociétés
Contexte: Le cahier cumulatif sépare le premier périmètre métier.
Décision: Ces éléments appartiennent au LOT 1A.
Motif: Isoler l'identité et les sociétés avant les marchés.
Impact: LOT 1A reste bloqué jusqu'à validation de GOV 1.1.
Exigences liées: AUTH-001..AUTH-004, SOC-001..SOC-012
Statut: ACCEPTED

## ADR-GOV-002 — Marchés mono/multi-formules

ADR-ID: ADR-GOV-002
Date: 2026-09-16
Sujet: Support des marchés à formule unique ou multiple
Contexte: Un marché peut contenir plusieurs lots, catégories et traitements.
Décision: Le modèle ne limite pas un marché à une seule formule.
Motif: Respecter les variantes contractuelles décrites par le CPS.
Impact: Les calculs agrègent les articles par groupe de révision.
Exigences liées: MKT-001, MKT-002, MKT-004, MKT-006..MKT-011, REV-001..REV-005
Statut: ACCEPTED

## ADR-GOV-003 — RevisionGroup

ADR-ID: ADR-GOV-003
Date: 2026-09-16
Sujet: Groupe de révision
Contexte: Des articles d'un même marché peuvent relever de traitements différents.
Décision: Introduire conceptuellement `RevisionGroup` reliant des articles à une `MarketFormula`.
Motif: Décorréler article, lot et formule.
Impact: La relation devient `Market → MarketLot → PriceItem → RevisionGroup → MarketFormula`.
Exigences liées: FRM-001
Statut: ACCEPTED

## ADR-GOV-004 — Séparation lot/formule

ADR-ID: ADR-GOV-004
Date: 2026-09-16
Sujet: MarketLot et structure contractuelle
Contexte: Un lot peut contenir plusieurs catégories et plusieurs groupes.
Décision: Un marché possède 0..N lots et un lot n'est pas une formule.
Motif: Ne pas imposer `MarketLot = Formula`.
Impact: Plusieurs groupes/formules sont possibles dans un même lot.
Exigences liées: MKT-003, LOT-001, LOT-002
Statut: ACCEPTED

## ADR-GOV-005 — PriceSchedule et PriceItem

ADR-ID: ADR-GOV-005
Date: 2026-09-16
Sujet: Bordereau des prix
Contexte: Le détail des articles est nécessaire aux marchés multi-formules mais pas obligatoirement aux marchés simples.
Décision: Prévoir `PriceSchedule` et `PriceItem` avec rattachement optionnel au lot et au groupe, sans imposer le bordereau détaillé à un marché simple et sans empêcher la décomposition approvisionnement/mise en œuvre.
Motif: Permettre l'affectation explicite des prestations.
Impact: Les imports futurs utiliseront un mapping configurable.
Exigences liées: BDP-001..BDP-010, BDP-017, IMP-002
Statut: ACCEPTED

## ADR-GOV-006 — Traitement explicite des articles

ADR-ID: ADR-GOV-006
Date: 2026-09-16
Sujet: Classification des articles
Contexte: Le régime de révision dépend du contrat/CPS et non du seul libellé.
Décision: Utiliser `REVISABLE`, `NON_REVISABLE` et `PENDING_CLASSIFICATION`; interdire la classification automatique par nom.
Motif: Éviter les décisions implicites et la fausse équivalence K=1.
Impact: Un article pending bloque la validation d'un calcul concerné.
Exigences liées: BDP-011..BDP-016
Statut: ACCEPTED

## ADR-GOV-007 — Moteur générique et Decimal

ADR-ID: ADR-GOV-007
Date: 2026-09-16
Sujet: Formules multi-indices et calculs financiers
Contexte: Les formules peuvent combiner partie fixe, coefficients et plusieurs indices.
Décision: Concevoir un moteur générique fondé sur `MarketFormula`, `FormulaTerm`, `IndexDefinition` et `IndexValue`, avec `Decimal` exclusivement.
Motif: Éviter toute dépendance à BAT3 et les erreurs de flottants.
Impact: Les valeurs PostgreSQL correspondantes utilisent NUMERIC/DECIMAL.
Exigences liées: FRM-002, FRM-003, REV-003, IDX-001, IDX-002
Statut: ACCEPTED

## ADR-GOV-008 — Décomptes et deltas

ADR-ID: ADR-GOV-008
Date: 2026-09-16
Sujet: Décompte cumulatif et détail article
Contexte: Un décompte peut être fourni en cumul ou avec détail par article.
Décision: Prévoir `Statement` et `StatementItem`; calculer le delta par article lorsque possible, puis agréger par groupe.
Motif: Conserver une base explicable pour le calcul.
Impact: Les montants de période sont déterminables par différence des cumuls.
Exigences liées: DEC-001..DEC-006
Statut: ACCEPTED

## ADR-GOV-009 — Ventilation mensuelle

ADR-ID: ADR-GOV-009
Date: 2026-09-16
Sujet: Exécution réelle prioritaire
Contexte: La répartition mensuelle réelle n'est pas toujours disponible.
Décision: Prioriser `ACTUAL_EXECUTION` et utiliser `CALENDAR_DAY_PRORATA` comme repli justifié.
Motif: Ne pas imposer un prorata jours lorsque des données réelles existent.
Impact: Méthode, valeurs et justifications sont conservées pour audit.
Exigences liées: VEN-001..VEN-005
Statut: ACCEPTED

## ADR-GOV-010 — Snapshots immuables

ADR-ID: ADR-GOV-010
Date: 2026-09-16
Sujet: Reproductibilité historique
Contexte: Les données du marché et les indices peuvent évoluer après validation.
Décision: Une révision validée fige toutes les données nécessaires et devient immuable.
Motif: Rendre le résultat historiquement reproductible.
Impact: Les modifications futures ne réécrivent pas les validations passées.
Exigences liées: OS-001, IDX-005, HIS-001..HIS-008
Statut: ACCEPTED

## ADR-GOV-011 — Documents depuis le calcul

ADR-ID: ADR-GOV-011
Date: 2026-09-16
Sujet: Génération PDF/DOCX
Contexte: La note de calcul doit expliquer le même résultat que l'application.
Décision: PDF et DOCX sont générés depuis la même donnée calculée et détaillable.
Motif: Éviter les divergences entre calcul et présentation.
Impact: Les sorties exposent groupes, formules, indices, ventilation et totaux.
Exigences liées: REV-007, DOC-001..DOC-007
Statut: ACCEPTED

## ADR-GOV-012 — Imports extensibles

ADR-ID: ADR-GOV-012
Date: 2026-09-16
Sujet: Import des bordereaux et décomptes
Contexte: Les fichiers entrants peuvent avoir des formats et colonnes différents.
Décision: Prévoir des espaces `imports/price_schedule/` et `imports/statements/` avec mapping configurable.
Motif: Ne pas coupler le modèle à Excel.
Impact: Les formats concrets seront définis lors d'une spécification dédiée.
Exigences liées: IMP-001, IMP-002
Statut: ACCEPTED

## ADR-GOV-013 — Réglementation non supposée

ADR-ID: ADR-GOV-013
Date: 2026-09-16
Sujet: Sources et règles réglementaires
Contexte: Au 2026-09-16, aucune source juridique vérifiée n'était encore intégrée.
Décision: Cette décision historique imposait PENDING_VALIDATION avant l'intégration formelle d'une source officielle ; elle est remplacée pour le noyau sourcé par ADR-REG-001.
Motif: Interdire toute interprétation réglementaire implicite.
Impact: Aucun calcul réglementaire nouveau n'est implémenté.
Exigences liées: REG-001..REG-016, PV-REG-001..PV-REG-007
Statut: SUPERSEDED

## ADR-REG-001 — Noyau réglementaire vérifié

ADR-ID: ADR-REG-001
Date: 2026-09-18
Sujet: Intégration du noyau réglementaire de révision des prix
Contexte: L'arrêté du Chef du Gouvernement n° 3-302-15 et l'avis CNCP n° 192/2025 ont été intégrés et vérifiés dans regulatory/.
Décision: Les règles REG-001 à REG-016 sont marquées VERIFIED avec leur source, article, portée et futurs tests. L'immutabilité reste une décision d'architecture distincte.
Motif: Fonder les futurs modèles et calculs sur des règles sourcées sans inventer les sous-points non établis.
Impact: Les specs et exigences liées sont mises à jour ; aucune implémentation n'est autorisée par cet ADR.
Exigences liées: REG-001..REG-016, MKT-012, BDP-018, OS-002, DEC-007, REV-008, REV-009
Statut: ACCEPTED

## ADR-GOV-014 — Git source officielle

ADR-ID: ADR-GOV-014
Date: 2026-09-16
Sujet: Référentiel officiel du code
Contexte: Le LOT 0 est publié dans `NMP26/REVISION`.
Décision: GitHub est la source officielle du code versionné, hors secrets et données persistantes.
Motif: Assurer l'identification, la revue et la reproductibilité des versions.
Impact: Les commits et tags structurent les livraisons.
Exigences liées: OPS-001
Statut: ACCEPTED

## ADR-GOV-015 — Lots contrôlés

ADR-ID: ADR-GOV-015
Date: 2026-09-16
Sujet: Autorisation progressive des lots
Contexte: Les lots métier doivent être validés dans un ordre contrôlé.
Décision: Aucun lot suivant ne démarre sans autorisation explicite et traçabilité du lot courant.
Motif: Empêcher la dérive fonctionnelle des agents.
Impact: LOT 1A, LOT 1B et suivants restent bloqués pendant GOV 1.1.
Exigences liées: OPS-002
Statut: ACCEPTED
## ADR LOT 1C — autorités contractantes et groupements

- Un groupement n’est jamais une Company ; les membres sont des Company réelles.
- Le rôle MANDATAIRE ne confère aucun droit applicatif implicite.
- Les quotes-parts sont nullable et contrôlées en Decimal ; total 100,00 % seulement si toutes sont renseignées.
- Les autorités et groupements utilisés sont désactivés plutôt que supprimés.
- La migration de `Market.company` est additive et backfillée vers le titulaire individuel, sans perte de lots, memberships ni données existantes.
- Aucun moteur de snapshot ou modèle LOT 2 n’est implémenté dans cette évolution.

## ADR-LOT2A-001 — Conception validée des formules contractuelles

ADR-ID: ADR-LOT2A-001
Date: 2026-09-20
Sujet: Groupes contractuels et formules versionnées
Contexte: LOT 1C est gelé en production v0.5.2. LOT 2A implémente les
groupes, formules et termes ; le moteur de calcul définitif reste hors lot.
Décision validée: modéliser `RevisionGroup → MarketFormula → FormulaTerm`
avec une relation versionnée 1→N entre groupe et formule. Un groupe
appartient au marché et reste indépendant de `MarketLot`. Les formules
validées sont immuables ; une évolution crée une nouvelle version. Les
statuts sont `DRAFT`, `VALIDATED` et `INACTIVE`; une formule utilisée ou
référencée n'est jamais supprimée physiquement. Les coefficients,
constantes, valeurs de base et calculs utilisent Decimal, avec un stockage
de base `NUMERIC(18,8)` sans troncature prématurée.
Motif: préserver les marchés multi-formules, plusieurs groupes par lot,
la séparation BDP/formule et la reproductibilité future des révisions.
Impact: les modèles, la migration, l'API et l'écran LOT 2A implémentent cette
décision. Les modèles LOT 2A refusent explicitement les opérations ORM bulk
qui contourneraient les invariants (`bulk_create`, `bulk_update`, `update`) ;
les créations et mutations passent par le service métier. Cette garantie est
applicative/ORM contrôlée et ne couvre pas du SQL direct. `PriceItem` n'est pas créé en
LOT 2A et sa relation future est `PriceItem N → 1 RevisionGroup`. Le BDP, les indices complets,
les snapshots et le calcul des montants restent hors LOT 2A.
Exigences liées: FRM-001..FRM-003, HIS-001..HIS-008, REG-002, REG-007.
Statut: ACCEPTED — LOT 2A implémenté, testé et gelé en v0.6.0

## ADR-LOT2A1-001 — Séparation des templates et des formules contractuelles

ADR-ID: ADR-LOT2A1-001
Date: 2026-09-20
Sujet: Bibliothèque de modèles et copie vers `MarketFormula`
Contexte: LOT 2A est gelé en v0.6.0 ; une bibliothèque doit accélérer la
création sans transformer un modèle en formule applicable à un marché.
Décision: un `FormulaTemplate` versionné est une référence réutilisable. Sa
sélection crée transactionnellement une `MarketFormula DRAFT` et des
`FormulaTerm` indépendants. Seule une provenance de copie est conservée ;
aucun calcul ne relit dynamiquement le template.
Motif: préserver l'indépendance contractuelle et empêcher toute modification
rétroactive des marchés.
Impact: le workflow template et l'API de copie sont propres à LOT 2A.1 ;
aucun `PriceItem` ou moteur de révision n'est introduit.
Exigences liées: TPL-001, TPL-009, TPL-010, TPL-011
Statut: ACCEPTED — DESIGN LOT 2A.1

## ADR-LOT2A1-002 — Versionnement, provenance et portée des templates

ADR-ID: ADR-LOT2A1-002
Date: 2026-09-20
Sujet: Familles, versions, statuts et portée GLOBAL/COMPANY
Contexte: les références doivent être traçables sans préjuger de leur
validité réglementaire.
Décision: `family_key` fournit l'identité stable, `version_number` distingue
les versions, et les statuts sont `DRAFT`, `VERIFIED`, `DEPRECATED`. LOT
2A.1 implémente prioritairement `GLOBAL` ; `COMPANY` est réservé par une
relation propriétaire nullable et des permissions futures. Une version
`VERIFIED` est immuable. `OFFICIAL` décrit une provenance, pas une
validation automatique.
Motif: séparer identité, provenance et confiance documentaire.
Impact: aucune formule n'est préchargée comme `VERIFIED` sans preuve ; les
templates utilisés sont conservés pour l'historique.
Exigences liées: TPL-002 à TPL-007, TPL-014
Statut: ACCEPTED — DESIGN LOT 2A.1

## ADR-LOT2A1-003 — Référence future aux définitions d'indices

ADR-ID: ADR-LOT2A1-003
Date: 2026-09-20
Sujet: IndexDefinition sans valeurs mensuelles dans LOT 2A.1
Contexte: les templates portent des codes d'indices, tandis que les
valeurs temporelles relèvent d'un lot réglementaire et de données futur.
Décision: LOT 2A.1 conserve `index_code` comme référence opaque et réserve
architecturalement `IndexDefinition`. Il n'implémente ni `IndexValue`, ni
barèmes, ni scraping, import PDF ou sélection temporelle automatique.
Motif: éviter une dépendance prématurée et toute formule réglementaire
implicitement calculée.
Impact: l'intégration future des valeurs d'indices devra faire l'objet d'un
lot et d'une validation documentaire distincts.
Exigences liées: TPL-008, TPL-012, TPL-013
Statut: ACCEPTED — DESIGN LOT 2A.1

## ADR-LOT2B-001 — Modèle BDP et cardinalité d'affectation

ADR-ID: ADR-LOT2B-001
Date: 2026-09-20
Sujet: `PriceSchedule`, `PriceItem` et affectation à une formule
Contexte: Le BDP doit permettre plusieurs formules dans un marché, plusieurs
articles par lot et des articles sans formule. LOT 2A possède déjà
`RevisionGroup → MarketFormula` versionné et `MarketLot` est indépendant des
formules.
Décision: créer un `PriceSchedule` au plus une fois par marché et
des `PriceItem` rattachés au bordereau. `PriceItem.revision_group` est une
FK nullable vers `RevisionGroup`, jamais une table de liaison. Le marché est
déduit du bordereau, le lot reste optionnel. L'interface traduit
`RevisionGroup` en « Formule de révision ».
Motif: une FK nullable exprime directement 0..1, empêche la multi-affectation
structurelle et conserve la stabilité du groupe pendant le versionnement des
formules.
Impact: les articles sont affectés à un groupe, non à une version individuelle
de formule. Une nouvelle `MarketFormula` dans le groupe ne force pas une
réécriture du BDP. `PriceSchedule` étant `OneToOne` avec `Market`, l'unicité
de `price_number` sur le bordereau réalise l'unicité au niveau du marché.
La cohérence inter-tables est garantie par le service/backend ; une
contrainte PostgreSQL additionnelle ne sera ajoutée que si elle exprime la
règle correctement, sans mécanisme artificiel.
Exigences liées: BDP-001..BDP-010, BDP-017, FRM-005, FRM-009, LOT2B-001..006
Statut: ACCEPTED — décision produit validée, implémentation non autorisée

## LOT 2B — Décision de gel v0.7.0

Le réaudit final LOT 2B est accepté. Les décisions ADR-LOT2B-001 à
ADR-LOT2B-006 sont implémentées, testées et validées dans le candidat
v0.7.0. Les deux parcours sont gelés : `GLOBAL_FORMULA` ne requiert pas de
BDP et `PRICE_ASSIGNMENT` impose une affectation exclusive par prix, avec
`NON_REVISABLE` explicite. La contrainte Decimal partie fixe + coefficients
indicés = 1 est conservée.

L'import Excel/CSV complet, les snapshots `StatementItem`, les indices et le
moteur de révision restent hors périmètre. La migration 0006 est incluse et
testée uniquement hors production ; la production reste en v0.6.1 sans
migration ni modification de données. Le candidat est gelé sous v0.7.0.

## ADR-LOT2B-006 — Mode explicite d'application globale ou par prix

ADR-ID: ADR-LOT2B-006
Date: 2026-09-20
Sujet: Ne pas rendre le BDP obligatoire pour une formule couvrant tout le marché
Contexte: Une seule formule peut soit couvrir toutes les prestations, soit
coexister avec des prix non révisables. Le nombre de `MarketFormula` ne
permet donc pas de déduire si le BDP est nécessaire.
Décision: ajouter un état métier explicite au niveau du marché :
`GLOBAL_FORMULA` ou `PRICE_ASSIGNMENT`. En `GLOBAL_FORMULA`, une seule
`MarketFormula` est sélectionnée et les futurs montants de décompte peuvent
référencer directement cette formule, sans `PriceSchedule`/`PriceItem`
obligatoire. En `PRICE_ASSIGNMENT`, le BDP est requis pour distinguer les
formules et les prix sans révision. Une formule unique avec des prix
`NON_REVISABLE` est obligatoirement dans `PRICE_ASSIGNMENT`.
Motif: représenter le choix contractuel explicite et éviter une obligation
technique inutile ou une couverture globale déduite à tort.
Impact: l'API et l'interface demandent explicitement le mode ; les
transitions sont validées et ne suppriment aucune donnée silencieusement.
La matrice et l'import sont conditionnels au mode `PRICE_ASSIGNMENT`.
Exigences liées: BDP-030..BDP-036, LOT2B-022..027
Statut: ACCEPTED — décision produit validée, implémentation non autorisée

## ADR-LOT2B-005 — Saisie métier des formules simples mono-index

ADR-ID: ADR-LOT2B-005
Date: 2026-09-20
Sujet: Calcul déterministe de la partie variable
Contexte: Pour une formule contractuelle simple `K = C + A × INDEX / INDEX0`,
la règle validée impose `C + A = 1`. La saisie de deux coefficients
redondants augmente le risque d'incohérence, alors que les formules
multi-indices ne suivent pas nécessairement cette complémentarité.
Décision: pour cette structure simple uniquement, l'utilisateur renseigne
la constante `C`, l'application calcule `A = 1 - C` avec `Decimal` et
présente automatiquement la partie variable. Cette règle ne s'applique pas
aux formules multi-indices sans vérification de leur structure contractuelle.
L'interface utilise le vocabulaire métier « Ajouter une formule de révision »
et masque autant que possible `RevisionGroup` et `FormulaTerm`.
Motif: éviter la saisie redondante tout en conservant la fidélité aux
structures contractuelles plus complexes.
Impact: la spécification des formules et la future UI doivent distinguer la
forme simple mono-index des formes multi-indices. La validation utilise
Decimal et reste indépendante de la politique d'arrondi réglementaire.
Exigences liées: FRM-016, LOT2B-021
Statut: ACCEPTED — décision produit validée, implémentation non autorisée

## ADR-LOT2B-002 — Classification explicite des prix sans formule

ADR-ID: ADR-LOT2B-002
Date: 2026-09-20
Sujet: Différencier hors révision et non classé
Contexte: Une absence d'affectation est valide, mais elle peut signifier soit
« volontairement hors révision », soit « pas encore décidé ». Une désignation
ne permet pas de décider automatiquement.
Décision: conserver `revision_group = NULL` pour les deux cas et imposer un
état explicite `PENDING_CLASSIFICATION`, `REVISABLE` ou `NON_REVISABLE`.
`REVISABLE` doit être affecté à un groupe avant calcul/validation.
`NON_REVISABLE` ne peut avoir aucun groupe. `PENDING_CLASSIFICATION` ne peut
recevoir aucune affectation définitive et ne peut être utilisé silencieusement
dans un calcul ; il bloque la validation qui exige une classification résolue.
Motif: ne pas inventer `K=1`, une formule « Sans révision » ou une règle par
mot-clé ; rendre l'intention utilisateur et l'incomplétude auditables.
Impact: la matrice affichera séparément sans formule et à classer. Aucune
classification ne sera déduite du texte de l'article et `NON_REVISABLE` ne
sera jamais représenté par une formule `K=1`.
Exigences liées: BDP-011..BDP-016, LOT2B-007..009
Statut: ACCEPTED — décision produit validée, implémentation non autorisée

## ADR-LOT2B-003 — Affectations bulk et matrice exclusive

ADR-ID: ADR-LOT2B-003
Date: 2026-09-20
Sujet: Affectation individuelle et « Tout sélectionner »
Contexte: Une matrice de plusieurs centaines de prix doit permettre une
affectation rapide sans jamais produire de chevauchement.
Décision: exposer une mutation bulk d'affectation/désaffectation,
protégée par OWNER/ADMIN, exécutée dans une transaction avec verrouillage des
articles concernés. Une affectation remplace l'ancien groupe ; une
désaffectation met le groupe à NULL et ne choisit aucune autre formule.
L'opération peut recevoir une liste d'IDs validés pour le marché ou un filtre
serveur reproductible. Le frontend ne constitue qu'une aide visuelle.
Motif: rendre l'exclusivité atomique et éviter une boucle de PATCH partiels.
Impact: l'API devra être idempotente, retourner les compteurs et signaler
les lignes refusées. La pagination/virtualisation n'aura pas à charger tous
les articles pour effectuer un « Tout sélectionner ».
Exigences liées: BDP-019..BDP-023, LOT2B-010..014
Statut: ACCEPTED — décision produit validée, implémentation non autorisée

## ADR-LOT2B-004 — Numérotation, intégrité inter-marchés et historique

ADR-ID: ADR-LOT2B-004
Date: 2026-09-20
Sujet: Unicité des prix et préparation des snapshots
Contexte: Les numéros de prix peuvent contenir des zéros, lettres et points.
Les futurs décomptes doivent rester reproductibles après modification du BDP.
Décision: conserver `price_number` comme chaîne et le rendre unique dans le
`PriceSchedule` canonique du marché. Puisque `PriceSchedule` est `OneToOne`
avec `Market`, `UNIQUE(price_schedule, price_number)` n'est pas une
unicité globale et couvre le marché. Les doublons d'import sont rejetés
avant écriture. Les affectations vers un lot ou un groupe d'un autre marché
sont bloquées par le backend/service ; aucune contrainte PostgreSQL
inter-table artificielle n'est imposée si elle ne peut être démontrée
correcte.
Les prix et formules utilisés par un décompte validé seront copiés dans un
future snapshot `StatementItem`; LOT 2B ne crée pas ce modèle.
Motif: préserver les identifiants contractuels, éviter les écrasements
silencieux et isoler l'historique des valeurs vivantes.
Impact: `Market` porte le bordereau canonique, `MarketLot` ne crée pas un
espace de numérotation distinct et `PriceItem` conserve le numéro. Une
formule/groupe utilisé ne sera pas supprimé physiquement. Un écart entre
quantité × PU HT et montant HT importé est signalé, jamais corrigé
silencieusement ; aucun seuil ou arrondi n'est inventé.
Exigences liées: BDP-003, BDP-009, IMP-001, IMP-002, DEC-003..DEC-004,
HIS-002..HIS-008, LOT2B-015..020
Statut: ACCEPTED — décision produit validée, implémentation non autorisée
