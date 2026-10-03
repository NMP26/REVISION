from django.core.management.base import BaseCommand

from markets.official_ingestion import check_official_publications


class Command(BaseCommand):
    help = "Détecte les nouveaux barèmes du portail officiel sans validation automatique."

    def handle(self, *args, **options):
        result = check_official_publications()
        self.stdout.write(f"STATUS={result['status']}")
        self.stdout.write(f"NEW_DOCUMENTS={result.get('new_documents', 0)}")
        if result.get("error"):
            self.stdout.write(f"ERROR={result['error']}")
