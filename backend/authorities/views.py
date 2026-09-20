from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import error_response
from companies.models import Company
from companies.permissions import can_update, get_membership

from .models import AuthorityAlias, CompanyAuthority, ContractingAuthority, normalize_authority
from .serializers import AuthoritySerializer


def errors(serializer):
    return {key: [str(item) for item in value] for key, value in serializer.errors.items()}


class AuthorityListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = normalize_authority(request.query_params.get("q", ""))
        authorities = ContractingAuthority.objects.filter(active=True, company_links__company__memberships__user=request.user, company_links__company__memberships__active=True).distinct()
        if query:
            authorities = authorities.filter(Q(normalized_name__icontains=query) | Q(short_name__icontains=query) | Q(aliases__normalized_alias__icontains=query, aliases__active=True)).distinct()
        return Response(AuthoritySerializer(authorities.order_by("name"), many=True).data)

    def post(self, request):
        company_id = request.data.get("company")
        company = Company.objects.filter(id=company_id, status=Company.Status.ACTIVE).first()
        if company is None or not can_update(get_membership(request.user, company)):
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        serializer = AuthoritySerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", errors(serializer))
        authority = serializer.save()
        return Response(AuthoritySerializer(authority).data, status=status.HTTP_201_CREATED)


class AuthorityDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, authority_id):
        authority = ContractingAuthority.objects.filter(id=authority_id, company_links__company__memberships__user=request.user, company_links__company__memberships__active=True).distinct().first()
        if authority is None:
            return error_response("NOT_FOUND", "Maître d’ouvrage introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not request.user.is_superuser and not any(can_update(get_membership(request.user, link.company)) for link in authority.company_links.select_related("company")):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = AuthoritySerializer(authority, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", errors(serializer))
        serializer.save()
        return Response(AuthoritySerializer(authority).data)
