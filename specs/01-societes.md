STATUS: APPROVED
SOURCE: GOV 1.1 + LOT 1A — périmètre fonctionnel validé

# Sociétés

## Éléments fonctionnels APPROVED

| ID | Obligation |
|---|---|
| SOC-001 | Créer une société avec ses champs obligatoires. |
| SOC-002 | Consulter une société pour un utilisateur autorisé. |
| SOC-003 | Modifier une société pour un utilisateur autorisé. |
| SOC-004 | Refuser les données non conformes. |
| SOC-005 | Utiliser les champs définis par le Blueprint §7. |
| SOC-006 | Persister la société dans PostgreSQL. |
| SOC-007 | Exposer la société par API. |
| SOC-008 | Respecter les sketches/specs dans l'UI. |
| SOC-009 | Fournir des tests backend. |
| SOC-010 | Fournir les tests API pertinents. |
| SOC-012 | Fournir les tests frontend pertinents. |

## Périmètre LOT 1A implémenté

L'accès utilisateur/société est porté par l'entité `Membership`, avec les
rôles `OWNER`, `ADMIN` et `MEMBER`, et un indicateur d'accès actif distinct
du statut de la société. La création d'une société crée atomiquement le
rattachement `OWNER`. Les sociétés sont exposées uniquement aux membres
actifs ; seuls `OWNER` et `ADMIN` peuvent modifier.

Les champs fonctionnels incluent la raison sociale, les informations
juridiques et financières, les coordonnées, le représentant légal, le logo
optionnel et les notes. Le capital social est décimal et les identifiants
ICE/IF/RC/CNSS ne sont pas rendus uniques sans exigence explicite.

L'archivage détaillé et les droits fins restent hors du périmètre livré.
Une société possédant des marchés ne doit pas être supprimée physiquement.

## Éléments encore DRAFT / TBD

La récupération complète du mot de passe par email reste planifiée tant
que l'infrastructure email n'est pas disponible. Les droits fins et les
évolutions d'archivage restent à spécifier ; ils ne sont pas nécessaires
pour LOT 1A. Voir plans/LOT-01.md.
