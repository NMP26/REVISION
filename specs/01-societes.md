STATUS: DRAFT
SOURCE: GOV 1.1 — fonctionnel partiellement approuvé

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

Le rattachement utilisateur/société, l'archivage détaillé et les droits
fins restent à préciser dans une décision ou une spec dédiée si
nécessaire. Une société possédant des marchés ne doit pas être supprimée
physiquement.

## Éléments DRAFT / TBD

L'architecture d'authentification, les sessions/tokens, la récupération
de mot de passe et les permissions détaillées restent TBD. Voir AUTH-001
à AUTH-004 et plans/LOT-01.md. Ce fichier reste DRAFT tant que la spec
complète et la décision d'architecture ne sont pas validées.
