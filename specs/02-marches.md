STATUS: DRAFT
SOURCE: GOV 1.1 — contraintes fonctionnelles approuvées, détail à valider

# Marchés

## Éléments fonctionnels APPROVED

| ID | Obligation |
|---|---|
| MKT-001 | Supporter un marché mono-formule. |
| MKT-002 | Supporter un marché multi-formules. |
| MKT-003 | Autoriser zéro à plusieurs MarketLot. |
| MKT-004 | Permettre le choix du mode de gestion de la révision. |
| MKT-005 | Rattacher un marché à une société. |
| MKT-006 | Conserver la date d'ouverture des plis. |
| MKT-007 | Conserver l'époque de base. |
| MKT-008 | Conserver l'OS de commencement. |
| MKT-009 | Conserver le délai contractuel. |
| MKT-010 | Conserver la TVA. |
| MKT-011 | Conserver le montant HT. |
| MKT-012 | Conserver la règle et la date de référence des indices selon la procédure du marché. |
| LOT-001 | Autoriser plusieurs PriceItem dans un lot. |
| LOT-002 | Maintenir Lot != Formula. |

Les données contractuelles comprennent au minimum date d'ouverture des
plis, date limite de remise des offres, date de signature si marché
négocié, règle et mois de référence, époque de base, OS de commencement,
délai, TVA et montant HT.
L'architecture doit rester compatible avec RevisionGroup, PriceSchedule et
PriceItem.

## Éléments DRAFT / TBD

Les champs définitifs, cardinalités, contraintes d'intégrité, API, UI et
règles de modification restent à spécifier avant implémentation. Avant
les migrations définitives du LOT 1B, le schéma proposé doit être présenté
pour validation.
