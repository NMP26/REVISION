from rest_framework import serializers

from .models import Company

MAX_LOGO_BYTES = 5 * 1024 * 1024


class CompanySerializer(serializers.ModelSerializer):
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id", "raison_sociale", "forme_juridique", "capital_social", "ice", "if_fiscal", "rc", "cnss",
            "adresse_complete", "ville", "telephone", "email", "site_web", "representant_nom",
            "representant_prenom", "representant_fonction", "logo", "notes", "status", "created_at",
            "updated_at", "archived_at",
            "current_user_role",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "archived_at", "current_user_role"]

    def get_current_user_role(self, company):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        if request.user.is_superuser:
            return "OWNER"
        membership = company.memberships.filter(user=request.user, active=True).first()
        return membership.role if membership else None

    def validate_logo(self, value):
        if value.size > MAX_LOGO_BYTES:
            raise serializers.ValidationError("Le logo ne doit pas dépasser 5 MiB.")
        return value

    def validate_raison_sociale(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Ce champ est obligatoire.")
        return value
