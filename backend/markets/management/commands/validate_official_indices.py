from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from markets.official_validation import OfficialIndexValidationService


class Command(BaseCommand):
    help = "Extrait un barème officiel, compare API/local et valide explicitement (dry-run par défaut)."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, type=Path)
        parser.add_argument("--source-url", default="")
        parser.add_argument("--document-reference", default="")
        parser.add_argument("--publication-date", default="")
        parser.add_argument("--dry-run", action="store_true", help="Mode lecture seule; mode par défaut.")
        parser.add_argument("--apply", action="store_true", help="Applique sur TEST_DATABASE uniquement.")

    def handle(self, *args, **options):
        if options["dry_run"] and options["apply"]:
            raise CommandError("--dry-run et --apply sont exclusifs.")
        path = options["file"]
        if not path.exists() or path.suffix.lower() != ".pdf":
            raise CommandError("--file doit désigner un PDF existant.")
        publication_date = None
        if options["publication_date"]:
            try:
                publication_date = datetime.strptime(options["publication_date"], "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("--publication-date doit être au format YYYY-MM-DD.") from exc
        service = OfficialIndexValidationService(path, source_url=options["source_url"], document_reference=options["document_reference"], publication_date=publication_date)
        plan = service.plan()
        if plan.duplicate:
            self.stdout.write("DOCUMENT_DUPLICATE_DETECTED")
            self.stdout.write("MODE=DRY_RUN" if not options["apply"] else "MODE=APPLY_NOOP")
            return
        self.stdout.write(f"TEST_DATABASE={'YES' if __import__('os').environ.get('DJANGO_ENV', '').lower() == 'test' else 'NO (écriture refusée hors test)'}")
        self.stdout.write(f"PRODUCTION_DATABASE=NO")
        self.stdout.write(f"DOCUMENT={plan.result.filename} SHA256={plan.result.sha256} METHOD={plan.result.extractor} STATUS={plan.result.extraction_status}")
        self.stdout.write(f"NOMINAL_PERIOD={plan.nominal_year or 'UNKNOWN'}-{plan.nominal_month or 'UNKNOWN'}")
        self.stdout.write(f"PERIODS={','.join(plan.result.periods) or 'UNKNOWN'}")
        self.stdout.write(f"OFFICIAL_ROWS={len(plan.result.raw_rows)} NOMINAL_COMPARISONS={len(plan.comparisons)}")
        for key, value in sorted(plan.summary.items()):
            if value:
                self.stdout.write(f"{key}={value}")
        if not options["apply"]:
            self.stdout.write("MODE=DRY_RUN")
            return
        try:
            _, outcome = service.apply()
        except RuntimeError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(f"EVENT={outcome['event']}")
        self.stdout.write("MODE=APPLY")
