from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Mécanisme tiers déprécié; les valeurs V1 proviennent uniquement du pipeline officiel PDF."

    def handle(self, *args, **options):
        raise CommandError("REVISIONDESPRIX_MA_DEPRECATED: aucune promotion de données tierces n'est autorisée en V1.")
