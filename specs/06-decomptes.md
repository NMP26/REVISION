STATUS: APPROVED FOR V1 SCOPE — IMPLEMENTATION NOT AUTHORIZED
SOURCE: décision produit V1 — décompte simple et jours de travaux par mois

# Décomptes

## Périmètre V1

En V1, `Statement` est une enveloppe financière HT rattachée au marché.
Il porte uniquement : numéro du décompte, date du décompte, montant HT en
`Decimal` et observation facultative.

Il ne porte aucun article, quantité, unité, prix unitaire, lot, BDP,
`PriceItem`, `StatementItem` ou groupe de révision dans le parcours V1.
Les dates de période de réalisation ne sont pas des champs du `Statement`
V1 ; elles relèvent de l'OS/calendrier et des données d'exécution.

## Jours de travaux par mois

Un décompte V1 conserve les mois concernés par la note de calcul via une
structure dédiée, conceptuellement nommée `MonthlyWorkAllocation` :

```text
Statement
  └── MonthlyWorkAllocation
        - year
        - month
        - work_days
```

Les mois à zéro jour restent conservés et affichés. Le total des jours est
contrôlé. Le montant mensuel est calculé avec `Decimal` par :

```text
Montant_mois = Montant_HT_décompte × jours_mois / total_jours
```

La somme des montants mensuels doit égaler exactement le montant HT du
décompte. L'écart d'arrondi éventuel est affecté explicitement à la dernière
ligne/mois. Cette règle est planifiée pour V1-C ; aucune migration n'est
créée par cette spécification.

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
