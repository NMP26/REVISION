from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from markets.revisiondesprix_client import RevisionDesPrixApiClient, RevisionDesPrixApiError
from markets.staging import YEARS_AUDITED, compare_evolution, stage_catalogue, stage_year


class Command(BaseCommand):
    help = "Synchronise revisiondesprix.ma vers le staging uniquement; aucune promotion locale."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Analyse sans écrire le staging.")
        parser.add_argument("--year", type=int, choices=YEARS_AUDITED)
        parser.add_argument("--code")
        parser.add_argument("--all-years", action="store_true", help="Synchronise toutes les années auditées.")
        parser.add_argument("--base-url", default=RevisionDesPrixApiClient.DEFAULT_BASE_URL)

    def handle(self, *args, **options):
        if options["year"] and options["all_years"]:
            raise CommandError("--year et --all-years sont exclusifs.")
        years = [options["year"]] if options["year"] else list(YEARS_AUDITED)
        client = RevisionDesPrixApiClient(base_url=options["base_url"])
        retrieved_at = timezone.now()
        try:
            catalogue = stage_catalogue(client, dry_run=options["dry_run"], retrieved_at=retrieved_at)
            totals = Counter()
            for year in years:
                counts = stage_year(client, year, code=options["code"], dry_run=options["dry_run"], retrieved_at=retrieved_at)
                totals.update(counts)
                self.stdout.write(self._year_line(year, counts))
            self.stdout.write("CATALOGUE | codes=%s matched=%s missing_local=%s local_only=%s" % (catalogue["total"], catalogue["matched"], catalogue["missing_local"], len(catalogue["local_only"])))
            self.stdout.write(self._total_line(totals))
            if catalogue["local_only"]:
                self.stdout.write("LOCAL_ONLY_CODES=" + ",".join(catalogue["local_only"]))
            self._evolution_report(client, years, options["code"])
            self.stdout.write("MODE=" + ("DRY_RUN" if options["dry_run"] else "STAGING_ONLY"))
            self.stdout.write("MONTHLY_INDEX_VALUE_WRITES=0")
        except RevisionDesPrixApiError as exc:
            raise CommandError(f"{exc.kind}: {exc} endpoint={exc.endpoint}") from exc

    def _evolution_report(self, client, years, code):
        codes = [code] if code else ["BAT3", "BAT6"]
        for item_code in codes:
            values = []
            for year in years:
                values.extend(client.get_indices_for_year(year))
            comparison = compare_evolution(client, year_values=values, code=item_code)
            counts = Counter(item["status"] for item in comparison)
            self.stdout.write("EVOLUTION %s | %s" % (item_code, " ".join(f"{key}={value}" for key, value in sorted(counts.items()))))

    @staticmethod
    def _year_line(year, counts):
        return "YEAR %s | API_VALUES=%s NORMALIZED=%s MATCHED=%s CONFLICT=%s MISSING_LOCAL=%s INVALID=%s PENDING=%s" % (year, counts["values"], counts["normalized"], counts["matched"], counts["conflict"], counts["missing_local"], counts["invalid"], counts["pending"])

    @staticmethod
    def _total_line(counts):
        return "TOTAL | API_VALUES=%s NORMALIZED=%s MATCHED=%s CONFLICT=%s MISSING_LOCAL=%s INVALID=%s PENDING=%s" % (counts["values"], counts["normalized"], counts["matched"], counts["conflict"], counts["missing_local"], counts["invalid"], counts["pending"])
