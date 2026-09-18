STATUS: DRAFT
SOURCE: REG V1 — concepts fonctionnels approuvés, détail à valider

# Indices et barèmes

Gabarit réservé à la spécification validée des indices et barèmes.

## Concepts approuvés

Le référentiel distingue `IndexDefinition` et `IndexValue`. Une valeur
conserve code, désignation, mois, valeur, statut, date de publication,
source officielle et historique.

Une valeur absente ne peut devenir zéro, reprendre silencieusement le
mois précédent ou être extrapolée automatiquement. Les règles exactes
de statut et d'utilisation restent dans `regulatory/`. Le décompte
provisoire ordinaire et le dernier décompte provisoire suivent des règles
distinctes ; les états PENDING_INDEX/PENDING_REVISION restent des choix
de modèle TBD.
