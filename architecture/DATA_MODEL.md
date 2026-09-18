STATUS: DRAFT
SOURCE: pending governance specification

# Modèle de données

Gabarit réservé à la description d'architecture validée du modèle de
données.

## Relations conceptuelles

```text
Market → MarketLot (0..N) → PriceItem → RevisionGroup
RevisionGroup → MarketFormula → FormulaTerm → IndexDefinition/IndexValue
PriceItem → StatementItem → Statement
```

Le modèle doit séparer lot, article, groupe de révision et formule.
Cette description n'est pas une migration ni un modèle Django.
