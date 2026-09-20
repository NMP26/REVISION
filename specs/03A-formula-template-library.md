STATUS: IMPLEMENTED — TESTED — FROZEN v0.6.1
IMPLEMENTATION: LOT 2A.1 — GLOBAL TEMPLATES AND COPY WORKFLOW
SOURCE: BLUEPRINT §§2, 11, 21 ; ADR-LOT2A1-001 ; ADR-LOT2A1-002 ; ADR-LOT2A1-003

# Bibliothèque des modèles de formules — LOT 2A.1

## 1. Objet et périmètre

LOT 2A.1 ajoute une bibliothèque de modèles réutilisables destinée à
préremplir une `MarketFormula`. Un modèle n'est jamais la formule
applicable à un marché : le CPS du marché reste la référence contractuelle.

Le lot couvre prioritairement les modèles `GLOBAL`, partagés par
l'application. Le modèle de données réserve la portée `COMPANY` pour un lot
ultérieur, sans exposer ni gérer cette portée dans LOT 2A.1.

Le lot ne couvre pas :

- `IndexValue` ou les valeurs mensuelles ;
- barèmes, scraping, import PDF ou publication automatique ;
- sélection réglementaire temporelle des indices ;
- moteur complet de révision, ventilation, décomptes ou montants ;
- `PriceSchedule`, `PriceItem` ou import BDP de LOT 2B ;
- préchargement d'une formule officielle non vérifiée.

## 2. Séparation de domaine

```text
FormulaTemplate version VERIFIED
              |
              | copie transactionnelle
              v
MarketFormula DRAFT propre au marché
              |
              v
FormulaTerm propres au marché
```

La copie est une opération métier backend. Après la copie, les données de
`MarketFormula` et de ses `FormulaTerm` sont autonomes. Une modification,
une nouvelle version ou une dépréciation du template ne modifie jamais une
formule marché existante.

`MarketFormula` conserve uniquement une provenance de copie, par exemple
`source_template_id` et `source_template_version`. Cette provenance est
informative et ne doit pas être relue pour évaluer la formule.

## 3. FormulaTemplate versionné

`FormulaTemplate` est une ligne versionnée. `family_key` est l'identité
stable de la famille ; `version_number` identifie une version donnée.

```text
FormulaTemplate
  id UUID
  family_key UUID
  version_number entier positif
  scope GLOBAL | COMPANY
  owner_company FK Company nullable — réservé à COMPANY
  code
  designation
  description nullable
  domain nullable — descriptif, jamais une règle de sélection
  expression_display
  constant_term NUMERIC(18,8)/Decimal nullable
  status DRAFT | VERIFIED | DEPRECATED
  valid_from nullable
  valid_to nullable
  source_type OFFICIAL | CONTRACT_EXAMPLE | INTERNAL
  source_title nullable
  source_url nullable
  source_reference nullable
  source_date nullable
  verification_status
  verified_at nullable
  verified_by nullable
  notes nullable
  created_at
  updated_at
```

Contraintes proposées :

- unicité `(family_key, version_number)` ;
- `scope=GLOBAL` implique `owner_company=NULL` ;
- `scope=COMPANY` nécessitera une société propriétaire lorsqu'il sera activé ;
- une version `VERIFIED` est immuable ;
- une version utilisée pour une copie n'est jamais supprimée physiquement ;
- `DEPRECATED` reste lisible et traçable mais n'est plus proposée par
  défaut pour une nouvelle copie ;
- `OFFICIAL` ne signifie pas automatiquement `VERIFIED`.

LOT 2A.1 crée uniquement des versions `GLOBAL`. Les templates `COMPANY`,
leur ownership et leurs permissions d'administration sont réservés à une
évolution ultérieure.

## 4. FormulaTemplateTerm

```text
FormulaTemplateTerm
  id UUID
  template FK FormulaTemplate
  position entier positif, unique par template
  coefficient NUMERIC(18,8)/Decimal
  term_type INDEX_RATIO dans LOT 2A.1
  index_code
  base_period_year nullable
  base_period_month nullable
  base_value NUMERIC(18,8)/Decimal nullable
  base_source nullable
  reference_note nullable
  created_at
  updated_at
```

Les contrôles de type, position, Decimal et valeur de base reprennent les
invariants structurels de `FormulaTerm`. Aucune règle n'est déduite du
nom du domaine ou du code d'index.

## 5. Statuts et vérification

- `DRAFT` : modèle en préparation, non présenté comme référence vérifiée ;
- `VERIFIED` : provenance et contenu vérifiés selon le processus documentaire ;
- `DEPRECATED` : modèle conservé pour l'historique, déconseillé pour les
  nouvelles copies.

La provenance est indépendante du statut. Un document officiel peut être
enregistré avec `source_type=OFFICIAL` tout en restant `DRAFT` ou non vérifié.
Le passage à `VERIFIED` exige une source, une référence documentaire et une
trace de vérification (`verification_status`, `verified_at`, `verified_by`)
selon le processus approuvé.

La bibliothèque ne précharge actuellement aucun template `VERIFIED`.

## 6. Indices

LOT 2A.1 conserve `index_code` comme référence contractuelle opaque.
`IndexDefinition` est une dépendance architecturale future :

```text
IndexDefinition
  code
  designation
  domain
  source
  active
```

`IndexDefinition` n'est pas implémenté dans LOT 2A.1. `IndexValue`, les
valeurs mensuelles, barèmes et imports restent dans un lot ultérieur. Aucun
template ne doit dépendre de valeurs courantes pour être copié.

## 7. Copie vers une formule marché

Endpoint métier recommandé :

```text
POST /api/markets/{market_id}/revision-groups/{group_id}/formulas/from-template/
```

Le backend :

1. vérifie l'accès d'écriture au marché ;
2. vérifie que le template GLOBAL est `VERIFIED` et non `DEPRECATED` par
   défaut ;
3. verrouille le groupe dans une transaction ;
4. calcule le prochain numéro de version sans race condition ;
5. copie la structure, constante, expression, termes, ordre, codes d'index
   et informations de base ;
6. crée une `MarketFormula DRAFT` ;
7. copie les `FormulaTerm` ;
8. enregistre la provenance de copie ;
9. retourne la nouvelle formule DRAFT.

La formule copiée peut ensuite être modifiée et validée selon les règles
LOT 2A. Le template ne devient jamais automatiquement applicable au marché.

## 8. UX

```text
Marché → Groupe de révision → Ajouter une formule
       → [Utiliser un modèle] [Créer une formule personnalisée]
```

Le sélecteur affiche : recherche, filtres, désignation, version, expression,
source, statut et aperçu des termes. L'action finale est intitulée
« Utiliser ce modèle ».

Avant ou après la copie, l'interface affiche obligatoirement :

> Vérifiez que cette formule correspond aux dispositions du CPS de votre marché.

La copie est identifiée comme `MarketFormula DRAFT` indépendante et reste
modifiable avant validation.

## 9. Formules et sources

Les sources actuellement intégrées établissent la forme générique
`P=P0[k+a(X/X0)+b(Y/Y0)+…]`, la contrainte `k≥0,15` lorsqu'elle s'applique
et la somme des coefficients égale à 1. Le cas mono-index générique est
également documenté.

La formule `K = 0,15 + 0,85 × BAT3/BAT3₀` reste un exemple de fixture ou de
contrat non qualifié comme formule officielle. Aucun template BAT3 n'est
préchargé et BAT3 ne doit jamais être codé en dur.

`PV-REG-001` reste `PENDING_VALIDATION`.

## 10. Hors périmètre et critères de préparation

La conception est prête lorsque :

- la séparation template/formule est explicite ;
- le versionnement et l'immutabilité sont définis ;
- la provenance et la vérification sont traçables ;
- la copie transactionnelle est spécifiée ;
- GLOBAL est supporté sans empêcher COMPANY ultérieur ;
- IndexDefinition est référencé sans introduire IndexValue ;
- aucun domaine ne déduit automatiquement une formule ;
- LOT 2B et le moteur de révision restent hors périmètre.

## 11. Requirement IDs

| ID | Exigence | Statut conception |
|---|---|---|
| TPL-001 | Un template est distinct d'une `MarketFormula` contractuelle. | APPROVED |
| TPL-002 | Une famille possède une identité stable et des versions numérotées uniques. | APPROVED |
| TPL-003 | Les statuts sont `DRAFT`, `VERIFIED` et `DEPRECATED`. | APPROVED |
| TPL-004 | Une version `VERIFIED` est immuable ; toute évolution crée une nouvelle version. | APPROVED |
| TPL-005 | La portée `GLOBAL` est implémentée en priorité ; `COMPANY` reste réservée sans bloquer son ajout futur. | APPROVED |
| TPL-006 | La provenance est explicite et inclut le type, la source et les éléments de vérification. | APPROVED |
| TPL-007 | `OFFICIAL` ne vaut pas `VERIFIED` sans vérification documentaire. | APPROVED |
| TPL-008 | Les termes supportent les formules simples et multi-index avec des coefficients Decimal. | APPROVED |
| TPL-009 | La sélection d'un template crée une `MarketFormula DRAFT` indépendante. | APPROVED |
| TPL-010 | La copie conserve structure, termes, ordre, bases et provenance de copie. | APPROVED |
| TPL-011 | Une évolution du template ne modifie jamais une formule marché existante. | APPROVED |
| TPL-012 | Aucun domaine, code d'index ou exemple BAT3 ne déclenche une sélection automatique. | APPROVED |
| TPL-013 | `IndexDefinition` est réservé architecturalement ; `IndexValue` et les barèmes sont hors lot. | APPROVED |
| TPL-014 | Un template utilisé n'est pas supprimé physiquement ; `DEPRECATED` reste traçable et non proposé par défaut. | APPROVED |
