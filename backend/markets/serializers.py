from decimal import Decimal

from rest_framework import serializers

from companies.models import Company

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


class MarketSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    company_detail = CompanySummarySerializer(source="company", read_only=True)
    current_user_role = serializers.SerializerMethodField()
    lots_count = serializers.IntegerField(source="lots.count", read_only=True)

    class Meta:
        model = Market
        fields = [
            "id", "company", "company_detail", "market_number", "contracting_authority", "subject",
            "amount_ht", "vat_rate", "date_limite_remise_offres", "date_ouverture_plis", "date_signature",
            "date_os_commencement", "contract_duration_value", "contract_duration_unit", "formula_structure",
            "status", "notes", "created_at", "updated_at", "current_user_role", "lots_count",
        ]
        read_only_fields = ["id", "company_detail", "created_at", "updated_at", "current_user_role", "lots_count"]

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
        membership = market.company.memberships.filter(user=request.user, active=True).first()
        return membership.role if membership else None

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
