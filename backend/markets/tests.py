from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from companies.models import Company, Membership
from consortia.models import Consortium, ConsortiumMember

from .models import FormulaTemplate, FormulaTemplateTerm, FormulaTerm, IndexDefinition, IndexPublication, Market, MarketFormula, MarketLot, MonthlyIndexValue, PriceItem, PriceSchedule, RevisionGroup
from .services import resolve_base_index, resolve_index


class Lot2BApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("lot2b-owner@example.com", "password-123")
        self.admin = user_model.objects.create_user("lot2b-admin@example.com", "password-123")
        self.member = user_model.objects.create_user("lot2b-member@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="LOT2B Company")
        self.other_company = Company.objects.create(raison_sociale="LOT2B Other")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.admin, company=self.company, role=Membership.Role.ADMIN)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        self.market = Market.objects.create(company=self.company, market_number="LOT2B-001", contracting_authority="Commune", subject="Travaux", formula_structure=Market.FormulaStructure.SINGLE)
        self.other_market = Market.objects.create(company=self.other_company, market_number="LOT2B-001", contracting_authority="Commune", subject="Autres travaux", formula_structure=Market.FormulaStructure.SINGLE)
        self.group = RevisionGroup.objects.create(market=self.market, code="F1", name="Formule 1")
        self.other_group = RevisionGroup.objects.create(market=self.other_market, code="F1", name="Formule autre")
        self.formula = MarketFormula.objects.create(revision_group=self.group, version_number=1, label="BAT3", constant_term=Decimal("0.15"), created_by=self.owner)
        self.client = APIClient(); self.client.force_authenticate(self.owner)

    def item_payload(self, **extra):
        payload = {"price_number": "00001", "designation": "Câble HTA", "unit": "ml", "estimated_quantity": "10.000000", "unit_price_ht": "12.50000000", "estimated_amount_ht": "125.00"}
        payload.update(extra)
        return payload

    def test_global_formula_without_bdp_is_accepted(self):
        response = self.client.patch(f"/api/markets/{self.market.id}/revision-application/", {"revision_application_mode": "GLOBAL_FORMULA", "global_revision_group": str(self.group.id)}, format="json")
        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        self.assertEqual(response.data["revision_application_mode"], "GLOBAL_FORMULA")
        schedule = self.client.get(f"/api/markets/{self.market.id}/price-schedule/")
        self.assertEqual(schedule.status_code, 200)
        self.assertFalse(schedule.data["required"])
        self.assertIsNone(schedule.data["schedule"])

    def test_assignment_endpoint_rejects_global_formula_mode(self):
        response = self.client.patch(f"/api/markets/{self.market.id}/revision-application/", {"revision_application_mode": "GLOBAL_FORMULA", "global_revision_group": str(self.group.id)}, format="json")
        self.assertEqual(response.status_code, 200)
        rejected = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "VALIDATE"}, format="json")
        self.assertEqual(rejected.status_code, 400)

    def test_global_formula_requires_exactly_one_applicable_formula(self):
        RevisionGroup.objects.get(pk=self.group.pk).formulas.create(
            version_number=2,
            label="BAT3 v2",
            constant_term=Decimal("0.20"),
            created_by=self.owner,
        )
        response = self.client.patch(
            f"/api/markets/{self.market.id}/revision-application/",
            {"revision_application_mode": "GLOBAL_FORMULA", "global_revision_group": str(self.group.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_mode_transitions_preserve_schedule_and_refuse_conflicting_global_transition(self):
        schedule = self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        self.assertEqual(schedule.status_code, 201)
        self.assertEqual(item.status_code, 201)
        global_response = self.client.patch(
            f"/api/markets/{self.market.id}/revision-application/",
            {"revision_application_mode": "GLOBAL_FORMULA", "global_revision_group": str(self.group.id)},
            format="json",
        )
        self.assertEqual(global_response.status_code, 400)
        self.assertTrue(PriceSchedule.objects.filter(pk=schedule.data["id"]).exists())
        self.assertTrue(PriceItem.objects.filter(pk=item.data["id"]).exists())

    def test_bulk_assignment_is_atomic_and_accepts_canonical_uppercase_actions(self):
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        first = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        second = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(price_number="00002"), format="json")
        self.client.patch(f"/api/markets/{self.market.id}/price-schedule/items/{second.data['id']}/", {"classification_status": "NON_REVISABLE"}, format="json")
        response = self.client.post(
            f"/api/markets/{self.market.id}/price-schedule/assignments/",
            {"action": "ASSIGN", "revision_group_id": str(self.group.id), "price_item_ids": [first.data["id"], second.data["id"]]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(PriceItem.objects.get(pk=first.data["id"]).revision_group_id)

    def test_admin_can_manage_and_member_cannot_change_individual_price(self):
        schedule = self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        admin = APIClient(); admin.force_authenticate(self.admin)
        member = APIClient(); member.force_authenticate(self.member)
        self.assertEqual(admin.patch(f"/api/markets/{self.market.id}/price-schedule/items/{item.data['id']}/", {"designation": "Administré"}, format="json").status_code, 200)
        self.assertEqual(member.patch(f"/api/markets/{self.market.id}/price-schedule/items/{item.data['id']}/", {"designation": "Interdit"}, format="json").status_code, 403)

    def test_price_assignment_requires_bdp_and_rejects_double_assignment(self):
        schedule = self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        self.assertEqual(schedule.status_code, 201)
        first = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        self.assertEqual(first.status_code, 201)
        second_group = RevisionGroup.objects.create(market=self.market, code="F2", name="Formule 2")
        assigned = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "assign", "revision_group_id": str(self.group.id), "price_item_ids": [first.data["id"]]}, format="json")
        self.assertEqual(assigned.status_code, 200)
        changed = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "assign", "revision_group_id": str(second_group.id), "price_item_ids": [first.data["id"]], "expected_version": assigned.data["change_version"]}, format="json")
        self.assertEqual(changed.status_code, 400)
        item = PriceItem.objects.get(pk=first.data["id"])
        self.assertEqual(item.revision_group_id, self.group.id)
        self.assertEqual(item.classification_status, PriceItem.ClassificationStatus.REVISABLE)

    def test_price_assignment_validation_requires_every_price_to_be_decided(self):
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        response = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "VALIDATE"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "ASSIGN", "revision_group_id": str(self.group.id), "price_item_ids": [item.data["id"]]}, format="json")
        response = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "VALIDATE"}, format="json")
        self.assertEqual(response.status_code, 200, getattr(response, "data", response.content))
        self.assertTrue(response.data["validated"])

    def test_non_revisable_is_explicit_and_cannot_be_assigned(self):
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        self.assertEqual(item.status_code, 201)
        updated = self.client.patch(f"/api/markets/{self.market.id}/price-schedule/items/{item.data['id']}/", {"classification_status": "NON_REVISABLE"}, format="json")
        self.assertEqual(updated.status_code, 200)
        rejected = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "assign", "revision_group_id": str(self.group.id), "price_item_ids": [item.data["id"]]}, format="json")
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(PriceItem.objects.get(pk=item.data["id"]).revision_group_id, None)

    def test_cross_market_group_and_float_are_rejected(self):
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        float_item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(estimated_quantity=10.5), format="json")
        self.assertEqual(float_item.status_code, 400)
        item = self.client.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json")
        self.assertEqual(item.status_code, 201)
        cross_market = self.client.post(f"/api/markets/{self.market.id}/price-schedule/assignments/", {"action": "assign", "revision_group_id": str(self.other_group.id), "price_item_ids": [item.data["id"]]}, format="json")
        self.assertEqual(cross_market.status_code, 400)

    def test_member_is_read_only_and_market_isolation_is_preserved(self):
        self.client.post(f"/api/markets/{self.market.id}/price-schedule/", {}, format="json")
        member = APIClient(); member.force_authenticate(self.member)
        self.assertEqual(member.get(f"/api/markets/{self.market.id}/price-schedule/").status_code, 200)
        self.assertEqual(member.post(f"/api/markets/{self.market.id}/price-schedule/items/", self.item_payload(), format="json").status_code, 403)
        self.assertEqual(self.client.get(f"/api/markets/{self.other_market.id}/price-schedule/").status_code, 404)


class V1SimpleFormulaApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("v1-owner@example.com", "password-123")
        self.member = user_model.objects.create_user("v1-member@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="V1 Company")
        self.other_company = Company.objects.create(raison_sociale="V1 Other")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        self.market = Market.objects.create(company=self.company, market_number="V1-001", contracting_authority="Commune", subject="Marché simple", formula_structure=Market.FormulaStructure.SINGLE)
        self.client = APIClient(); self.client.force_authenticate(self.owner)

    def test_v1_catalog_is_visible_without_search_and_contains_bat3(self):
        response = self.client.get("/api/formula-templates/")
        self.assertEqual(response.status_code, 200)
        codes = {item["code"] for item in response.data}
        self.assertIn("BAT3", codes)
        bat3 = next(item for item in response.data if item["code"] == "BAT3")
        self.assertEqual(bat3["designation"], "Électricité")
        self.assertIn("BAT3", bat3["expression_display"])

    def test_v1_can_select_one_global_formula_without_bdp_or_lot(self):
        template = FormulaTemplate.objects.get(code="BAT3", scope=FormulaTemplate.Scope.GLOBAL, status=FormulaTemplate.Status.VERIFIED)
        group = self.client.post(f"/api/markets/{self.market.id}/revision-groups/", {"code": "BAT3", "name": "Électricité"}, format="json")
        self.assertEqual(group.status_code, 201, getattr(group, "data", group.content))
        copied = self.client.post(f"/api/markets/{self.market.id}/revision-groups/{group.data['id']}/formulas/from-template/", {"template_id": str(template.id)}, format="json")
        self.assertEqual(copied.status_code, 201, getattr(copied, "data", copied.content))
        selected = self.client.patch(f"/api/markets/{self.market.id}/revision-application/", {"revision_application_mode": "GLOBAL_FORMULA", "global_revision_group": group.data["id"]}, format="json")
        self.assertEqual(selected.status_code, 200, getattr(selected, "data", selected.content))
        self.assertFalse(PriceSchedule.objects.filter(market=self.market).exists())
        self.assertFalse(MarketLot.objects.filter(market=self.market).exists())
        self.assertEqual(self.market.revision_groups.count(), 1)
        self.assertEqual(self.market.revision_groups.first().formulas.exclude(status=MarketFormula.Status.INACTIVE).count(), 1)

    def test_v1_formula_selection_is_isolated_by_company(self):
        foreign_market = Market.objects.create(company=self.other_company, market_number="V1-001", contracting_authority="Commune", subject="Autre marché", formula_structure=Market.FormulaStructure.SINGLE)
        self.assertEqual(self.client.get(f"/api/markets/{foreign_market.id}/revision-groups/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/markets/{foreign_market.id}/revision-application/").status_code, 404)


class IndexRepositoryTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("index-owner@example.com", "password-123")
        self.member = user_model.objects.create_user("index-member@example.com", "password-123")
        self.other = user_model.objects.create_user("index-other@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="Index Company")
        self.other_company = Company.objects.create(raison_sociale="Other Index Company")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        self.definition = IndexDefinition.objects.create(code="BAT3-TEST", designation="Électricité", domain="BAT")
        self.publication = IndexPublication.objects.get(year=2025, month=11)
        self.publication.status = IndexPublication.Status.VALIDATED
        self.publication.save(update_fields=["status"])
        self.value = MonthlyIndexValue.objects.create(index_definition=self.definition, publication=self.publication, year=2025, month=11, value=Decimal("337.8"), status=MonthlyIndexValue.Status.DEFINITIVE)
        self.client = APIClient(); self.client.force_authenticate(self.owner)

    def test_decimal_and_unique_code_month(self):
        self.assertEqual(self.value.value, Decimal("337.80000000"))
        with self.assertRaises(ValidationError):
            MonthlyIndexValue.objects.create(index_definition=self.definition, publication=self.publication, year=2025, month=11, value=Decimal("338"), status=MonthlyIndexValue.Status.PROVISIONAL)

    def test_exact_resolution_has_source_and_no_month_fallback(self):
        resolved = resolve_index("BAT3-TEST", 2025, 11)
        self.assertEqual(resolved["value"], "337.80000000")
        self.assertEqual(resolved["status"], MonthlyIndexValue.Status.DEFINITIVE)
        self.assertEqual(resolved["source"]["document_reference"], "Barème novembre 2025")
        self.assertEqual(resolve_index("BAT3-TEST", 2025, 10)["status"], "INDEX_NOT_AVAILABLE")
        self.assertEqual(resolve_index("BAT3-TEST", 2025, 12)["status"], "INDEX_NOT_AVAILABLE")

    def test_api_filters_and_member_read_isolation(self):
        response = self.client.get("/api/indices/values/?year=2025&month=11&code=BAT3-TEST&domain=BAT&status=DEFINITIVE")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        member = APIClient(); member.force_authenticate(self.member)
        self.assertEqual(member.get("/api/indices/publications/").status_code, 200)
        other = APIClient(); other.force_authenticate(self.other)
        self.assertEqual(other.get("/api/indices/values/").status_code, 403)

    def test_base_resolution_uses_exact_market_month_and_formula_code(self):
        market = Market.objects.create(company=self.company, market_number="INDEX-001", contracting_authority="Commune", subject="Travaux", date_limite_remise_offres=date(2025, 11, 19), formula_structure=Market.FormulaStructure.SINGLE)
        group = RevisionGroup.objects.create(market=market, code="BAT3-TEST", name="Électricité")
        formula = MarketFormula.objects.create(revision_group=group, version_number=1, label="BAT3", created_by=self.owner)
        FormulaTerm.objects.create(formula=formula, position=1, coefficient=Decimal("0.85"), index_code="BAT3-TEST", base_value=None)
        market.revision_application_mode = Market.RevisionApplicationMode.GLOBAL_FORMULA
        market.global_revision_group = group
        market.save(update_fields=["revision_application_mode", "global_revision_group", "updated_at"])
        result = resolve_base_index(market, formula)
        self.assertEqual(result["base_month"], "2025-11")
        self.assertEqual(result["base_index_value"], "337.80000000")
        base_response = self.client.get(f"/api/markets/{market.id}/base-index/")
        self.assertEqual(base_response.status_code, 200)
        self.assertEqual(base_response.data["base_index_value"], "337.80000000")

    def test_publication_import_command_is_available(self):
        from django.core.management import get_commands
        self.assertIn("import_index_publication", get_commands())


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


class RevisionFormulaApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("formula-owner@example.com", "password-123")
        self.member = user_model.objects.create_user("formula-member@example.com", "password-123")
        self.other = user_model.objects.create_user("formula-other@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="NAXU")
        self.other_company = Company.objects.create(raison_sociale="Autre société")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        Membership.objects.create(user=self.other, company=self.other_company, role=Membership.Role.OWNER)
        self.market = Market.objects.create(
            company=self.company, market_number="10006299/4500004338", contracting_authority="Agadir",
            subject="Travaux électriques", formula_structure=Market.FormulaStructure.SINGLE,
        )
        self.group = RevisionGroup.objects.create(market=self.market, code="ELEC", name="Travaux électriques")

    def authenticated(self, user):
        client = APIClient(); client.force_authenticate(user); return client

    def draft_payload(self, **extra):
        payload = {
            "label": "Formule travaux électriques", "expression_display": "K = 0,15 + 0,85 × BAT3/BAT3₀",
            "constant_term": "0.15", "terms": [{"position": 1, "coefficient": "0.85", "term_type": "INDEX_RATIO", "index_code": "BAT3", "base_value": "337.80000000"}],
        }
        payload.update(extra)
        return payload

    def test_create_group_formula_and_terms_uses_decimal_strings(self):
        response = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["constant_term"], "0.15000000")
        self.assertEqual(response.data["terms"][0]["coefficient"], "0.85000000")
        self.assertEqual(response.data["terms"][0]["base_value"], "337.80000000")
        self.assertEqual(MarketFormula.objects.get(revision_group=self.group).terms.get().coefficient, Decimal("0.85000000"))

    def test_float_financial_input_is_rejected(self):
        response = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(constant_term=0.15), format="json")
        self.assertEqual(response.status_code, 400)

    def test_validated_formula_requires_coherent_sum_and_is_immutable(self):
        invalid = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(status="VALIDATED", constant_term="0.20"), format="json")
        self.assertEqual(invalid.status_code, 400)
        valid = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(status="VALIDATED"), format="json")
        self.assertEqual(valid.status_code, 201)
        formula_id = valid.data["id"]
        immutable = self.authenticated(self.owner).patch(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/{formula_id}/", {"label": "Réécriture interdite"}, format="json")
        self.assertEqual(immutable.status_code, 400)
        inactive = self.authenticated(self.owner).patch(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/{formula_id}/", {"status": "INACTIVE"}, format="json")
        self.assertEqual(inactive.status_code, 200)

    def test_new_version_is_allowed_and_two_validated_versions_overlap_is_rejected(self):
        first = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(status="VALIDATED"), format="json")
        self.assertEqual(first.status_code, 201)
        second = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(status="VALIDATED"), format="json")
        self.assertEqual(second.status_code, 400)
        created = self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", self.draft_payload(version_number=2), format="json")
        self.assertEqual(created.status_code, 201)
        self.assertEqual(created.data["version_number"], 2)

    def test_member_reads_but_cannot_write_and_other_market_isolated(self):
        self.assertEqual(self.authenticated(self.member).get(f"/api/markets/{self.market.id}/revision-groups/").status_code, 200)
        denied = self.authenticated(self.member).post(f"/api/markets/{self.market.id}/revision-groups/", {"code": "NO", "name": "Interdit"}, format="json")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.authenticated(self.other).get(f"/api/markets/{self.market.id}/revision-groups/").status_code, 404)

    def test_duplicate_term_positions_and_missing_validated_base_are_rejected(self):
        duplicate = self.draft_payload(status="VALIDATED", terms=[
            {"position": 1, "coefficient": "0.40", "index_code": "I1", "base_value": "100"},
            {"position": 1, "coefficient": "0.45", "index_code": "I2", "base_value": "100"},
        ])
        self.assertEqual(self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", duplicate, format="json").status_code, 400)
        missing = self.draft_payload(status="VALIDATED", terms=[{"position": 1, "coefficient": "0.85", "index_code": "BAT3", "base_value": None}])
        self.assertEqual(self.authenticated(self.owner).post(f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/", missing, format="json").status_code, 400)

    def test_validated_formula_and_terms_are_immutable_through_orm(self):
        response = self.authenticated(self.owner).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/",
            self.draft_payload(status="VALIDATED"), format="json",
        )
        self.assertEqual(response.status_code, 201)
        formula = MarketFormula.objects.get(pk=response.data["id"])
        term = formula.terms.get()

        formula.label = "Mutation ORM interdite"
        with self.assertRaises(ValidationError):
            formula.save()
        with self.assertRaises(ValidationError):
            MarketFormula.objects.filter(pk=formula.pk).update(label="Mutation bulk interdite")
        formula.label = "Mutation bulk_update interdite"
        with self.assertRaises(ValidationError):
            MarketFormula.objects.bulk_update([formula], ["label"])
        with self.assertRaises(ValidationError):
            MarketFormula.objects.bulk_create([MarketFormula(
                revision_group=self.group, version_number=2, label="Création bulk interdite",
                constant_term=Decimal("1"), status=MarketFormula.Status.VALIDATED, created_by=self.owner,
            )])
        term.coefficient = Decimal("0.70")
        with self.assertRaises(ValidationError):
            term.save()
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.filter(pk=term.pk).update(coefficient=Decimal("0.70"))
        term.coefficient = Decimal("0.70")
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.bulk_update([term], ["coefficient"])
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.bulk_create([FormulaTerm(
                formula=formula, position=2, coefficient=Decimal("0.10"),
                term_type=FormulaTerm.TermType.INDEX_RATIO, index_code="I2", base_value=Decimal("100"),
            )])
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.create(
                formula=formula, position=2, coefficient=Decimal("0.10"),
                term_type=FormulaTerm.TermType.INDEX_RATIO, index_code="I2", base_value=Decimal("100"),
            )
        with self.assertRaises(ProtectedError):
            term.delete()
        with self.assertRaises(ProtectedError):
            FormulaTerm.objects.filter(pk=term.pk).delete()
        with self.assertRaises(ProtectedError):
            formula.delete()
        with self.assertRaises(ProtectedError):
            MarketFormula.objects.filter(pk=formula.pk).delete()
        with self.assertRaises(ProtectedError):
            self.market.delete()

    def test_draft_terms_remain_mutable_through_normal_orm_operations(self):
        draft = MarketFormula.objects.create(
            revision_group=self.group, version_number=1, label="DRAFT", constant_term=Decimal("0.15"), created_by=self.owner,
        )
        term = FormulaTerm.objects.create(
            formula=draft, position=1, coefficient=Decimal("0.85"), index_code="I1", base_value=Decimal("100"),
        )
        term.coefficient = Decimal("0.80")
        term.save()
        self.assertEqual(draft.terms.get().coefficient, Decimal("0.80"))
        term.delete()
        self.assertFalse(draft.terms.exists())

    def test_domain_invariants_are_enforced_without_serializer(self):
        draft = MarketFormula.objects.create(
            revision_group=self.group, version_number=1, label="DRAFT", constant_term=Decimal("0.15"), created_by=self.owner,
        )
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.create(formula=draft, position=1, coefficient=Decimal("0.85"), term_type="UNKNOWN", index_code="I", base_value=Decimal("100"))
        with self.assertRaises(ValidationError):
            FormulaTerm.objects.create(formula=draft, position=1, coefficient=Decimal("0.85"), index_code="   ", base_value=Decimal("100"))
        draft.status = MarketFormula.Status.VALIDATED
        with self.assertRaises(ValidationError):
            draft.save()

    def test_version_number_is_read_only_and_date_order_is_validated_on_partial_update(self):
        created = self.authenticated(self.owner).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/",
            self.draft_payload(valid_from="2026-02-01"), format="json",
        )
        self.assertEqual(created.status_code, 201)
        formula_url = f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/{created.data['id']}/"
        unchanged = self.authenticated(self.owner).patch(formula_url, {"version_number": 99}, format="json")
        self.assertEqual(unchanged.status_code, 200)
        self.assertEqual(unchanged.data["version_number"], 1)
        invalid_dates = self.authenticated(self.owner).patch(formula_url, {"valid_to": "2026-01-01"}, format="json")
        self.assertEqual(invalid_dates.status_code, 400)


class FormulaTemplateTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("template-owner@example.com", "password-123")
        self.member = user_model.objects.create_user("template-member@example.com", "password-123")
        self.other = user_model.objects.create_user("template-other@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="Template Company")
        self.other_company = Company.objects.create(raison_sociale="Other Template Company")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, company=self.company, role=Membership.Role.MEMBER)
        Membership.objects.create(user=self.other, company=self.other_company, role=Membership.Role.OWNER)
        self.market = Market.objects.create(
            company=self.company, market_number="TEMPLATE-MARKET", contracting_authority="Commune",
            subject="Travaux", formula_structure=Market.FormulaStructure.SINGLE,
        )
        self.group = RevisionGroup.objects.create(market=self.market, code="GEN", name="Général")

    def authenticated(self, user):
        client = APIClient(); client.force_authenticate(user); return client

    def create_verified_template(self):
        template = FormulaTemplate.objects.create(
            family_key=uuid.uuid4(), version_number=1, scope=FormulaTemplate.Scope.GLOBAL,
            code="EXAMPLE-001", designation="Exemple contractuel", expression_display="K = C + A × I/I₀",
            constant_term=Decimal("0.15"), source_type=FormulaTemplate.SourceType.CONTRACT_EXAMPLE,
            source_title="CPS de test", source_reference="FIXTURE-001", status=FormulaTemplate.Status.DRAFT,
        )
        FormulaTemplateTerm.objects.create(
            template=template, position=1, coefficient=Decimal("0.85"), index_code="IDX-TEST", base_value=Decimal("100.00000000"),
        )
        template.status = FormulaTemplate.Status.VERIFIED
        template.verification_status = "TEST_VERIFIED"
        template.save()
        return template

    def test_global_templates_are_readable_but_not_writable_by_business_api(self):
        template = self.create_verified_template()
        listed = self.authenticated(self.member).get("/api/formula-templates/")
        self.assertEqual(listed.status_code, 200)
        self.assertIn(str(template.id), {item["id"] for item in listed.data})
        listed_template = next(item for item in listed.data if item["id"] == str(template.id))
        self.assertEqual(listed_template["terms"][0]["coefficient"], "0.85000000")
        self.assertEqual(self.authenticated(self.other).get(f"/api/formula-templates/{template.id}/").status_code, 200)
        self.assertEqual(self.authenticated(self.member).post("/api/formula-templates/", {}, format="json").status_code, 405)

    def test_global_template_read_requires_active_membership_or_superuser(self):
        template = self.create_verified_template()
        user_model = get_user_model()
        admin = user_model.objects.create_user("template-admin@example.com", "password-123")
        Membership.objects.create(user=admin, company=self.company, role=Membership.Role.ADMIN)
        no_membership = user_model.objects.create_user("template-no-membership@example.com", "password-123")
        inactive = user_model.objects.create_user("template-inactive@example.com", "password-123")
        Membership.objects.create(user=inactive, company=self.company, role=Membership.Role.MEMBER, active=False)
        superuser = user_model.objects.create_superuser("template-superuser@example.com", "password-123")

        for user in (no_membership, inactive):
            self.assertEqual(self.authenticated(user).get("/api/formula-templates/").status_code, 403)
            self.assertEqual(self.authenticated(user).get(f"/api/formula-templates/{template.id}/").status_code, 403)
        for user in (self.owner, admin, self.member, self.other, superuser):
            self.assertEqual(self.authenticated(user).get("/api/formula-templates/").status_code, 200)
            self.assertEqual(self.authenticated(user).get(f"/api/formula-templates/{template.id}/").status_code, 200)
        self.assertEqual(APIClient().get("/api/formula-templates/").status_code, 401)
        self.assertEqual(APIClient().get(f"/api/formula-templates/{template.id}/").status_code, 401)

    def test_copy_is_transactional_independent_and_preserves_traceability(self):
        template = self.create_verified_template()
        response = self.authenticated(self.owner).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/from-template/",
            {"template_id": str(template.id)}, format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], "DRAFT")
        self.assertEqual(str(response.data["source_template"]), str(template.id))
        self.assertEqual(response.data["source_template_version"], 1)
        self.assertEqual(response.data["terms"][0]["coefficient"], "0.85000000")
        formula = MarketFormula.objects.get(pk=response.data["id"])
        self.assertEqual(formula.source_template_id, template.id)
        formula.label = "Formule de marché indépendante"
        formula.save()
        self.assertEqual(FormulaTemplate.objects.get(pk=template.id).designation, "Exemple contractuel")

    def test_member_cannot_copy_template_to_market(self):
        template = self.create_verified_template()
        response = self.authenticated(self.member).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/from-template/",
            {"template_id": str(template.id)}, format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.authenticated(self.other).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/from-template/",
            {"template_id": str(template.id)}, format="json",
        ).status_code, 404)

    def test_copy_failure_rolls_back_formula_and_terms(self):
        template = FormulaTemplate.objects.create(
            family_key=uuid.uuid4(), version_number=1, scope=FormulaTemplate.Scope.GLOBAL,
            code="BROKEN-001", designation="Template invalide", constant_term=Decimal("0.15"),
            source_type=FormulaTemplate.SourceType.CONTRACT_EXAMPLE, source_title="Fixture", source_reference="BROKEN",
        )
        FormulaTemplateTerm.objects.bulk_create([FormulaTemplateTerm(
            template=template, position=1, coefficient=Decimal("0.85"), index_code=" ", base_value=Decimal("100"),
        )])
        template.status = FormulaTemplate.Status.VERIFIED
        template.save()
        response = self.authenticated(self.owner).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/from-template/",
            {"template_id": str(template.id)}, format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(MarketFormula.objects.filter(source_template=template).exists())

    def test_deprecated_template_is_traceable_but_not_copyable(self):
        template = self.create_verified_template()
        template.status = FormulaTemplate.Status.DEPRECATED
        template.save()
        listed = self.authenticated(self.member).get(f"/api/formula-templates/{template.id}/")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data["status"], "DEPRECATED")
        response = self.authenticated(self.owner).post(
            f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/from-template/",
            {"template_id": str(template.id)}, format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_verified_template_and_terms_are_immutable_through_orm(self):
        template = self.create_verified_template()
        term = template.terms.get()
        template.designation = "Mutation interdite"
        with self.assertRaises(ValidationError):
            template.save()
        with self.assertRaises(ValidationError):
            FormulaTemplate.objects.filter(pk=template.pk).update(designation="Bulk interdite")
        template.designation = "Bulk update interdite"
        with self.assertRaises(ValidationError):
            FormulaTemplate.objects.bulk_update([template], ["designation"])
        with self.assertRaises(ValidationError):
            FormulaTemplate.objects.bulk_create([FormulaTemplate(
                family_key=uuid.uuid4(), version_number=1, code="BULK", designation="Bulk", source_type=FormulaTemplate.SourceType.INTERNAL, status=FormulaTemplate.Status.VERIFIED,
            )])
        term.coefficient = Decimal("0.70")
        with self.assertRaises(ValidationError):
            term.save()
        with self.assertRaises(ValidationError):
            FormulaTemplateTerm.objects.filter(pk=term.pk).update(coefficient=Decimal("0.70"))
        with self.assertRaises(ValidationError):
            FormulaTemplateTerm.objects.bulk_update([term], ["coefficient"])
        with self.assertRaises(ValidationError):
            FormulaTemplateTerm.objects.bulk_create([FormulaTemplateTerm(
                template=template, position=2, coefficient=Decimal("0.15"), index_code="IDX-2", base_value=Decimal("100"),
            )])
        with self.assertRaises(ProtectedError):
            term.delete()
        with self.assertRaises(ProtectedError):
            FormulaTemplateTerm.objects.filter(pk=term.pk).delete()
        with self.assertRaises(ProtectedError):
            template.delete()
        with self.assertRaises(ProtectedError):
            FormulaTemplate.objects.filter(pk=template.pk).delete()

    def test_draft_template_terms_remain_creatable_and_mutable(self):
        template = FormulaTemplate.objects.create(
            family_key=uuid.uuid4(), version_number=1, code="DRAFT-001", designation="Brouillon",
            source_type=FormulaTemplate.SourceType.INTERNAL,
        )
        term = FormulaTemplateTerm.objects.create(template=template, position=1, coefficient=Decimal("0.85"), index_code="IDX", base_value=Decimal("100"))
        term.coefficient = Decimal("0.80")
        term.save()
        self.assertEqual(template.terms.get().coefficient, Decimal("0.80"))
        term.delete()
        self.assertFalse(template.terms.exists())


class FormulaVersionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        user_model = get_user_model()
        self.owner = user_model.objects.create_user("formula-concurrency@example.com", "password-123")
        self.company = Company.objects.create(raison_sociale="Concurrency Company")
        Membership.objects.create(user=self.owner, company=self.company, role=Membership.Role.OWNER)
        self.market = Market.objects.create(
            company=self.company, market_number="CONCURRENT", contracting_authority="Agadir",
            subject="Travaux", formula_structure=Market.FormulaStructure.SINGLE,
        )
        self.group = RevisionGroup.objects.create(market=self.market, code="G", name="Groupe")

    def create_formula(self):
        client = APIClient()
        client.force_authenticate(self.owner)
        try:
            return client.post(
                f"/api/markets/{self.market.id}/revision-groups/{self.group.id}/formulas/",
                {"label": "Formule concurrente", "constant_term": "0.15", "terms": [{"position": 1, "coefficient": "0.85", "index_code": "BAT3", "base_value": "100"}]},
                format="json",
            )
        finally:
            connection.close()

    def test_automatic_versions_are_serialized_under_concurrency(self):
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(executor.map(lambda _: self.create_formula(), range(2)))
        self.assertEqual(sorted(response.status_code for response in responses), [201, 201])
        self.assertEqual(sorted(response.data["version_number"] for response in responses), [1, 2])


class ConsortiumMarketPermissionTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.naxu_user = user_model.objects.create_user("naxu-owner@example.com", "password-123")
        self.naxu_admin = user_model.objects.create_user("naxu-admin@example.com", "password-123")
        self.naxu_member = user_model.objects.create_user("naxu-member@example.com", "password-123")
        self.ingc_admin = user_model.objects.create_user("ingc-admin@example.com", "password-123")
        self.no_membership = user_model.objects.create_user("outside@example.com", "password-123")
        self.naxu = Company.objects.create(raison_sociale="NAXU")
        self.ingc = Company.objects.create(raison_sociale="INGC")
        Membership.objects.create(user=self.naxu_user, company=self.naxu, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.naxu_admin, company=self.naxu, role=Membership.Role.ADMIN)
        Membership.objects.create(user=self.naxu_member, company=self.naxu, role=Membership.Role.MEMBER)
        Membership.objects.create(user=self.ingc_admin, company=self.ingc, role=Membership.Role.ADMIN)
        with transaction.atomic():
            self.consortium = Consortium.objects.create(owner_company=self.naxu, created_by=self.naxu_user, name="Groupement INGC/NAXU")
            ConsortiumMember.objects.create(consortium=self.consortium, company=self.ingc, role=ConsortiumMember.Role.MANDATAIRE, share_percent=Decimal("50.00"))
            ConsortiumMember.objects.create(consortium=self.consortium, company=self.naxu, role=ConsortiumMember.Role.MEMBER, share_percent=Decimal("50.00"))
        self.market = Market.objects.create(company=self.naxu, holder_type=Market.HolderType.CONSORTIUM, consortium=self.consortium, market_number="10006299/4500004338", contracting_authority="Société Régionale Multiservices Souss-Massa", subject="Travaux", formula_structure=Market.FormulaStructure.SINGLE)

    def api_client(self, user):
        client = APIClient(); client.force_authenticate(user); return client

    def test_naxu_member_can_read_and_administer_even_if_ingc_is_mandataire(self):
        response = self.api_client(self.naxu_user).get(f"/api/markets/{self.market.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["holder_type"], "CONSORTIUM")
        self.assertEqual(response.data["consortium_detail"]["name"], "Groupement INGC/NAXU")
        self.assertEqual(self.api_client(self.naxu_user).patch(f"/api/markets/{self.market.id}/", {"subject": "Administré par NAXU"}, format="json").status_code, 200)

    def test_missing_or_inactive_membership_cannot_read_group_market(self):
        self.assertEqual(self.api_client(self.no_membership).get(f"/api/markets/{self.market.id}/").status_code, 404)
        membership = Membership.objects.create(user=self.no_membership, company=self.naxu, role=Membership.Role.ADMIN, active=False)
        self.assertEqual(self.api_client(self.no_membership).get(f"/api/markets/{self.market.id}/").status_code, 404)
        membership.active = True; membership.save()
        self.assertEqual(self.api_client(self.no_membership).get(f"/api/markets/{self.market.id}/").status_code, 200)

    def test_owner_admin_member_and_ingc_permissions_do_not_follow_contractual_role(self):
        create_payload = {"company": str(self.naxu.id), "holder_type": "CONSORTIUM", "consortium": str(self.consortium.id), "market_number": "GROUP-CREATE-ADMIN", "contracting_authority": "Commune", "subject": "Travaux", "formula_structure": "SINGLE"}
        self.assertEqual(self.api_client(self.naxu_admin).post("/api/markets/", create_payload, format="json").status_code, 201)
        self.assertEqual(self.api_client(self.naxu_member).post("/api/markets/", {**create_payload, "market_number": "GROUP-CREATE-MEMBER"}, format="json").status_code, 400)
        self.assertEqual(self.api_client(self.naxu_admin).get(f"/api/markets/{self.market.id}/").status_code, 200)
        self.assertEqual(self.api_client(self.naxu_admin).patch(f"/api/markets/{self.market.id}/", {"subject": "Admin NAXU"}, format="json").status_code, 200)
        self.assertEqual(self.api_client(self.naxu_member).get(f"/api/markets/{self.market.id}/").status_code, 200)
        self.assertEqual(self.api_client(self.naxu_member).patch(f"/api/markets/{self.market.id}/", {"subject": "Refusé"}, format="json").status_code, 403)
        self.assertEqual(self.api_client(self.ingc_admin).get(f"/api/markets/{self.market.id}/").status_code, 200)
        self.assertEqual(self.api_client(self.ingc_admin).patch(f"/api/markets/{self.market.id}/", {"subject": "Admin INGC"}, format="json").status_code, 200)
        self.assertEqual(self.api_client(self.no_membership).get(f"/api/markets/{self.market.id}/").status_code, 404)

    def test_anonymous_is_refused_and_consortium_management_is_owner_admin_only(self):
        self.assertEqual(APIClient().get(f"/api/markets/{self.market.id}/").status_code, 401)
        self.assertEqual(self.api_client(self.naxu_member).get(f"/api/consortia/{self.consortium.id}/").status_code, 200)
        self.assertEqual(self.api_client(self.naxu_member).patch(f"/api/consortia/{self.consortium.id}/", {"notes": "Refusé"}, format="json").status_code, 403)
        self.assertEqual(self.api_client(self.naxu_admin).patch(f"/api/consortia/{self.consortium.id}/", {"notes": "Administré"}, format="json").status_code, 200)

    def test_market_creation_rejects_an_unmanaged_consortium_uuid(self):
        other_user = get_user_model().objects.create_user("other-owner@example.com", "password-123")
        other_company = Company.objects.create(raison_sociale="Autre société")
        Membership.objects.create(user=other_user, company=other_company, role=Membership.Role.OWNER)
        response = self.api_client(other_user).post("/api/markets/", {
            "company": str(other_company.id), "holder_type": "CONSORTIUM", "consortium": str(self.consortium.id),
            "market_number": "UNAUTHORIZED-GROUP", "contracting_authority": "Commune", "subject": "Travaux", "formula_structure": "SINGLE",
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("consortium", response.data["fields"])

    def test_market_update_rejects_substitution_with_unmanaged_consortium(self):
        other_user = get_user_model().objects.create_user("other-group-owner@example.com", "password-123")
        other_company = Company.objects.create(raison_sociale="Autre group company")
        other_member = Company.objects.create(raison_sociale="Autre group member")
        Membership.objects.create(user=other_user, company=other_company, role=Membership.Role.OWNER)
        response = self.api_client(other_user).post("/api/consortia/", {
            "owner_company": str(other_company.id), "name": "Autre groupement", "members": [
                {"company": str(other_company.id), "role": "MANDATAIRE", "share_percent": "50", "sort_order": 0, "active": True},
                {"company": str(other_member.id), "role": "MEMBER", "share_percent": "50", "sort_order": 1, "active": True},
            ],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        update = self.api_client(self.naxu_user).patch(f"/api/markets/{self.market.id}/", {"consortium": response.data["id"], "holder_type": "CONSORTIUM"}, format="json")
        self.assertEqual(update.status_code, 400)
        self.assertIn("consortium", update.data["fields"])
