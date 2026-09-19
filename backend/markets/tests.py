from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership

from .models import Market, MarketLot


class MarketApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("owner@example.com", "password-123", first_name="Owner", last_name="User")
        self.admin = user_model.objects.create_user("admin@example.com", "password-123", first_name="Admin", last_name="User")
        self.member = user_model.objects.create_user("member@example.com", "password-123", first_name="Member", last_name="User")
        self.other = user_model.objects.create_user("other@example.com", "password-123", first_name="Other", last_name="User")
        self.company = Company.objects.create(raison_sociale="Entreprise A")
        self.other_company = Company.objects.create(raison_sociale="Entreprise B")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.admin, company=self.company, role=Membership.Role.ADMIN)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        self.market = Market.objects.create(
            company=self.company,
            market_number="M-001",
            contracting_authority="Commune A",
            subject="Travaux test",
            amount_ht=Decimal("100.00"),
            vat_rate=Decimal("20.00"),
            formula_structure=Market.FormulaStructure.SINGLE,
        )

    def authenticated(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def valid_payload(self, **extra):
        payload = {
            "company": str(self.company.id),
            "market_number": "M-NEW",
            "contracting_authority": "Commune A",
            "subject": "Nouveau marché",
            "amount_ht": "1234.50",
            "vat_rate": "20.00",
            "formula_structure": "MULTIPLE",
        }
        payload.update(extra)
        return payload

    def test_create_returns_decimal_values_and_defaults_active(self):
        response = self.authenticated(self.owner).post("/api/markets/", self.valid_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["amount_ht"], "1234.50")
        self.assertEqual(response.data["vat_rate"], "20.0000")
        self.assertEqual(response.data["status"], "ACTIVE")

    def test_amount_and_vat_boundaries_are_validated(self):
        for field, value in [("amount_ht", "-1"), ("vat_rate", "-0.01"), ("vat_rate", "100.01")]:
            response = self.authenticated(self.owner).post("/api/markets/", self.valid_payload(**{field: value}), format="json")
            self.assertEqual(response.status_code, 400)
            self.assertIn(field, response.data["fields"])

    def test_required_market_text_fields_reject_empty_and_whitespace(self):
        for field in ("market_number", "contracting_authority", "subject"):
            for value in ("", "   "):
                payload = self.valid_payload(market_number=f"M-TEXT-{field}-{len(value)}")
                payload[field] = value
                response = self.authenticated(self.owner).post(
                    "/api/markets/",
                    payload,
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["fields"])

    def test_decimal_round_trip_including_maximum_amount(self):
        maximum = "9999999999999999.99"
        for market_number, amount, vat_rate in [
            ("M-DECIMAL-01", "0.01", "20.50"),
            ("M-DECIMAL-MAX", maximum, "20.50"),
        ]:
            response = self.authenticated(self.owner).post(
                "/api/markets/",
                self.valid_payload(market_number=market_number, amount_ht=amount, vat_rate=vat_rate),
                format="json",
            )
            self.assertEqual(response.status_code, 201)
            market = Market.objects.get(id=response.data["id"])
            self.assertEqual(market.amount_ht, Decimal(amount))
            self.assertEqual(market.vat_rate, Decimal(vat_rate))
            self.assertEqual(Decimal(response.data["amount_ht"]), Decimal(amount))
            self.assertEqual(Decimal(response.data["vat_rate"]), Decimal(vat_rate))

    def test_database_constraints_reject_invalid_market_values(self):
        def create_market(**overrides):
            values = {
                "company": self.company,
                "market_number": "M-DIRECT",
                "contracting_authority": "Commune A",
                "subject": "Travaux",
                "formula_structure": Market.FormulaStructure.SINGLE,
            }
            values.update(overrides)
            Market.objects.create(**values)

        invalid_values = [
            {"contract_duration_value": 0, "contract_duration_unit": "DAYS"},
            {"contract_duration_value": -1, "contract_duration_unit": "DAYS"},
            {"contract_duration_value": 1, "contract_duration_unit": "YEARS"},
            {"contract_duration_value": 1},
            {"contract_duration_unit": "DAYS"},
            {"amount_ht": Decimal("-0.01")},
            {"vat_rate": Decimal("-0.01")},
            {"vat_rate": Decimal("100.01")},
            {"market_number": ""},
            {"market_number": "   "},
            {"contracting_authority": ""},
            {"contracting_authority": "   "},
            {"subject": ""},
            {"subject": "   "},
        ]
        for index, overrides in enumerate(invalid_values):
            overrides.setdefault("market_number", f"M-DIRECT-{index}")
            with self.subTest(overrides=overrides):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        create_market(**overrides)

    def test_dates_are_nullable(self):
        response = self.authenticated(self.owner).post("/api/markets/", self.valid_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["date_ouverture_plis"])
        self.assertIsNone(response.data["date_limite_remise_offres"])
        self.assertIsNone(response.data["date_signature"])
        self.assertIsNone(response.data["date_os_commencement"])

    def test_duration_requires_pair_and_positive_value(self):
        for payload in [
            {"contract_duration_value": 10},
            {"contract_duration_unit": "DAYS"},
            {"contract_duration_value": 0, "contract_duration_unit": "DAYS"},
            {"contract_duration_value": -1, "contract_duration_unit": "MONTHS"},
        ]:
            response = self.authenticated(self.owner).post("/api/markets/", self.valid_payload(**payload), format="json")
            self.assertEqual(response.status_code, 400)
        for unit in ("DAYS", "MONTHS"):
            response = self.authenticated(self.owner).post(
                "/api/markets/", self.valid_payload(market_number=f"M-{unit}", contract_duration_value=12, contract_duration_unit=unit), format="json"
            )
            self.assertEqual(response.status_code, 201)

    def test_formula_structure_and_archived_status(self):
        response = self.authenticated(self.owner).post(
            "/api/markets/", self.valid_payload(formula_structure="SINGLE", status="ARCHIVED"), format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["formula_structure"], "SINGLE")
        self.assertEqual(response.data["status"], "ARCHIVED")

    def test_number_unique_per_company_but_reusable_in_other_company(self):
        duplicate = self.authenticated(self.owner).post("/api/markets/", self.valid_payload(market_number="M-001"), format="json")
        self.assertEqual(duplicate.status_code, 400)
        Membership.objects.create(user=self.owner, company=self.other_company, role=Membership.Role.OWNER)
        other = self.authenticated(self.owner).post(
            "/api/markets/", self.valid_payload(company=str(self.other_company.id), market_number="M-001"), format="json"
        )
        self.assertEqual(other.status_code, 201)

    def test_owner_admin_can_create_and_update_member_can_read_only(self):
        self.assertEqual(self.authenticated(self.owner).get("/api/markets/").status_code, 200)
        self.assertEqual(self.authenticated(self.admin).post("/api/markets/", self.valid_payload(market_number="M-ADMIN"), format="json").status_code, 201)
        self.assertEqual(self.authenticated(self.member).get(f"/api/markets/{self.market.id}/").status_code, 200)
        self.assertEqual(self.authenticated(self.member).post("/api/markets/", self.valid_payload(market_number="M-MEMBER"), format="json").status_code, 404)
        response = self.authenticated(self.member).patch(f"/api/markets/{self.market.id}/", {"subject": "Interdit"}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.authenticated(self.admin).patch(f"/api/markets/{self.market.id}/", {"subject": "Modifié"}, format="json").status_code, 200)

    def test_inactive_or_missing_membership_cannot_read_or_create(self):
        Membership.objects.filter(user=self.member, company=self.company).update(active=False)
        self.assertEqual(self.authenticated(self.member).get("/api/markets/").data, [])
        self.assertEqual(self.authenticated(self.member).get(f"/api/markets/{self.market.id}/").status_code, 404)
        self.assertEqual(self.authenticated(self.other).get("/api/markets/").data, [])
        self.assertEqual(self.authenticated(self.other).get(f"/api/markets/{self.market.id}/").status_code, 404)

    def test_company_is_immutable_on_update(self):
        Membership.objects.create(user=self.owner, company=self.other_company, role=Membership.Role.OWNER)
        response = self.authenticated(self.owner).patch(
            f"/api/markets/{self.market.id}/", {"company": str(self.other_company.id)}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.market.refresh_from_db()
        self.assertEqual(self.market.company_id, self.company.id)

    def test_company_isolation_by_id_and_list(self):
        Membership.objects.create(user=self.other, company=self.other_company, role=Membership.Role.OWNER)
        response = self.authenticated(self.other).get(f"/api/markets/{self.market.id}/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.authenticated(self.other).get("/api/markets/").data, [])

    def test_delete_is_not_exposed(self):
        response = self.authenticated(self.owner).delete(f"/api/markets/{self.market.id}/")
        self.assertEqual(response.status_code, 405)


class MarketLotApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("owner@example.com", "password-123", first_name="Owner", last_name="User")
        self.member = user_model.objects.create_user("member@example.com", "password-123", first_name="Member", last_name="User")
        self.other = user_model.objects.create_user("other@example.com", "password-123", first_name="Other", last_name="User")
        self.company = Company.objects.create(raison_sociale="Entreprise A")
        self.other_company = Company.objects.create(raison_sociale="Entreprise B")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        Membership.objects.create(user=self.other, company=self.other_company, role=Membership.Role.OWNER)
        self.market = Market.objects.create(
            company=self.company, market_number="M-001", contracting_authority="Commune A", subject="Travaux",
            formula_structure=Market.FormulaStructure.MULTIPLE,
        )
        self.other_market = Market.objects.create(
            company=self.other_company, market_number="M-001", contracting_authority="Commune B", subject="Autres travaux",
            formula_structure=Market.FormulaStructure.SINGLE,
        )

    def authenticated(self, user):
        client = APIClient(); client.force_authenticate(user); return client

    def payload(self, **extra):
        payload = {"lot_number": "1", "title": "Lot principal", "amount_ht": "10.00", "display_order": 0}
        payload.update(extra)
        return payload

    def test_create_read_update_and_order(self):
        client = self.authenticated(self.owner)
        first = client.post(f"/api/markets/{self.market.id}/lots/", self.payload(display_order=2), format="json")
        second = client.post(f"/api/markets/{self.market.id}/lots/", self.payload(lot_number="0", display_order=1), format="json")
        self.assertEqual(first.status_code, 201); self.assertEqual(second.status_code, 201)
        listed = client.get(f"/api/markets/{self.market.id}/lots/")
        self.assertEqual([lot["lot_number"] for lot in listed.data], ["0", "1"])
        updated = client.patch(f"/api/markets/{self.market.id}/lots/{first.data['id']}/", {"title": "Modifié"}, format="json")
        self.assertEqual(updated.status_code, 200)

    def test_amount_nullable_and_negative_rejected(self):
        client = self.authenticated(self.owner)
        self.assertEqual(client.post(f"/api/markets/{self.market.id}/lots/", self.payload(lot_number="null", amount_ht=None), format="json").status_code, 201)
        response = client.post(f"/api/markets/{self.market.id}/lots/", self.payload(lot_number="negative", amount_ht="-1"), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("amount_ht", response.data["fields"])

    def test_required_lot_text_fields_reject_empty_and_whitespace(self):
        client = self.authenticated(self.owner)
        for field in ("lot_number", "title"):
            for value in ("", "   "):
                response = client.post(
                    f"/api/markets/{self.market.id}/lots/",
                    self.payload(**{field: value}),
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.data["fields"])

    def test_unique_within_market_and_reusable_in_other_market(self):
        client = self.authenticated(self.owner)
        self.assertEqual(client.post(f"/api/markets/{self.market.id}/lots/", self.payload(), format="json").status_code, 201)
        duplicate = client.post(f"/api/markets/{self.market.id}/lots/", self.payload(), format="json")
        self.assertEqual(duplicate.status_code, 400)
        other = self.authenticated(self.other)
        self.assertEqual(other.post(f"/api/markets/{self.other_market.id}/lots/", self.payload(), format="json").status_code, 201)

    def test_member_reads_but_cannot_create_or_update(self):
        lot = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/lots/", self.payload(), format="json").data
        member = self.authenticated(self.member)
        self.assertEqual(member.get(f"/api/markets/{self.market.id}/lots/").status_code, 200)
        self.assertEqual(member.post(f"/api/markets/{self.market.id}/lots/", self.payload(lot_number="2"), format="json").status_code, 403)
        self.assertEqual(member.patch(f"/api/markets/{self.market.id}/lots/{lot['id']}/", {"title": "Interdit"}, format="json").status_code, 403)

    def test_nested_url_cannot_access_lot_from_other_market(self):
        lot = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/lots/", self.payload(), format="json").data
        response = self.authenticated(self.owner).get(f"/api/markets/{self.other_market.id}/lots/{lot['id']}/")
        self.assertEqual(response.status_code, 404)

    def test_nested_url_rejects_lot_from_other_accessible_market_on_read_and_patch(self):
        Membership.objects.create(user=self.owner, company=self.other_company, role=Membership.Role.OWNER)
        lot = self.authenticated(self.other).post(
            f"/api/markets/{self.other_market.id}/lots/", self.payload(), format="json"
        ).data
        nested_url = f"/api/markets/{self.market.id}/lots/{lot['id']}/"
        self.assertEqual(self.authenticated(self.owner).get(nested_url).status_code, 404)
        self.assertEqual(self.authenticated(self.owner).patch(nested_url, {"title": "Interdit"}, format="json").status_code, 404)

    def test_database_constraints_reject_invalid_lot_values(self):
        def create_lot(**overrides):
            values = {"market": self.market, "lot_number": "1", "title": "Lot principal"}
            values.update(overrides)
            MarketLot.objects.create(**values)

        invalid_values = [
            {"amount_ht": Decimal("-0.01")},
            {"display_order": -1},
            {"lot_number": ""},
            {"lot_number": "   "},
            {"title": ""},
            {"title": "   "},
        ]
        for index, overrides in enumerate(invalid_values):
            overrides.setdefault("lot_number", f"DIRECT-{index}")
            with self.subTest(overrides=overrides):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        create_lot(**overrides)

    def test_delete_is_not_exposed(self):
        response = self.authenticated(self.owner).delete(f"/api/markets/{self.market.id}/lots/00000000-0000-0000-0000-000000000000/")
        self.assertEqual(response.status_code, 405)
