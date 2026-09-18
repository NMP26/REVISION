STATUS: DRAFT
SOURCE: GOV 1.1 — contraintes fonctionnelles approuvées

# Bordereau des prix

## Éléments fonctionnels APPROVED

| ID | Obligation |
|---|---|
| BDP-001 | La présence du BDP est activable selon le marché. |
| BDP-002 | PriceSchedule regroupe les PriceItem d'un marché. |
| BDP-003 | PriceItem porte un numéro de prix. |
| BDP-004 | PriceItem porte une désignation. |
| BDP-005 | PriceItem porte une unité. |
| BDP-006 | PriceItem porte les quantités. |
| BDP-007 | PriceItem porte un prix unitaire HT. |
| BDP-008 | PriceItem porte un montant estimatif. |
| BDP-009 | PriceItem peut être rattaché à un lot. |
| BDP-010 | PriceItem peut être rattaché à un RevisionGroup. |
| BDP-011 | Le traitement REVISABLE est explicite. |
| BDP-012 | Le traitement NON_REVISABLE est explicite. |
| BDP-013 | Un article non classé reste PENDING_CLASSIFICATION. |
| BDP-014 | PENDING_CLASSIFICATION bloque la validation concernée. |
| BDP-015 | NON_REVISABLE ne signifie pas formule K=1. |
| BDP-016 | Aucune classification n'est déduite du seul nom. |
| BDP-017 | Une prestation reste compatible avec approvisionnement à pied d'œuvre / mise en œuvre. |
| BDP-018 | Une prestation d'approvisionnement conserve sa date effective d'approvisionnement. |
| IMP-002 | Le mapping de colonnes est configurable et indépendant d'Excel. |

Pour un marché simple à formule unique, le BDP détaillé n'est pas une
condition obligatoire de la révision. Pour un marché multi-formules,
PriceSchedule et PriceItem permettent l'affectation explicite.

## Éléments DRAFT / TBD

Les contraintes de modèle, import, validations détaillées et cas
d'interface restent à spécifier avant développement.
