import csv
import json
from collections import Counter
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from markets.index_importer import analyse_archive, analyse_pdf
from markets.models import IndexDefinition, IndexPublication, MonthlyIndexValue


class Command(BaseCommand):
    help = "Analyse un archive de barèmes en dry-run ou importe un CSV approuvé."

    def add_arguments(self, parser):
        parser.add_argument("source", type=Path)
        parser.add_argument("--document-reference", default="")
        parser.add_argument("--source-url", default="")
        parser.add_argument("--publication-date", default="")
        parser.add_argument("--dry-run", action="store_true", help="Analyse sans aucune écriture en base.")
        parser.add_argument("--report-path", type=Path, default=None)

    def handle(self, *args, **options):
        path = options["source"]
        if not path.exists():
            raise CommandError(f"Fichier introuvable: {path}")
        if options["dry_run"]:
            self._dry_run(path, options.get("report_path"))
            return
        if path.suffix.lower() != ".csv":
            raise CommandError("L'import permanent est limité au CSV approuvé; utilisez --dry-run pour un PDF/ZIP.")
        if not options["document_reference"]:
            raise CommandError("--document-reference est obligatoire hors dry-run.")
        self._import_csv(path, options)

    def _dry_run(self, path: Path, report_path: Path | None):
        try:
            results = analyse_archive(path) if path.suffix.lower() == ".zip" else [analyse_pdf(path)]
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        rows = [row for result in results for row in result.raw_rows]
        periods = sorted({period for result in results for period in result.periods})
        valid = [row for row in rows if row.validation_status != "PENDING_VALIDATION" and row.normalized_code and row.normalized_value]
        pending = [row for row in rows if row.validation_status == "PENDING_VALIDATION"]
        errors = [error for result in results for error in result.errors]
        codes = {}
        for row in rows:
            if not row.normalized_code:
                continue
            item = codes.setdefault(row.normalized_code, {"designation": row.raw_designation, "months": set(), "values": 0, "pending": 0})
            item["months"].update(periods)
            item["values"] += 1
            item["pending"] += row.validation_status == "PENDING_VALIDATION"
        report = {"documents": [result.as_dict() for result in results], "summary": {"documents": len(results), "months": len(periods), "raw_rows": len(rows), "valid_values": len(valid), "pending": len(pending), "errors": len(errors)}, "codes": [{"code": code, "designation": item["designation"], "first_month": min(item["months"]) if item["months"] else None, "last_month": max(item["months"]) if item["months"] else None, "values": item["values"], "pending": item["pending"]} for code, item in sorted(codes.items())], "bat3": self._bat3_control(results)}
        if report_path:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write("MOIS | FICHIER | EXTRACTEUR | NB LIGNES BRUTES | NB INDICES VALIDES | NB PENDING | NB ERREURS")
        for result in results:
            valid_count = sum(row.validation_status != "PENDING_VALIDATION" for row in result.raw_rows)
            pending_count = sum(row.validation_status == "PENDING_VALIDATION" for row in result.raw_rows)
            self.stdout.write(f"{','.join(result.periods) or 'INCONNU'} | {result.filename} | {result.extractor} | {len(result.raw_rows)} | {valid_count} | {pending_count} | {len(result.errors)}")
        self.stdout.write("")
        self.stdout.write(f"TOTAL_DOCUMENTS={len(results)} TOTAL_MONTHS={len(periods)} TOTAL_RAW_ROWS={len(rows)} TOTAL_VALID_INDEX_VALUES={len(valid)} TOTAL_PENDING={len(pending)} TOTAL_ERRORS={len(errors)}")
        self.stdout.write("CODE | DESIGNATION | PREMIER MOIS | DERNIER MOIS | NB VALEURS | NB PENDING")
        for item in report["codes"]:
            self.stdout.write(f"{item['code']} | {item['designation']} | {item['first_month'] or '-'} | {item['last_month'] or '-'} | {item['values']} | {item['pending']}")
        self.stdout.write("BAT3 CONTROL | MOIS | VALEUR | STATUT | FICHIER SOURCE")
        for item in report["bat3"]:
            self.stdout.write(f"BAT3 | {item['month']} | {item['value']} | {item['status']} | {item['source']}")
        if report_path:
            self.stdout.write(f"RAPPORT_JSON={report_path}")

    @staticmethod
    def _bat3_control(results):
        controls = {}
        for result in results:
            periods = result.periods[:3]
            for row in result.raw_rows:
                if row.normalized_code != "BAT3":
                    continue
                column = int(row.source_column) - 1
                if column < len(periods) and periods[column] not in controls:
                    controls[periods[column]] = {"month": periods[column], "value": row.normalized_value or "-", "status": row.validation_status, "source": result.filename}
        return [controls[key] for key in sorted(controls)]

    @transaction.atomic
    def _import_csv(self, path, options):
        rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
        required = {"code", "designation", "domain", "year", "month", "value"}
        if not rows or not required.issubset(rows[0]):
            raise CommandError(f"Colonnes requises: {', '.join(sorted(required))}")
        first = rows[0]
        year, month = int(first["year"]), int(first["month"])
        publication_date = datetime.strptime(options["publication-date"], "%Y-%m-%d").date() if options["publication-date"] else None
        publication, _ = IndexPublication.objects.update_or_create(year=year, month=month, defaults={"document_reference": options["document_reference"], "source_url": options["source_url"], "publication_date": publication_date, "status": IndexPublication.Status.IMPORTED})
        counts, errors = Counter(), []
        for line_number, row in enumerate(rows, start=2):
            try:
                code = row["code"].strip()
                value = Decimal(row["value"].strip().replace(" ", "").replace(",", ".")) if row["value"].strip() else None
                row_year, row_month = int(row["year"]), int(row["month"])
                if row_year != year or row_month != month or not code or value is None or value <= 0:
                    raise ValueError("code, valeur ou mois invalide")
            except (KeyError, ValueError, InvalidOperation) as exc:
                errors.append(f"ligne {line_number}: {exc}")
                counts["PENDING_VALIDATION"] += 1
                continue
            definition, _ = IndexDefinition.objects.get_or_create(code=code, defaults={"designation": row["designation"].strip(), "domain": row["domain"].strip(), "active": True})
            status = row.get("status", "PENDING_VALIDATION").strip().upper() or "PENDING_VALIDATION"
            if status not in MonthlyIndexValue.Status.values:
                status = MonthlyIndexValue.Status.PENDING_VALIDATION
            existing = MonthlyIndexValue.objects.filter(index_definition=definition, year=year, month=month).first()
            if existing and existing.status == MonthlyIndexValue.Status.DEFINITIVE:
                counts[existing.status] += 1
                continue
            MonthlyIndexValue.objects.update_or_create(index_definition=definition, year=year, month=month, defaults={"publication": publication, "value": value, "status": status, "source_url": row.get("source_url", "").strip() or options["source_url"], "source_document": row.get("source_document", "").strip() or options["document_reference"], "validated_at": date.today() if status == "DEFINITIVE" else None})
            counts[status] += 1
        if errors:
            publication.status = IndexPublication.Status.PENDING_VALIDATION
            publication.save(update_fields=["status"])
        self.stdout.write(f"{year:04d}-{month:02d} | détectés={len(rows)} | importés={sum(counts.values())} | définitifs={counts['DEFINITIVE']} | provisoires={counts['PROVISIONAL']} | pending={counts['PENDING_VALIDATION']} | erreurs={len(errors)}")
