# Changelog

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
