from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from companies.models import Company
from authorities.models import ContractingAuthority
from consortia.models import Consortium
from consortia.permissions import can_manage_consortium
from companies.permissions import get_membership

from .models import FormulaTerm, Market, MarketFormula, MarketLot, RevisionGroup


def validate_non_blank(value, label):
    value = value.strip()
    if not value:
        raise serializers.ValidationError(f"{label} est obligatoire.")
    return value


class CompanySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "raison_sociale"]


class AuthoritySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractingAuthority
        fields = ["id", "name", "short_name", "active"]


class ConsortiumSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Consortium
        fields = ["id", "name", "owner_company"]


class MarketSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    company_detail = CompanySummarySerializer(source="company", read_only=True)
    holder_company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all(), required=False, allow_null=True)
    holder_company_detail = CompanySummarySerializer(source="holder_company", read_only=True)
    consortium_detail = ConsortiumSummarySerializer(source="consortium", read_only=True)
    authority_detail = AuthoritySummarySerializer(source="authority", read_only=True)
    current_user_role = serializers.SerializerMethodField()
    lots_count = serializers.IntegerField(source="lots.count", read_only=True)

    class Meta:
        model = Market
        fields = [
            "id", "company", "company_detail", "holder_type", "holder_company", "holder_company_detail", "consortium", "consortium_detail", "authority", "authority_detail", "market_number", "contracting_authority", "subject",
            "amount_ht", "vat_rate", "date_limite_remise_offres", "date_ouverture_plis", "date_signature",
            "date_os_commencement", "contract_duration_value", "contract_duration_unit", "formula_structure",
            "status", "notes", "created_at", "updated_at", "current_user_role", "lots_count",
        ]
        read_only_fields = ["id", "company_detail", "holder_company_detail", "consortium_detail", "authority_detail", "created_at", "updated_at", "current_user_role", "lots_count"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance is not None:
            self.fields["company"].read_only = True

    def get_current_user_role(self, market):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if request.user.is_superuser:
            return "OWNER"
        from .permissions import market_role
        return market_role(request.user, market)

    def validate_market_number(self, value):
        return validate_non_blank(value, "Le numéro du marché")

    def validate_contracting_authority(self, value):
        return validate_non_blank(value, "Le maître d'ouvrage")

    def validate_subject(self, value):
        return validate_non_blank(value, "L'objet du marché")

    def validate_amount_ht(self, value):
        if value is not None and value < Decimal("0"):
            raise serializers.ValidationError("Le montant HT doit être supérieur ou égal à zéro.")
        return value

    def validate_vat_rate(self, value):
        if value is not None and not Decimal("0") <= value <= Decimal("100"):
            raise serializers.ValidationError("Le taux de TVA doit être compris entre 0 et 100 %.")
        return value

    def validate(self, attrs):
        if self.instance is not None:
            attrs.pop("company", None)
        value = attrs.get("contract_duration_value", getattr(self.instance, "contract_duration_value", None))
        unit = attrs.get("contract_duration_unit", getattr(self.instance, "contract_duration_unit", None))
        if (value is None) != (unit is None):
            raise serializers.ValidationError({
                "contract_duration_value": "La valeur et l'unité du délai doivent être renseignées ensemble.",
            })
        if value is not None and value <= 0:
            raise serializers.ValidationError({"contract_duration_value": "La valeur du délai doit être strictement positive."})
        if self.instance is None and attrs.get("company") is None:
            raise serializers.ValidationError({"company": "La société est obligatoire."})
        holder_type = attrs.get("holder_type", getattr(self.instance, "holder_type", Market.HolderType.SOLE_COMPANY))
        holder_company = attrs.get("holder_company", getattr(self.instance, "holder_company", None))
        consortium = attrs.get("consortium", getattr(self.instance, "consortium", None))
        if holder_type == Market.HolderType.SOLE_COMPANY and holder_company is None and self.instance is None:
            attrs["holder_company"] = attrs.get("company")
            holder_company = attrs["company"]
        if holder_type == Market.HolderType.SOLE_COMPANY and (holder_company is None or consortium is not None):
            raise serializers.ValidationError({"holder_company": "La société titulaire est obligatoire et exclusive."})
        if holder_type == Market.HolderType.CONSORTIUM and (consortium is None or holder_company is not None):
            raise serializers.ValidationError({"consortium": "Le groupement titulaire est obligatoire et exclusif."})
        request = self.context.get("request")
        if request and not request.user.is_superuser and holder_type == Market.HolderType.SOLE_COMPANY and get_membership(request.user, holder_company) is None:
            raise serializers.ValidationError({"holder_company": "Cette société n’est pas accessible avec votre Membership active."})
        if consortium is not None and not consortium.active:
            raise serializers.ValidationError({"consortium": "Ce groupement est inactif."})
        consortium_changed = self.instance is None or (consortium is not None and consortium.pk != getattr(self.instance, "consortium_id", None))
        if request and consortium is not None and consortium_changed and not request.user.is_superuser and not can_manage_consortium(request.user, consortium):
            raise serializers.ValidationError({"consortium": "Ce groupement n’est pas administrable avec votre Membership active."})
        if attrs.get("authority") is not None:
            attrs["contracting_authority"] = attrs["authority"].name
        return attrs


class MarketLotSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketLot
        fields = [
            "id", "market", "lot_number", "title", "description", "amount_ht", "display_order", "active",
            "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "market", "created_at", "updated_at"]

    def validate_lot_number(self, value):
        return validate_non_blank(value, "Le numéro du lot")

    def validate_title(self, value):
        return validate_non_blank(value, "Le titre du lot")

    def validate_amount_ht(self, value):
        if value is not None and value < Decimal("0"):
            raise serializers.ValidationError("Le montant HT doit être supérieur ou égal à zéro.")
        return value

    def validate_display_order(self, value):
        if value < 0:
            raise serializers.ValidationError("L'ordre d'affichage doit être supérieur ou égal à zéro.")
        return value


class StrictDecimalField(serializers.DecimalField):
    """Require decimal strings at the API boundary; never accept binary floats."""

    def to_internal_value(self, data):
        if data is not None and not isinstance(data, str):
            raise serializers.ValidationError("Cette valeur doit être fournie comme chaîne décimale.")
        return super().to_internal_value(data)


class FormulaTermSerializer(serializers.ModelSerializer):
    coefficient = StrictDecimalField(max_digits=18, decimal_places=8)
    base_value = StrictDecimalField(max_digits=18, decimal_places=8, required=False, allow_null=True)

    class Meta:
        model = FormulaTerm
        fields = [
            "id", "position", "coefficient", "term_type", "index_code", "base_period_year",
            "base_period_month", "base_value", "base_source", "reference_note", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_position(self, value):
        if value < 1:
            raise serializers.ValidationError("La position doit être supérieure ou égale à 1.")
        return value

    def validate_index_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le code de l’index est obligatoire.")
        return value


def validate_formula_terms(terms, status):
    positions = [term.get("position") for term in terms]
    if len(positions) != len(set(positions)):
        raise serializers.ValidationError({"terms": "Chaque terme doit avoir une position unique."})
    if status != MarketFormula.Status.VALIDATED:
        return
    if not terms:
        raise serializers.ValidationError({"terms": "Une formule validée doit comporter au moins un terme."})
    for term in terms:
        if term.get("term_type", FormulaTerm.TermType.INDEX_RATIO) == FormulaTerm.TermType.INDEX_RATIO:
            if term.get("base_value") is None or term["base_value"] <= Decimal("0"):
                raise serializers.ValidationError({"terms": "Chaque ratio d’index validé doit avoir une valeur de base strictement positive."})


class MarketFormulaSerializer(serializers.ModelSerializer):
    constant_term = StrictDecimalField(max_digits=18, decimal_places=8, required=False, allow_null=True)
    terms = FormulaTermSerializer(many=True, required=False)

    class Meta:
        model = MarketFormula
        fields = [
            "id", "revision_group", "version_number", "label", "expression_display", "constant_term", "status",
            "valid_from", "valid_to", "reference_period_year", "reference_period_month", "reference_rule_code",
            "reference_source", "created_by", "created_at", "updated_at", "validated_at", "terms",
        ]
        read_only_fields = ["id", "revision_group", "version_number", "created_by", "created_at", "updated_at", "validated_at"]
        extra_kwargs = {"version_number": {"required": False}}

    def validate_label(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le libellé de la formule est obligatoire.")
        return value

    def validate(self, attrs):
        instance = self.instance
        current_status = instance.status if instance else MarketFormula.Status.DRAFT
        requested_status = attrs.get("status", current_status)
        if instance and current_status == MarketFormula.Status.VALIDATED:
            changed = set(attrs) - {"status"}
            if changed or requested_status == MarketFormula.Status.VALIDATED:
                if requested_status != MarketFormula.Status.INACTIVE or changed:
                    raise serializers.ValidationError("Une formule validée est immuable. Créez une nouvelle version.")
        if instance and current_status == MarketFormula.Status.INACTIVE and requested_status != MarketFormula.Status.INACTIVE:
            raise serializers.ValidationError("Une formule inactive ne peut pas être réactivée.")
        if requested_status == MarketFormula.Status.VALIDATED and current_status == MarketFormula.Status.INACTIVE:
            raise serializers.ValidationError("Une formule inactive ne peut pas être validée.")
        terms = attrs.get("terms")
        if terms is None and instance is not None:
            terms = list(instance.terms.values("position", "coefficient", "term_type", "index_code", "base_value"))
        validate_formula_terms(terms or [], requested_status)
        constant = attrs.get("constant_term", instance.constant_term if instance else None)
        if requested_status == MarketFormula.Status.VALIDATED:
            if constant is None:
                raise serializers.ValidationError({"constant_term": "La constante est obligatoire pour valider la formule."})
            if constant < Decimal("0.15"):
                raise serializers.ValidationError({"constant_term": "La constante doit être supérieure ou égale à 0,15 pour cette structure de formule."})
            total = constant + sum((term["coefficient"] for term in (terms or [])), Decimal("0"))
            if total != Decimal("1"):
                raise serializers.ValidationError({"terms": "La constante et les coefficients doivent totaliser exactement 1,00."})
            group = self.context.get("revision_group") or (instance.revision_group if instance else None)
            if group is not None:
                valid_from = attrs.get("valid_from", instance.valid_from if instance else None)
                valid_to = attrs.get("valid_to", instance.valid_to if instance else None)
                for other in group.formulas.filter(status=MarketFormula.Status.VALIDATED).exclude(pk=getattr(instance, "pk", None)):
                    overlaps = (valid_to is None or other.valid_from is None or other.valid_from <= valid_to) and (other.valid_to is None or valid_from is None or valid_from <= other.valid_to)
                    if overlaps:
                        raise serializers.ValidationError({"status": "Une seule formule VALIDATED peut être applicable à une même période."})
        valid_from = attrs.get("valid_from", instance.valid_from if instance else None)
        valid_to = attrs.get("valid_to", instance.valid_to if instance else None)
        if valid_from and valid_to and valid_to < valid_from:
            raise serializers.ValidationError({"valid_to": "La fin de validité doit être postérieure ou égale au début."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        terms = validated_data.pop("terms", [])
        group = self.context["revision_group"]
        requested_status = validated_data.get("status", MarketFormula.Status.DRAFT)
        locked_group = RevisionGroup.objects.select_for_update().get(pk=group.pk)
        validated_data["revision_group"] = locked_group
        validated_data["created_by"] = self.context["request"].user
        if "version_number" not in validated_data:
            last = locked_group.formulas.order_by("-version_number").values_list("version_number", flat=True).first()
            validated_data["version_number"] = (last or 0) + 1
        if requested_status == MarketFormula.Status.VALIDATED:
            self._validate_locked_group_overlap(locked_group, validated_data)
            validated_data["status"] = MarketFormula.Status.DRAFT
        formula = MarketFormula.objects.create(**validated_data)
        for term in terms:
            FormulaTerm.objects.create(formula=formula, **term)
        if requested_status == MarketFormula.Status.VALIDATED:
            from django.utils import timezone
            formula.status = MarketFormula.Status.VALIDATED
            formula.validated_at = timezone.now()
            formula.save()
        return formula

    def _validate_locked_group_overlap(self, group, validated_data):
        if validated_data.get("status") != MarketFormula.Status.VALIDATED:
            return
        valid_from = validated_data.get("valid_from")
        valid_to = validated_data.get("valid_to")
        for other in group.formulas.filter(status=MarketFormula.Status.VALIDATED):
            overlaps = (valid_to is None or other.valid_from is None or other.valid_from <= valid_to) and (other.valid_to is None or valid_from is None or valid_from <= other.valid_to)
            if overlaps:
                raise serializers.ValidationError({"status": "Une seule formule VALIDATED peut être applicable à une même période."})

    @transaction.atomic
    def update(self, instance, validated_data):
        terms = validated_data.pop("terms", None)
        requested_status = validated_data.pop("status", instance.status)
        validating = requested_status == MarketFormula.Status.VALIDATED and instance.status != MarketFormula.Status.VALIDATED
        if validating:
            from django.utils import timezone
            validated_data["validated_at"] = timezone.now()
        formula = instance
        for field, value in validated_data.items():
            setattr(formula, field, value)
        if not validating:
            formula.status = requested_status
        formula.save()
        if terms is not None:
            formula.terms.all().delete()
            for term in terms:
                FormulaTerm.objects.create(formula=formula, **term)
        if validating:
            formula.status = requested_status
            formula.save()
        return formula


class RevisionGroupSerializer(serializers.ModelSerializer):
    formulas = MarketFormulaSerializer(many=True, read_only=True)

    class Meta:
        model = RevisionGroup
        fields = ["id", "market", "code", "name", "description", "sort_order", "active", "notes", "created_at", "updated_at", "formulas"]
        read_only_fields = ["id", "market", "created_at", "updated_at", "formulas"]

    def validate_code(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le code du groupe est obligatoire.")
        return value

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom du groupe est obligatoire.")
        return value
        return value
