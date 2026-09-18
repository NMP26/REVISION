STATUS: DRAFT
SOURCE: pending governance specification

# Décomptes

Gabarit réservé à la spécification validée des décomptes.

## Concepts approuvés

`Statement` porte numéro, date, période début/fin, montant HT, cumul
éventuel, indication de dernier décompte et observations.

`StatementItem` référence un `PriceItem` et porte quantité période,
quantité cumulative, montant période HT, montant cumulatif HT, snapshot
du `RevisionGroup` et snapshot du traitement de révision.

Le montant période doit pouvoir être déterminé par différence entre
cumul courant et cumul précédent. Lorsque le détail existe, le delta
est calculable par article puis agrégable par `RevisionGroup`.

## Règles réglementaires intégrées — éléments PLANNED

Le `Statement` doit identifier explicitement le dernier décompte
provisoire. Pour le traitement des valeurs d'index, distinguer le
décompte provisoire ordinaire du dernier décompte provisoire selon
REG-010 et REG-011. Le décompte définitif doit faire ressortir le total
de révision et un état récapitulatif (DEC-007).
