from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_create_user_normalizes_email_and_hashes_password(self):
        user = get_user_model().objects.create_user(" User@Example.COM ", "password-123")
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("password-123"))
        self.assertNotEqual(user.password, "password-123")

    def test_create_superuser_sets_admin_flags(self):
        user = get_user_model().objects.create_superuser("admin@example.com", "password-123", first_name="A", last_name="D")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_email_is_unique(self):
        get_user_model().objects.create_user("user@example.com", "password-123", first_name="A", last_name="B")
        with self.assertRaises(Exception):
            get_user_model().objects.create_user("USER@example.com", "password-456", first_name="C", last_name="D")
