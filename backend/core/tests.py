from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_health_reports_database_and_migrations(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"]["status"], "ok")
        self.assertEqual(payload["migrations"]["status"], "ok")
