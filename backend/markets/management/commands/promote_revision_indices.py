from django.core.management.base import BaseCommand, CommandError

from markets.promotion import IndexPromotionService


class Command(BaseCommand):
    help = "Prépare ou promeut explicitement les indices staging vers le référentiel local."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Mode lecture seule; c'est le mode par défaut.")
        parser.add_argument("--apply", action="store_true", help="Autorise les écritures dans la base courante.")
        parser.add_argument("--year", type=int)
        parser.add_argument("--code")

    def handle(self, *args, **options):
        if options["dry_run"] and options["apply"]:
            raise CommandError("--dry-run et --apply sont exclusifs.")
        service = IndexPromotionService(year=options.get("year"), code=options.get("code"))
        plan = service.plan()
        counts = plan.summary
        self.stdout.write(f"INDEX_DEFINITIONS_TO_CREATE={counts['index_definitions_to_create']}")
        self.stdout.write(f"VALUES_TO_CREATE={counts['values_to_create']}")
        self.stdout.write(f"VALUES_ALREADY_IDENTICAL={counts['values_already_identical']}")
        self.stdout.write(f"CONFLICTS={counts['conflicts']}")
        self.stdout.write(f"REJECTED={counts['rejected']}")
        self.stdout.write(f"PENDING_VALIDATION={counts['pending_validation']}")
        self.stdout.write(f"MODE={'APPLY' if options['apply'] else 'DRY_RUN'}")
        for item in plan.conflicts:
            self.stdout.write(f"CONFLICT | {item['code']} | {item['year']:04d}-{item['month']:02d} | external={item['external_value']} | local={item['local_value']}")
        if not options["apply"]:
            return
        _, applied = service.apply()
        self.stdout.write(f"INDEX_DEFINITIONS_CREATED={applied['index_definitions_created']}")
        self.stdout.write(f"MONTHLY_VALUES_CREATED={applied['monthly_values_created']}")
