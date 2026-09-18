import json

from django.test import TestCase
from django.test import RequestFactory

from .middleware import ApiInternalErrorMiddleware


class HealthEndpointTests(TestCase):
    def test_health_reports_database_and_migrations(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"]["status"], "ok")
        self.assertEqual(payload["migrations"]["status"], "ok")


class ApiErrorTests(TestCase):
    def test_unhandled_api_error_is_uniform_and_does_not_expose_detail(self):
        def broken_view(request):
            raise RuntimeError("private database detail")

        request = RequestFactory().get("/api/broken/")
        response = ApiInternalErrorMiddleware(broken_view)(request)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(json.loads(response.content), {"code": "INTERNAL_ERROR", "message": "Une erreur interne est survenue."})
