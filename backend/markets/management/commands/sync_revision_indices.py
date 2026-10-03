from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Mécanisme historique déprécié; la source V1 est le portail officiel du Ministère."

    def handle(self, *args, **options):
        raise CommandError("REVISIONDESPRIX_MA_DEPRECATED: utilisez check_official_publications().")
