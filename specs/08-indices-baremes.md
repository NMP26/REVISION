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

## Règle V1 — indice mensuel manquant

La migration V1 minimale implémente `IndexDefinition` et `IndexValue` pour
la résolution du mois de base du parcours formule unique. Elle ne couvre pas
les imports, barèmes, scraping ni les calculs de révision. La date source est
exclusivement `Market.date_limite_remise_offres`; aucune valeur n'est
dupliquée dans React et aucun mois voisin n'est utilisé comme repli.

Pour chaque mois de la ventilation d'un décompte V1, si l'indice requis
n'est pas disponible, la note de calcul affiche exactement :

```text
Index non disponible
```

Le calcul est bloqué pour la ligne concernée. Aucun zéro, aucune reprise du
mois précédent, aucune valeur inventée et aucun fallback provisoire non
validé ne sont autorisés.
