from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.db import transaction
from django.test import TestCase
from PIL import Image
from rest_framework.test import APIClient

from .models import Company, Membership


class CompanyModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("owner@example.com", "password-123", first_name="Owner", last_name="User")
        self.company = Company.objects.create(raison_sociale="Entreprise test")

    def test_membership_roles_and_unique_pair(self):
        Membership.objects.create(user=self.user, company=self.company, role=Membership.Role.OWNER)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Membership.objects.create(user=self.user, company=self.company, role=Membership.Role.MEMBER)

    def test_company_defaults_active_and_identifiers_are_not_unique(self):
        self.assertEqual(self.company.status, Company.Status.ACTIVE)
        Company.objects.create(raison_sociale="Autre", ice="same", if_fiscal="same", rc="same", cnss="same")
        Company.objects.create(raison_sociale="Encore", ice="same", if_fiscal="same", rc="same", cnss="same")

    def test_rc_city_is_separate_and_does_not_change_existing_city(self):
        self.company.rc = "13165"
        self.company.rc_city = "Inezgane"
        self.company.ville = "Agadir"
        self.company.save()
        self.company.refresh_from_db()
        self.assertEqual(self.company.rc, "13165")
        self.assertEqual(self.company.rc_city, "Inezgane")
        self.assertEqual(self.company.ville, "Agadir")

    def test_logo_size_limit(self):
        client = APIClient(); client.force_authenticate(self.user)
        oversized = SimpleUploadedFile("logo.png", b"x" * (5 * 1024 * 1024 + 1), content_type="image/png")
        response = client.post("/api/companies/", {"raison_sociale": "Logo", "logo": oversized}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "VALIDATION_ERROR")

    def test_logo_valid_image_is_accepted(self):
        stream = BytesIO(); Image.new("RGB", (10, 10), "blue").save(stream, format="PNG"); stream.seek(0)
        client = APIClient(); client.force_authenticate(self.user)
        response = client.post("/api/companies/", {"raison_sociale": "Logo valide", "logo": SimpleUploadedFile("logo.png", stream.read(), content_type="image/png")}, format="multipart")
        self.assertEqual(response.status_code, 201)

    def test_logo_extension_and_content_are_validated(self):
        client = APIClient(); client.force_authenticate(self.user)
        extension = client.post("/api/companies/", {"raison_sociale": "Extension", "logo": SimpleUploadedFile("logo.gif", b"GIF89a", content_type="image/gif")}, format="multipart")
        content = client.post("/api/companies/", {"raison_sociale": "Contenu", "logo": SimpleUploadedFile("logo.png", b"not-an-image", content_type="image/png")}, format="multipart")
        self.assertEqual(extension.status_code, 400)
        self.assertEqual(content.status_code, 400)

    def test_logo_path_traversal_is_never_persisted(self):
        stream = BytesIO(); Image.new("RGB", (10, 10), "green").save(stream, format="PNG"); stream.seek(0)
        client = APIClient(); client.force_authenticate(self.user)
        response = client.post("/api/companies/", {"raison_sociale": "Chemin sûr", "logo": SimpleUploadedFile("../../evil.png", stream.read(), content_type="image/png")}, format="multipart")
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("..", response.data["logo"])
        self.assertIn("companies/logos/", response.data["logo"])

    def test_logo_replacement_updates_the_stored_path(self):
        client = APIClient(); client.force_authenticate(self.user)
        first = BytesIO(); Image.new("RGB", (10, 10), "red").save(first, format="PNG"); first.seek(0)
        second = BytesIO(); Image.new("RGB", (12, 12), "blue").save(second, format="PNG"); second.seek(0)
        created = client.post("/api/companies/", {"raison_sociale": "Remplacement", "logo": SimpleUploadedFile("first.png", first.read(), content_type="image/png")}, format="multipart")
        replaced = client.patch(f"/api/companies/{created.data['id']}/", {"logo": SimpleUploadedFile("second.png", second.read(), content_type="image/png")}, format="multipart")
        self.assertEqual(replaced.status_code, 200)
        self.assertNotEqual(created.data["logo"], replaced.data["logo"])

    def test_creation_is_atomic_when_membership_fails(self):
        client = APIClient(); client.force_authenticate(self.user)
        with patch("companies.views.Membership.objects.create", side_effect=RuntimeError("fail")):
            with self.assertRaises(RuntimeError):
                client.post("/api/companies/", {"raison_sociale": "Atomic"}, format="json")
        self.assertFalse(Company.objects.filter(raison_sociale="Atomic").exists())


class CompanyApiTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user("owner@example.com", "password-123", first_name="Owner", last_name="User")
        self.admin = get_user_model().objects.create_user("admin@example.com", "password-123", first_name="Admin", last_name="User")
        self.member = get_user_model().objects.create_user("member@example.com", "password-123", first_name="Member", last_name="User")
        self.other = get_user_model().objects.create_user("other@example.com", "password-123", first_name="Other", last_name="User")
        self.company = Company.objects.create(raison_sociale="Entreprise")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.admin, company=self.company, role=Membership.Role.ADMIN)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)

    def authenticated_client(self, user):
        client = APIClient(); client.force_authenticate(user); return client

    def test_anonymous_is_refused(self):
        response = APIClient().get("/api/companies/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "AUTHENTICATION_REQUIRED")

    def test_list_is_limited_to_active_memberships(self):
        response = self.authenticated_client(self.owner).get("/api/companies/")
        self.assertEqual(response.status_code, 200); self.assertEqual(len(response.data), 1)
        Membership.objects.filter(user=self.owner, company=self.company).update(active=False)
        self.assertEqual(self.authenticated_client(self.owner).get("/api/companies/").data, [])

    def test_inactive_membership_cannot_read_detail(self):
        Membership.objects.filter(user=self.member, company=self.company).update(active=False)
        response = self.authenticated_client(self.member).get(f"/api/companies/{self.company.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "NOT_FOUND")

    def test_api_exposes_only_current_membership_role(self):
        self.assertEqual(self.authenticated_client(self.owner).get(f"/api/companies/{self.company.id}/").data["current_user_role"], "OWNER")
        self.assertEqual(self.authenticated_client(self.admin).get(f"/api/companies/{self.company.id}/").data["current_user_role"], "ADMIN")
        self.assertEqual(self.authenticated_client(self.member).get(f"/api/companies/{self.company.id}/").data["current_user_role"], "MEMBER")

    def test_member_can_read_but_cannot_update(self):
        self.assertEqual(self.authenticated_client(self.member).get(f"/api/companies/{self.company.id}/").status_code, 200)
        response = self.authenticated_client(self.member).patch(f"/api/companies/{self.company.id}/", {"ville": "Rabat"}, format="json")
        self.assertEqual(response.status_code, 403); self.assertEqual(response.data["code"], "PERMISSION_DENIED")

    def test_admin_and_owner_can_update(self):
        self.assertEqual(self.authenticated_client(self.admin).patch(f"/api/companies/{self.company.id}/", {"ville": "Rabat"}, format="json").status_code, 200)
        self.assertEqual(self.authenticated_client(self.owner).put(f"/api/companies/{self.company.id}/", {"raison_sociale": "Entreprise modifiée"}, format="json").status_code, 200)

    def test_user_without_membership_gets_not_found(self):
        response = self.authenticated_client(self.other).get(f"/api/companies/{self.company.id}/")
        self.assertEqual(response.status_code, 404); self.assertEqual(response.data["code"], "NOT_FOUND")

    def test_delete_is_not_exposed(self):
        response = self.authenticated_client(self.owner).delete(f"/api/companies/{self.company.id}/")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.data["code"], "REQUEST_ERROR")

    def test_forbidden_response_is_uniform(self):
        response = self.authenticated_client(self.member).patch(f"/api/companies/{self.company.id}/", {"ville": "Rabat"}, format="json")
        self.assertEqual(set(response.data), {"code", "message"})

    def test_create_assigns_owner(self):
        response = self.authenticated_client(self.other).post("/api/companies/", {"raison_sociale": "Nouvelle"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Membership.objects.get(company_id=response.data["id"]).role, Membership.Role.OWNER)
