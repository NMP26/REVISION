from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import error_response
from companies.models import Company
from companies.permissions import can_update, get_membership

from .models import Consortium
from .permissions import can_manage_consortium, can_read_consortium
from .serializers import ConsortiumSerializer


def errors(serializer):
    return {key: [str(item) for item in value] for key, value in serializer.errors.items()}


def accessible(user):
    if user.is_superuser:
        return Consortium.objects.all()
    return Consortium.objects.filter(members__company__memberships__user=user, members__company__memberships__active=True, members__active=True).distinct()


class ConsortiumListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ConsortiumSerializer(accessible(request.user).prefetch_related("members__company"), many=True, context={"request": request}).data)

    def post(self, request):
        owner = Company.objects.filter(id=request.data.get("owner_company"), status=Company.Status.ACTIVE).first()
        if owner is None or not can_update(get_membership(request.user, owner)):
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        serializer = ConsortiumSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", errors(serializer))
        consortium = serializer.save()
        return Response(ConsortiumSerializer(consortium, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ConsortiumDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_consortium(self, request, consortium_id):
        return accessible(request.user).filter(id=consortium_id).prefetch_related("members__company").first()

    def get(self, request, consortium_id):
        consortium = self.get_consortium(request, consortium_id)
        if consortium is None:
            return error_response("NOT_FOUND", "Groupement introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(ConsortiumSerializer(consortium).data)

    def patch(self, request, consortium_id):
        consortium = self.get_consortium(request, consortium_id)
        if consortium is None:
            return error_response("NOT_FOUND", "Groupement introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_manage_consortium(request.user, consortium):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = ConsortiumSerializer(consortium, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", errors(serializer))
        serializer.save()
        return Response(ConsortiumSerializer(consortium).data)

    def put(self, request, consortium_id):
        consortium = self.get_consortium(request, consortium_id)
        if consortium is None:
            return error_response("NOT_FOUND", "Groupement introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_manage_consortium(request.user, consortium):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = ConsortiumSerializer(consortium, data=request.data, partial=False, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", errors(serializer))
        serializer.save()
        return Response(ConsortiumSerializer(consortium).data)
