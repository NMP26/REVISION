from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .models import CompanyAuthority, ContractingAuthority


class AuthorityApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("authority@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="NAXU")
        Membership.objects.create(user=self.user, company=self.company, role=Membership.Role.OWNER)
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_create_and_autocomplete_is_scoped_to_company_membership(self):
        response = self.client.post("/api/authorities/", {"name": "Société Régionale Multiservices Souss-Massa", "short_name": "SRM-SM", "company": str(self.company.id)}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/authorities/?q=Société Rég").data[0]["short_name"], "SRM-SM")
        self.assertEqual(CompanyAuthority.objects.count(), 1)
    def test_duplicate_official_name_is_rejected_without_merge(self):
        ContractingAuthority.objects.create(name="SRM-SM")
        response = self.client.post("/api/authorities/", {"name": "  srm-sm  ", "company": str(self.company.id)}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ContractingAuthority.objects.count(), 1)
