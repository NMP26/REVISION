from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import error_response
from companies.models import Company
from companies.permissions import can_update, get_membership

from .models import Market, MarketLot
from .permissions import can_update_market
from .serializers import MarketLotSerializer, MarketSerializer


def serializer_errors(serializer):
    return {field: [str(error) for error in errors] for field, errors in serializer.errors.items()}


def accessible_markets(user):
    queryset = Market.objects.select_related("company").prefetch_related("lots")
    if user.is_superuser:
        return queryset
    return queryset.filter(company__memberships__user=user, company__memberships__active=True).distinct()


class MarketListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        markets = accessible_markets(request.user)
        return Response(MarketSerializer(markets, many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request):
        serializer = MarketSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        company = serializer.validated_data["company"]
        if not can_update(get_membership(request.user, company)):
            return error_response("NOT_FOUND", "Société introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        try:
            market = serializer.save()
        except IntegrityError as exc:
            if "uniq_market_company_number" in str(exc):
                return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"market_number": ["Ce numéro existe déjà pour cette société."]})
            raise
        return Response(MarketSerializer(market, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MarketDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_market(self, request, market_id):
        return accessible_markets(request.user).filter(id=market_id).first()

    def get(self, request, market_id):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(MarketSerializer(market, context={"request": request}).data)

    def patch(self, request, market_id):
        return self._update(request, market_id, partial=True)

    def _update(self, request, market_id, partial):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = MarketSerializer(market, data=request.data, partial=partial, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            serializer.save()
        except IntegrityError as exc:
            if "uniq_market_company_number" in str(exc):
                return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"market_number": ["Ce numéro existe déjà pour cette société."]})
            raise
        return Response(MarketSerializer(market, context={"request": request}).data)


class MarketLotListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_market(self, request, market_id):
        return accessible_markets(request.user).filter(id=market_id).first()

    def get(self, request, market_id):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        lots = market.lots.all()
        return Response(MarketLotSerializer(lots, many=True).data)

    @transaction.atomic
    def post(self, request, market_id):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = MarketLotSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            lot = serializer.save(market=market)
        except IntegrityError as exc:
            if "uniq_marketlot_market_number" in str(exc):
                return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"lot_number": ["Ce numéro existe déjà pour ce marché."]})
            raise
        return Response(MarketLotSerializer(lot).data, status=status.HTTP_201_CREATED)


class MarketLotDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_market(self, request, market_id):
        return accessible_markets(request.user).filter(id=market_id).first()

    def get_lot(self, request, market_id, lot_id):
        market = self.get_market(request, market_id)
        if market is None:
            return None, None
        return market, MarketLot.objects.filter(market=market, id=lot_id).first()

    def get(self, request, market_id, lot_id):
        market, lot = self.get_lot(request, market_id, lot_id)
        if market is None or lot is None:
            return error_response("NOT_FOUND", "Lot introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(MarketLotSerializer(lot).data)

    def patch(self, request, market_id, lot_id):
        market, lot = self.get_lot(request, market_id, lot_id)
        if market is None or lot is None:
            return error_response("NOT_FOUND", "Lot introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = MarketLotSerializer(lot, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            serializer.save()
        except IntegrityError as exc:
            if "uniq_marketlot_market_number" in str(exc):
                return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"lot_number": ["Ce numéro existe déjà pour ce marché."]})
            raise
        return Response(MarketLotSerializer(lot).data)
