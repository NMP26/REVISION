from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import error_response

from .models import Company, Membership
from .permissions import can_update, get_membership
from .serializers import CompanySerializer


def serializer_errors(serializer):
    return {field: [str(error) for error in errors] for field, errors in serializer.errors.items()}


class CompanyListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        companies = Company.objects.filter(memberships__user=request.user, memberships__active=True).distinct()
        return Response(CompanySerializer(companies, many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request):
        serializer = CompanySerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        company = serializer.save()
        Membership.objects.create(user=request.user, company=company, role=Membership.Role.OWNER, active=True)
        return Response(CompanySerializer(company, context={"request": request}).data, status=status.HTTP_201_CREATED)


class CompanyDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_company(self, company_id):
        return Company.objects.filter(id=company_id).first()

    def get(self, request, company_id):
        company = self.get_company(company_id)
        if company is None:
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if get_membership(request.user, company) is None:
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(CompanySerializer(company, context={"request": request}).data)

    def put(self, request, company_id):
        return self._update(request, company_id, partial=False)

    def patch(self, request, company_id):
        return self._update(request, company_id, partial=True)

    def _update(self, request, company_id, partial):
        company = self.get_company(company_id)
        if company is None:
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        role = get_membership(request.user, company)
        if role is None:
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update(role):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = CompanySerializer(company, data=request.data, partial=partial, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        serializer.save()
        return Response(CompanySerializer(company, context={"request": request}).data)
