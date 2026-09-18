# Constitution permanente des agents IA — RevisionPrix

Ces règles s'appliquent à toute intervention sur ce dépôt.

1. Lire `BLUEPRINT.md` avant tout développement métier.
2. Lire `DECISIONS.md`.
3. Lire `ROADMAP.md`.
4. Lire `TRACEABILITY.md`.
5. Lire les specs concernées.
6. Lire le plan du LOT autorisé.
7. Ne travailler que sur le LOT explicitement autorisé.
8. Ne jamais inventer une règle métier.
9. Ne jamais inventer une règle réglementaire.
10. Signaler toute contradiction entre code, spec et Blueprint.
11. Ne jamais supprimer une exigence pour simplifier.
12. Toute exigence implémentée doit être traçable vers le code et les tests.
13. Toute nouvelle règle métier doit avoir des tests.
14. Les calculs financiers utilisent `Decimal` exclusivement.
15. Aucune valeur d'indice ne doit être inventée.
16. Aucun indice absent ne doit être remplacé silencieusement.
17. Une révision validée doit être historiquement reproductible.
18. Les snapshots validés seront immuables.
19. Aucun secret dans Git.
20. PostgreSQL ne doit jamais être exposé publiquement.
21. Ne jamais commencer le LOT suivant sans autorisation explicite.
22. Avant livraison : tests, contrôles et `make doctor`.
23. Mettre à jour `TRACEABILITY.md` avec l'implémentation.
24. Toute modification architecturale importante doit être enregistrée dans `DECISIONS.md`.
25. En cas d'ambiguïté réglementaire, documenter dans `regulatory/PENDING_VALIDATION.md` et ne pas inventer.

Le LOT 1 et les lots suivants restent interdits tant qu'une autorisation
explicite n'est pas enregistrée dans la gouvernance du projet.
