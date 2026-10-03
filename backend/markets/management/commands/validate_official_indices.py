from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from markets.official_ingestion import OfficialIngestionError, Provenance, ingest_official_bareme, validate_official_bareme
from markets.models import IndexSourceDocument


class Command(BaseCommand):
    help = "Importe un PDF officiel dans le pipeline partagé; validation explicite facultative."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, type=Path)
        parser.add_argument("--source-url", default="", help="URL PDF officielle; vide pour un upload manuel.")
        parser.add_argument("--apply", action="store_true", help="Valide explicitement le barème après prévisualisation.")
        parser.add_argument("--confirm-conflicts", action="store_true")

    def handle(self, *args, **options):
        path = options["file"]
        if not path.exists():
            raise CommandError("--file doit désigner un fichier existant.")
        provenance = Provenance(source_pdf_url=options["source_url"], import_method=IndexSourceDocument.ImportMethod.MANUAL)
        try:
            outcome = ingest_official_bareme(path, provenance)
            self.stdout.write(f"EVENT={outcome['event']}")
            self.stdout.write(f"DOCUMENT={outcome['preview']['filename']} SHA256={outcome['preview']['sha256']}")
            self.stdout.write(f"NOMINAL_PERIOD={outcome['preview']['year']}-{outcome['preview']['month']}")
            self.stdout.write(f"INDICES={outcome['preview']['count']} BLOCKING={outcome['preview']['blocking_issues']}")
            if options["apply"] and outcome["event"] != "DOCUMENT_ALREADY_IMPORTED":
                preview = validate_official_bareme(outcome["preview"]["document_id"], confirm_conflicts=options["confirm_conflicts"])
                self.stdout.write(f"VALIDATION_STATUS={preview['validation_status']}")
        except OfficialIngestionError as exc:
            raise CommandError(f"{exc.code}: {exc}") from exc
