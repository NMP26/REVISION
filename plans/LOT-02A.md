STATUS: APPROVED DESIGN — LOT 2A FROZEN v0.6.0
IMPLEMENTATION: CODE PRESENT — TESTED — FROZEN v0.6.0
SOURCE: BLUEPRINT §§10–11, 57 ; specs/03-formules.md ; ADR-LOT2A-001

# Plan LOT 2A — Formules contractuelles

## Objectif

Concevoir puis implémenter les groupes contractuels et les formules
versionnées d’un marché, sans implémenter le bordereau, les décomptes, les
indices complets ni le moteur de révision.

## Périmètre inclus dans le futur développement

- `RevisionGroup` rattaché à `Market` ;
- `MarketFormula` versionnée ;
- `FormulaTerm` ordonnée et multi-index ;
- constante et coefficients Decimal ;
- valeurs de base, périodes et provenance explicites ;
- statuts DRAFT/VALIDATED/INACTIVE ;
- validation de cohérence ;
- API et UI de gestion des groupes/formules ;
- évaluateur pur Python limité à l’évaluation d’un K ;
- tests d’isolation, permissions, Decimal, versions et index manquants.

## Hors périmètre

- `PriceSchedule`/`PriceItem` et import ;
- `WorkSuspension` et calendrier ;
- `Statement`/`StatementItem` ;
- référentiel officiel des indices ;
- ventilation mensuelle ;
- calcul des montants de révision ;
- snapshots de révision ;
- régularisations ;
- documents PDF/DOCX.

## Dépendances

- `Market`, `MarketLot`, `Company` et Membership existants ;
- validation de `PV-REG-001` pour le mode d’arrondi avant toute sortie
  réglementaire définitive ;
- définition future de la sélection temporelle avec le moteur de révision ;
- contrat détaillé du BDP en LOT 2B.

## Modèles futurs

```text
RevisionGroup 1 ─── N MarketFormula 1 ─── N FormulaTerm
MarketLot 1 ─── N PriceItem (LOT 2B)
PriceItem N ─── 1 RevisionGroup (LOT 2B)
```

Une formule validée ne sera pas modifiée et ne sera jamais supprimée
physiquement si elle est utilisée ou référencée. Les futures révisions
référenceront sa version puis en copieront les données dans un snapshot.

## Migrations futures

Migrations additives uniquement : tables et contraintes des trois modèles,
sans modification destructive de `Market`, `MarketLot`, Company ou
Consortium. Aucune migration ne doit être créée dans la phase actuelle.

## API et UI futures

Les routes et écrans proposés sont documentés dans `architecture/API.md`
et `specs/03-formules.md`. Le détail marché affichera les groupes, leur
formule courante, les termes, le statut et la provenance de la base.

## Matrice de tests

- formule simple `C + aI/I0` ;
- formule multi-index ;
- Decimal sans float ;
- somme des coefficients et constante ;
- DRAFT incomplet puis VALIDATED ;
- doublon de position ou terme ;
- valeur de base absente/nulle ;
- index courant absent → `PENDING_INDEX` ;
- version validée immuable ;
- isolation entre marchés ;
- permissions OWNER/ADMIN/MEMBER ;
- sérialisation des Decimal en chaînes ;
- property tests sur ordre, bornes et conservation des termes ;
- aucune mutation de template vers une formule existante.

## Critères d’acceptation

Le lot ne sera considéré terminé que lorsque :

1. la spécification est approuvée ;
2. les décisions réglementaires requises sont documentées ;
3. les migrations sont additives et auditées ;
4. les coefficients utilisent Decimal ;
5. une formule validée est immuable ;
6. les opérations ORM bulk qui contourneraient les invariants sont refusées ;
7. aucun index manquant n’est substitué silencieusement ;
8. les groupes restent indépendants des lots ;
9. les tests backend/frontend, le moteur pur Python et les migrations
   sont passés ;
10. la traçabilité est mise à jour ;
11. l’autorisation de développement et de livraison est explicite.

## Bloquants avant implémentation

- `specs/03-formules.md` doit être approuvée ;
- ce plan doit être approuvé ;
- `PV-REG-001` doit être tranché pour toute production de coefficient
  réglementaire définitif ; il ne bloque pas le stockage, le versionnage
  ou l’UI LOT 2A ;
- le contrat futur avec le BDP doit être validé en LOT 2B.
