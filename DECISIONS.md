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
