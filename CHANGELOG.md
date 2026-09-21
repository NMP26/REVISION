# Changelog

## v0.7.0 — LOT 2B Bordereau et affectation aux formules

- `PriceSchedule` et `PriceItem` avec numéro opaque, valeurs Decimal, lot
  optionnel et classification explicite.
- Parcours `GLOBAL_FORMULA` sans BDP obligatoire ni création artificielle de
  `PriceItem` ; parcours `PRICE_ASSIGNMENT` avec affectation exclusive et
  possibilité explicite « Sans révision ».
- Affectations individuelles et bulk atomiques, permissions OWNER/ADMIN et
  isolation inter-marchés validées.
- Migration additive `0006` auditée depuis zéro et depuis le schéma `0005`
  dans PostgreSQL de test isolé ; aucune application en production.
- Invariant Decimal : partie fixe + somme des coefficients indicés = 1.
- Import Excel/CSV complet, snapshots `StatementItem`, indices et moteur de
  révision restent hors périmètre.
- Production conservée en v0.6.1 ; aucune donnée de production modifiée.

## v0.6.1 — LOT 2A.1 Bibliothèque des modèles de formules

- Bibliothèque de modèles de formules de révision avec templates `GLOBAL`.
- Versionnement et immutabilité des versions publiées/vérifiées.
- Copie transactionnelle et indépendante vers une `MarketFormula DRAFT`.
- Lecture des templates GLOBAL réservée aux utilisateurs authentifiés avec une `Membership` active ou aux superusers ; correction de `MAJOR-001`.
- Interface LOT 2A.1 pour rechercher, prévisualiser et utiliser un modèle, avec conservation du parcours de formule personnalisée.
- Aucun moteur réglementaire définitif, `IndexDefinition`, `IndexValue`, barème, BDP ou fonctionnalité LOT 2B n'est inclus.
- `PV-REG-001` reste `PENDING_VALIDATION`.

## v0.6.0 — LOT 2A Formules contractuelles

- Groupes de révision (`RevisionGroup`) rattachés aux marchés.
- Formules contractuelles versionnées (`MarketFormula`) et termes génériques (`FormulaTerm`).
- Support des formules simples et multi-index.
- Coefficients, constantes et valeurs de base en `Decimal` / `NUMERIC(18,8)`.
- Cycle `DRAFT` / `VALIDATED` / `INACTIVE`.
- Immutabilité des versions validées et protections ORM applicatives contrôlées.
- API imbriquée et interface des formules dans le détail marché.
- Permissions OWNER/ADMIN/MEMBER, isolation par marché et validations associées.
- Tests backend/frontend, tests ORM, migrations et build validés.
- Le moteur réglementaire définitif, le calcul complet, le chargement des barèmes et le LOT 2B restent hors périmètre.
- `PV-REG-001` reste `PENDING_VALIDATION`.

## v0.5.2 — Market holder display

- Détail marché : distinction explicite entre titulaire contractuel et société gestionnaire.
- Affichage des Consortiums sous la forme `Titulaire : Groupement …`.
- Conservation de l'affichage du titulaire société pour les marchés `SOLE_COMPANY`.
- Tests frontend couvrant les deux types de titulaire et l'absence de confusion avec `Market.company`.
- Aucune migration DB et aucune modification de données métier.

## v0.5.1 — Consortium management UI

- Interface dédiée de gestion des groupements : liste, création, détail et modification.
- Réutilisation exclusive des Company existantes pour les membres et le mandataire.
- Gestion dynamique des membres et des quotes-parts avec validation 100,00 % lorsque toutes les valeurs sont renseignées.
- Navigation applicative `Sociétés | Groupements | Marchés` et routes `/app/consortia`.
- Formulaire marché : libellé `Société dossier` remplacé par `Société gestionnaire`, sans changement de relation ni de données en base.
- Aucune nouvelle migration DB ; l'architecture Consortium de v0.5.0 est réutilisée.
- Tests frontend de navigation, création INGC/NAXU, permissions d'interface et validations dynamiques.

## v0.5.0 — Consortium, authorities and company RC city

- Support des marchés dont le titulaire est un groupement.
- Consortium distinct de Company, composé de sociétés réelles.
- Membres, mandataire contractuel et contrôles d'accès applicatifs séparés.
- Quotes-parts Decimal, nullable, avec contrôle du total lorsqu'elles sont toutes renseignées.
- Maîtres d'ouvrage structurés avec historique et autocomplétion.
- Conservation du texte historique du maître d'ouvrage dans les marchés existants.
- Ville du registre de commerce distincte de la ville de l'entreprise.
- Format financier français et affichage des dates en `JJ/MM/AAAA`.
- Migrations additives avec conservation des données historiques.
- Tests de migration pré/post couvrant identité, dates, montants, TVA, objet, titulaire et maître d'ouvrage.
- Tests backend/frontend, build TypeScript/Vite et diagnostic d'exploitation validés.

## v0.4.1

- Durcissement de la persistance, de la gouvernance et de la préparation de release.
