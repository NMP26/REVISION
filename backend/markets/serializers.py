from decimal import Decimal

from rest_framework import serializers

from companies.models import Company
from authorities.models import ContractingAuthority
from consortia.models import Consortium
from consortia.permissions import can_manage_consortium
from companies.permissions import get_membership

from .models import Market, MarketLot


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
