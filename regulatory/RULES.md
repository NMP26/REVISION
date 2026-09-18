STATUS: APPROVED
SOURCE: REG V1 — noyau réglementaire vérifié
DATE DE VERIFICATION: 2026-09-18

# Règles réglementaires

## Statut du registre

- VERIFIED = 16.
- PENDING_VALIDATION contient uniquement les sous-points non établis par les sources intégrées.
- Une règle VERIFIED n'est activable dans le code qu'après conception, implémentation, migration éventuelle et tests tracés.

## Règles VERIFIED

| ID | Source / article | Règle résumée | Portée / impact fonctionnel | Exigences liées | Futurs tests | Statut |
|---|---|---|---|---|---|---|
| REG-001 | SRC-REG-001, art. 3, 4, 9 | Le CPS peut prévoir une ou plusieurs formules et associe chaque prestation à sa formule. | Market 1..N MarketFormula ; association PriceItem/RevisionGroup. | MKT-001, MKT-002, FRM-001, BDP-010 | mono-formule ; multi-formules ; affectation prestation | VERIFIED |
| REG-002 | SRC-REG-001, art. 4 | Forme générale P=P0[k+a(X/X0)+b(Y/Y0)+…] ; P/P0 HT ; k≥0,15 ; somme des coefficients=1. | FormulaTerm/IndexDefinition multiples ; moteur générique, jamais BAT3 hardcodé. | FRM-002, FRM-003, REV-006 | formule mono/multi-index ; contraintes k/somme | VERIFIED |
| REG-003 | SRC-REG-001, art. 4, 7 | Référence : mois de la date limite de remise des offres en appel à concurrence ; mois de signature par l'attributaire en négocié. | Date et règle de référence explicites, pas seulement date d'ouverture. | MKT-006, MKT-007, MKT-012 | chaque procédure ; mois de référence | VERIFIED |
| REG-004 | SRC-REG-001, art. 5 | Coefficients et nature des index viennent des cahiers applicables ; formule stockée par marché. | Pas de déduction automatique depuis objet/catégorie. | MKT-004, FRM-002 | formule contractuelle persistée | VERIFIED |
| REG-005 | SRC-REG-001, art. 6 | Pour un marché révisable ≤ 1 000 000 DH, maximum cinq index. | Règle paramétrable et testable, sans implémentation dans REG V1. | FRM-002 | seuil et sixième index | VERIFIED |
| REG-006 | SRC-REG-001, art. 7 | La forme globale P=P0[k+a(I/I0)] est un cas du moteur générique, k+a=1. | Pas de moteur séparé. | FRM-002, FRM-003 | calcul global ; contrainte somme | VERIFIED |
| REG-007 | SRC-REG-001, art. 8 | Coefficient final et rapports intermédiaires à la quatrième décimale. | Decimal et service centralisé ; mode exact d'arrondi non déterminé. | REV-006, HIS-007 | précision à quatre décimales | VERIFIED |
| REG-008 | SRC-REG-001, art. 9 | Application automatique aux prestations à exécuter, sans demande spéciale ni avenant spécifique. | Déclenchement métier futur. | REV-008 | application automatique | VERIFIED |
| REG-009 | SRC-REG-001, art. 10 | Valeurs des index publiées mensuellement par le ministre chargé de l'équipement. | IndexDefinition/IndexValue avec mois, valeur, publication, source, statut. | IDX-001, IDX-002, IDX-003 | publication et provenance | VERIFIED |
| REG-010 | SRC-REG-001, art. 12 ; SRC-REG-002 | Décompte provisoire ordinaire : valeurs définitives ; si non publiées, paiement sans révision puis régularisation au décompte provisoire suivant. | États PENDING_INDEX/PENDING_REVISION ou équivalent ; aucune valeur inventée. | IDX-004, DEC-005 | définitif absent ; régularisation suivante | VERIFIED |
| REG-011 | SRC-REG-001, art. 12 ; SRC-REG-002 | Dernier décompte provisoire : valeurs publiées disponibles à la date d'établissement. | Statement identifie explicitement le dernier décompte provisoire. | DEC-002, IDX-004 | dernier décompte et valeurs publiées | VERIFIED |
| REG-012 | SRC-REG-001, art. 13 | Chaque révision d'un décompte provisoire est accompagnée d'une note justificative. | PDF/DOCX conserve la justification complète. | DOC-001..DOC-007, REV-007 | note cohérente avec le calcul | VERIFIED |
| REG-013 | SRC-REG-001, art. 14 | Sur plusieurs mois, exécution réelle prioritaire ; prorata jours calendaires en repli. | Confirme ACTUAL_EXECUTION et CALENDAR_DAY_PRORATA. | VEN-001..VEN-005 | priorité et repli justifié | VERIFIED |
| REG-014 | SRC-REG-001, art. 15 | Décompte définitif : total de révision et état récapitulatif. | Sortie définitive explicite. | DEC-007, DOC-004, DOC-007 | total et état récapitulatif | VERIFIED |
| REG-015 | SRC-REG-001, art. 16 | Approvisionnement et mise en œuvre peuvent avoir prix/formules distincts ; date effective d'approvisionnement prise en compte. | Préserver la capacité modèle ; UI non obligatoire au LOT 1. | BDP-017, BDP-018 | prix/formules distincts ; date effective | VERIFIED |
| REG-016 | SRC-REG-001, art. 18 | Si retard imputable : comparer coefficient du mois réel et du dernier mois contractuel, retenir le plus faible. | Imputabilité obligatoirement fournie/validée explicitement, jamais déduite seule. | OS-002, REV-009 | imputabilité absente ; min(A,B) | VERIFIED |

## Règles non juridiques

L'immutabilité et les snapshots restent une décision d'architecture
nécessaire à l'audit et à la reproductibilité ; ils ne sont pas déclarés
comme règle juridique REG VERIFIED. Voir ADR-GOV-010 et HIS-001..HIS-008.
