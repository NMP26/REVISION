# Changelog

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
