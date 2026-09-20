from rest_framework import serializers

from .models import CompanyAuthority, ContractingAuthority, normalize_authority


class AuthoritySerializer(serializers.ModelSerializer):
    company = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ContractingAuthority
        fields = ["id", "name", "short_name", "active", "company", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        value = " ".join(value.strip().split())
        if not value:
            raise serializers.ValidationError("Le nom officiel est obligatoire.")
        if ContractingAuthority.objects.filter(normalized_name=normalize_authority(value)).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Ce maître d’ouvrage existe déjà. Aucun doublon n’a été fusionné.")
        return value

    def create(self, validated_data):
        company_id = validated_data.pop("company", None)
        authority = ContractingAuthority.objects.create(**validated_data)
        if company_id:
            CompanyAuthority.objects.create(company_id=company_id, authority=authority)
        return authority
