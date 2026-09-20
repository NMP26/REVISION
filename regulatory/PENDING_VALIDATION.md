STATUS: DRAFT
SOURCE: REG V1 — sous-points non couverts par les sources intégrées

# Points en attente de validation

## État

- Règles réglementaires VERIFIED : 16.
- Sous-points PENDING_VALIDATION : ci-dessous.
- Aucun élément ci-dessous ne doit être complété par supposition.

## PV-REG-001 — Mode informatique d'arrondi

L'arrêt à la quatrième décimale est VERIFIED par l'article 8, mais le mode
informatique exact (par exemple ROUND_HALF_UP) n'est pas précisé dans les
éléments intégrés. Le choix doit rester TBD jusqu'à validation.

Impact LOT 2A : ce point ne bloque pas le stockage/versionnage des formules,
les validations structurelles ni l'UI de gestion. Il bloque toute sortie
présentée comme un coefficient réglementaire définitif lorsque cet arrondi
est nécessaire. La politique doit rester centralisée et explicite ; aucun
mode (`ROUND_HALF_UP`, `ROUND_HALF_EVEN`, `ROUND_DOWN` ou autre) n'est
choisi par la présente documentation.

## PV-REG-002 — Arrêts, reprises et effets détaillés

Les effets détaillés de chaque type d'arrêt/reprise sur les périodes et
indices ne sont pas établis par les sources intégrées.

## PV-REG-003 — Imputabilité du retard

Le logiciel ne peut pas qualifier seul un retard comme imputable au
titulaire. La donnée, son auteur et sa validation restent à définir.

## PV-REG-004 — Catégories de prestations

Aucune exclusion automatique d'une catégorie de prestation n'est retenue
sans source explicite.

## PV-REG-005 — Location

La règle « location = non révisable » n'est pas retenue sans source
explicite.

## PV-REG-006 — Index provisoire hors article 12

Aucune généralisation du traitement des index provisoires n'est retenue
en dehors du cas précis du dernier décompte provisoire et du cas du
décompte provisoire ordinaire documentés par les sources intégrées.

## PV-REG-007 — Autres exceptions

Toute autre exception non explicitement sourcée doit être ajoutée ici
avant interprétation ou implémentation.
