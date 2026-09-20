from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import DatabaseError, transaction
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .models import Consortium, ConsortiumMember


class ConsortiumTests(TransactionTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("naxu@example.com", "password-123")
        self.naxu = Company.objects.create(raison_sociale="NAXU")
        self.ingc = Company.objects.create(raison_sociale="INGC")
        Membership.objects.create(user=self.user, company=self.naxu, role=Membership.Role.OWNER)
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def payload(self, shares=("50.00", "50.00")):
        return {"owner_company": str(self.naxu.id), "name": "Groupement INGC/NAXU", "members": [
            {"company": str(self.ingc.id), "role": "MANDATAIRE", "share_percent": shares[0], "sort_order": 0, "active": True},
            {"company": str(self.naxu.id), "role": "MEMBER", "share_percent": shares[1], "sort_order": 1, "active": True},
        ]}

    def test_real_companies_and_nullable_decimal_shares(self):
        response = self.client.post("/api/consortia/", self.payload(), format="json")
        self.assertEqual(response.status_code, 201)
        consortium = Consortium.objects.get(pk=response.data["id"])
        self.assertEqual(consortium.members.count(), 2)
        self.assertEqual(consortium.members.get(company=self.ingc).share_percent, Decimal("50.0000"))
        self.assertFalse(Company.objects.filter(raison_sociale="Groupement INGC/NAXU").exists())

    def test_all_shares_must_total_exactly_one_hundred(self):
        response = self.client.post("/api/consortia/", self.payload(("40", "50")), format="json")
        self.assertEqual(response.status_code, 400)

    def test_share_sum_rules_use_decimal_without_float(self):
        for index, shares in enumerate((("50", "50"), ("40", "60"), ("33.33", "66.67"), ("50", None), (None, None))):
            with self.subTest(shares=shares):
                response = self.client.post("/api/consortia/", {**self.payload(shares), "name": f"Groupement {index}"}, format="json")
                self.assertEqual(response.status_code, 201)

    def test_invalid_share_bounds_are_rejected(self):
        for index, shares in enumerate((("50", "40"), ("50", "60"), ("0", "100"), ("-1", "101"), ("100.0001", "0.1"))):
            with self.subTest(shares=shares):
                response = self.client.post("/api/consortia/", {**self.payload(shares), "name": f"Invalid {index}"}, format="json")
                self.assertEqual(response.status_code, 400)

    def test_one_active_mandataire_is_required(self):
        payload = self.payload(); payload["members"][1]["role"] = "MANDATAIRE"
        response = self.client.post("/api/consortia/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_owner_company_is_immutable_on_patch_and_put(self):
        created = self.client.post("/api/consortia/", self.payload(), format="json")
        self.assertEqual(created.status_code, 201)
        replacement = Company.objects.create(raison_sociale="Autre société")
        consortium_id = created.data["id"]
        patch_response = self.client.patch(f"/api/consortia/{consortium_id}/", {"owner_company": str(replacement.id)}, format="json")
        self.assertEqual(patch_response.status_code, 400)
        put_response = self.client.put(f"/api/consortia/{consortium_id}/", {**self.payload(), "owner_company": str(replacement.id)}, format="json")
        self.assertEqual(put_response.status_code, 400)
        self.assertEqual(Consortium.objects.get(pk=consortium_id).owner_company_id, self.naxu.id)

    def test_database_trigger_rejects_two_active_mandataires(self):
        with self.assertRaises(DatabaseError):
            with transaction.atomic():
                consortium = Consortium.objects.create(owner_company=self.naxu, created_by=self.user, name="Invalid direct ORM")
                ConsortiumMember.objects.create(consortium=consortium, company=self.ingc, role=ConsortiumMember.Role.MANDATAIRE, share_percent=Decimal("50"))
                ConsortiumMember.objects.create(consortium=consortium, company=self.naxu, role=ConsortiumMember.Role.MANDATAIRE, share_percent=Decimal("50"))
