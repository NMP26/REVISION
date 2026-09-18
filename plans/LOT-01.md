STATUS: APPROVED
SOURCE: GOV 1.1 — critères d'acceptation documentaires
IMPLEMENTATION: NON AUTORISÉE DANS GOV 1.1

# Plan LOT 01

LOT 1 est le lot parent historique du Blueprint. Il est exécuté en deux
sous-lots : LOT 1A et LOT 1B. Aucun développement du LOT 1 n'est autorisé
pendant GOV 1.1.

## LOT 1A — Authentification / Utilisateurs / Sociétés

### Périmètre

- authentification, déconnexion et gestion des utilisateurs ;
- sociétés : création, consultation, modification et archivage selon la spec ;
- validations backend, API et UI ;
- persistance PostgreSQL et traçabilité.

L'architecture d'authentification n'est pas encore choisie. Sessions,
tokens, récupération/changement de mot de passe et permissions détaillées
restent TBD jusqu'à décision documentée.

### Critères d'acceptation documentaires

Chaque critère doit être prouvé par un test ou un contrôle identifié dans
TRACEABILITY.md :

- AUTH-001 : accès authentifié aux fonctions privées ;
- AUTH-002 : sessions/tokens conformes à l'architecture retenue ;
- AUTH-003 : refus d'accès non authentifié ;
- AUTH-004 : aucune donnée sensible exposée ;
- SOC-001 : création d'une société ;
- SOC-002 : consultation d'une société ;
- SOC-003 : modification d'une société ;
- SOC-004 : validations des données ;
- SOC-005 : champs conformes à la spec société ;
- SOC-006 : persistance PostgreSQL ;
- SOC-007 : API société ;
- SOC-008 : UI conforme aux sketches/specs ;
- SOC-009 : tests backend ;
- SOC-010 : tests API pertinents.
- SOC-011 : rattachement utilisateur/société si cette relation est retenue par la spec.
- SOC-012 : tests frontend pertinents.

### Definition of Done LOT 1A

- exigences autorisées implémentées ;
- migrations appliquées ;
- tests réussis ;
- traçabilité mise à jour ;
- aucune régression LOT 0 ;
- `make doctor` réussi ;
- revue avant commit/version.

Le passage à l'implémentation exige une autorisation explicite après
validation GOV 1.1.

## LOT 1B — Marchés / Lots / Structure contractuelle

### Périmètre minimal

- création et modification d'un marché ;
- rattachement à une société ;
- données contractuelles : date d'ouverture des plis, époque de base,
  OS de commencement, délai, TVA et montant HT ;
- choix du mode de gestion de la révision ;
- support mono-formule et multi-formules ;
- `MarketLot), cardinalité 0..N lots et contrainte `Lot != Formula` ;
- architecture compatible avec `RevisionGroup`, `PriceSchedule` et
  `PriceItem`.

### Critères d'acceptation documentaires

Le futur LOT 1B devra démontrer au minimum MKT-001 à MKT-011, LOT-001,
LOT-002 et la compatibilité avec FRM-001, BDP-002 et BDP-010. Les critères
de création, modification, API, validations, persistance, UI et tests
seront détaillés dans la spec marchés avant développement.

Avant toute migration définitive du LOT 1B, l'agent présente le schéma de
données proposé, ses cardinalités, contraintes et relations pour
validation explicite. Cette présentation n'est pas une migration et
n'autorise pas le développement.

## État de gouvernance

LOT 1A et LOT 1B restent BLOQUÉS. Ce document définit les critères futurs ;
il ne commence ni LOT 1A ni LOT 1B.
