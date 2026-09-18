from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from rest_framework.test import APIClient


class AuthenticationApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("user@example.com", "password-123", first_name="Test", last_name="User")
        self.client = APIClient()

    def test_login_me_logout(self):
        response = self.client.post("/api/auth/login/", {"email": " USER@EXAMPLE.COM ", "password": "password-123"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["email"], "user@example.com")
        self.assertNotIn("password", response.data)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertEqual(self.client.post("/api/auth/logout/").status_code, 204)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_invalid_login_is_generic(self):
        response = self.client.post("/api/auth/login/", {"email": "missing@example.com", "password": "wrong"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data, {"code": "INVALID_CREDENTIALS", "message": "Identifiants invalides."})

    def test_password_change_requires_current_password(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/auth/password/change/", {"current_password": "wrong", "new_password": "new-password"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/auth/password/change/", {"current_password": "password-123", "new_password": "new-password"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password"))

    def test_csrf_endpoint_returns_token(self):
        response = self.client.get("/api/auth/csrf/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["csrfToken"])

    def test_csrf_is_required_for_authenticated_mutation(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post("/api/auth/password/change/", {"current_password": "password-123", "new_password": "new-password"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"code": "CSRF_FAILED", "message": "La vérification CSRF a échoué."})

    @override_settings(AXES_FAILURE_LIMIT=2)
    def test_repeated_login_failures_are_limited(self):
        for _ in range(2):
            response = self.client.post("/api/auth/login/", {"email": self.user.email, "password": "wrong"}, format="json")
            self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/auth/login/", {"email": self.user.email, "password": "password-123"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "INVALID_CREDENTIALS")
