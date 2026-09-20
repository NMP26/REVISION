from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from companies.models import Company

from .models import Consortium, ConsortiumMember


class ConsortiumMemberSerializer(serializers.ModelSerializer):
    company_detail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ConsortiumMember
        fields = ["id", "company", "company_detail", "role", "share_percent", "sort_order", "active"]
        read_only_fields = ["id", "company_detail"]

    def get_company_detail(self, member):
        return {"id": str(member.company_id), "raison_sociale": member.company.raison_sociale}


def validate_members(members):
    if len(members) < 2:
        raise serializers.ValidationError("Un groupement doit comporter au moins deux membres actifs.")
    if sum(1 for member in members if member.get("active", True)) < 2:
        raise serializers.ValidationError("Un groupement doit comporter au moins deux membres actifs.")
    active = [member for member in members if member.get("active", True)]
    if sum(1 for member in active if member.get("role") == ConsortiumMember.Role.MANDATAIRE) != 1:
        raise serializers.ValidationError("Un seul mandataire actif est autorisé.")
    companies = [str(member.get("company")) for member in active]
    if len(companies) != len(set(companies)):
        raise serializers.ValidationError("Une société ne peut apparaître qu’une seule fois dans le groupement.")
    shares = [member.get("share_percent") for member in active]
    if all(share is not None for share in shares) and sum(shares, Decimal("0")) != Decimal("100.00"):
        raise serializers.ValidationError("La somme des quotes-parts renseignées doit être exactement 100,00 %.")
    return members


class ConsortiumSerializer(serializers.ModelSerializer):
    members = ConsortiumMemberSerializer(many=True)

    class Meta:
        model = Consortium
        fields = ["id", "owner_company", "name", "consortium_type", "active", "notes", "members", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        value = " ".join(value.strip().split())
        if not value:
            raise serializers.ValidationError("La dénomination est obligatoire.")
        return value

    def validate(self, attrs):
        if self.instance is not None and "owner_company" in attrs and attrs["owner_company"].pk != self.instance.owner_company_id:
            raise serializers.ValidationError({"owner_company": "La société propriétaire est immuable après création."})
        members = attrs.get("members")
        if members is None and self.instance is not None:
            members = list(self.instance.members.filter(active=True).values("company", "role", "share_percent", "sort_order", "active"))
        validate_members(members or [])
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        members = validated_data.pop("members")
        consortium = Consortium.objects.create(created_by=self.context["request"].user, **validated_data)
        ConsortiumMember.objects.bulk_create([ConsortiumMember(consortium=consortium, **member) for member in members])
        return consortium

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = Consortium.objects.select_for_update().get(pk=instance.pk)
        members = validated_data.pop("members", None)
        instance = super().update(instance, validated_data)
        if members is not None:
            incoming_companies = {member["company"].pk for member in members}
            instance.members.filter(active=True).exclude(company_id__in=incoming_companies).update(active=False)
            for member in members:
                ConsortiumMember.objects.update_or_create(
                    consortium=instance,
                    company=member["company"],
                    defaults={"role": member["role"], "share_percent": member.get("share_percent"), "sort_order": member.get("sort_order", 0), "active": member.get("active", True)},
                )
        return instance
