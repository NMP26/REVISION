# Backup et restauration

`make backup` crée un répertoire horodaté dans `backups/` avec un dump
`pg_dump` au format custom, les migrations, les métadonnées de version et
les sommes SHA-256.

La restauration est bloquée par défaut dans le LOT 0 et doit faire l'objet
d'une procédure approuvée avec contrôle d'impact.
