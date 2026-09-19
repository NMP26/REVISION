STATUS: APPROVED — LOT 1A GELÉ v0.3.0 / LOT 1B IMPLEMENTÉ
IMPLEMENTATION: LOT 1A GELÉE ; LOT 1B IMPLEMENTED — TESTED, NON VALIDATED
SOURCE: ADR-LOT1B-001, specs/02-marches.md

# Plan LOT 01

LOT 1 reste le lot parent historique du Blueprint. Il est exécuté en deux
sous-lots : LOT 1A et LOT 1B. LOT 1A reste gelé sur `v0.3.0` ; la présente
phase ne modifie pas son fonctionnement. LOT 1B est implémenté et testé ;
sa validation finale reste une étape d'audit distincte.

## LOT 1A — état gelé

La version de référence est `v0.3.0` / commit
`0bcafd0d3b50637578c4afe47838c8d897f9af61`. Aucun changement fonctionnel
LOT 1A n'est autorisé dans le cadre du plan LOT 1B.

## LOT 1B — périmètre approuvé

`Market` : FK `Company` obligatoire, numéro obligatoire et unique par
société, autorité contractante et objet obligatoires, montant HT nullable
en `Decimal(18,2)` avec validation positive ou nulle, dates factuelles
nullables, TVA en pourcentage humain, structure `SINGLE`/`MULTIPLE`, délai
par valeur/unité `DAYS` ou `MONTHS`, statut `ACTIVE`/`ARCHIVED`.
La société est choisie à la création puis immuable.

`MarketLot` : FK `Market` obligatoire, numéro/code et titre obligatoires,
description/montant/notes optionnels, ordre d'affichage >= 0, actif par
défaut, timestamps et unicité `(market, lot_number)`. Aucun lot fictif,
`has_lots`, lien direct vers `MarketFormula` ou rapprochement automatique
des montants.

Permissions : réutilisation de `Membership` LOT 1A ; OWNER/ADMIN actifs
pour create/update, MEMBER actif pour read, aucun accès sans membership
actif, exception superuser Django existante.

## Plan d'implémentation futur

Ce plan identifie les travaux réalisés et les contrôles restant à mener.

### A. Backend models

- `backend/markets/apps.py`
- `backend/markets/models.py`
- `backend/markets/admin.py` si l'interface administrative le justifie
- mise à jour ciblée de la configuration Django uniquement si nécessaire

Créer `Market` et `MarketLot` selon `architecture/DATA_MODEL.md`, sans
introduire `MarketFormula` ni `WorkSuspension` dans LOT 1B.

### B. Migrations

- `backend/markets/migrations/0001_initial.py`

La migration `0001_initial.py` a été produite après revue du schéma et ne
contient que les objets LOT 1B prévus.

### C. Serializers / API

- `backend/markets/serializers.py`
- `backend/markets/views.py`
- `backend/markets/urls.py`
- `backend/core/urls.py` (raccordement des routes)

Les validations couvriront les champs obligatoires, montants, TVA,
cohérence de durée, unités, statuts et contraintes d'unicité.

### D. Permissions

- `backend/markets/permissions.py`
- réutilisation vérifiée de `backend/companies/models.py` et
  `backend/companies/permissions.py`

Aucun RBAC parallèle ne sera introduit.

### E. Tests backend

- `backend/markets/tests.py`
- `backend/markets/tests.py`

Cas prévus : création/mise à jour, accès OWNER/ADMIN/MEMBER, absence de
membership, montant et TVA, dates nulles, délai incohérent, absence de
conversion mois/jours, statuts, unicités Market/MarketLot et absence de
lot automatique.

### F. Frontend routes/pages

- `frontend/src/markets/MarketsPage.tsx`
- `frontend/src/markets/MarketsPage.tsx` (liste, création et détail)
- `frontend/src/App.tsx`
- `frontend/src/lib/api.ts`

Les écrans réutiliseront le contexte de société/marché sans redemander le
marché dans ses sous-écrans.

### G. Formulaire Market réutilisable

- `frontend/src/markets/MarketForm.tsx`
- `frontend/src/markets/MarketForm.test.tsx`

Le formulaire distinguera dates absentes et dates saisies, affichera la
TVA comme pourcentage humain et imposera la cohérence du délai sans
inventer de valeur.

### H. Gestion MarketLot

- `frontend/src/markets/MarketsPage.tsx` (section lots)
- `frontend/src/markets/MarketLotForm.tsx`
- `frontend/src/markets/MarketLotForm.test.tsx`

La gestion couvrira l'ordre, l'activation et l'unicité signalée par l'API,
sans champ `has_lots` ni totalisation automatique vers le marché.

### I. Tests frontend

- `frontend/src/markets/MarketsPage.test.tsx`
- `frontend/src/markets/MarketsPage.test.tsx`
- tests des formulaires ci-dessus

Les tests vérifieront les droits d'interface comme représentation de l'API,
sans considérer le masquage d'un bouton comme une autorisation.

### J. Documentation / traçabilité finale

- mise à jour de `specs/02-marches.md`
- mise à jour de `architecture/DATA_MODEL.md` et `architecture/API.md`
- mise à jour de `TRACEABILITY.md`
- mise à jour de `ROADMAP.md`, `BLUEPRINT.md` et du présent plan

Cette étape a produit les preuves `IMPLEMENTED` et `TESTED`. Le statut
`VALIDATED` reste réservé à l'audit final.

### K. Audit

- revue `git diff --check`, statut et diff stat
- contrôle d'absence de secret et d'infrastructure modifiée
- audit des permissions et de la non-régression LOT 1A
- revue du schéma avant migration

## Critère de reprise

La phase d'implémentation LOT 1B est terminée pour Market et MarketLot.
Les composants de lots ultérieurs restent hors périmètre.
