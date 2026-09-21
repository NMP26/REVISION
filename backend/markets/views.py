from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import error_response
from companies.models import Company
from companies.permissions import can_read_global_resources, can_update, get_membership

from .models import FormulaTemplate, Market, MarketLot, PriceItem, PriceSchedule
from .permissions import can_update_market
from .serializers import (
    FormulaTemplateSerializer, MarketFormulaSerializer, MarketLotSerializer, MarketSerializer,
    PriceItemSerializer, PriceScheduleSerializer, RevisionApplicationSerializer,
    RevisionGroupSerializer,
)
from .services import bulk_assign_price_items, copy_formula_template, create_price_item, create_price_schedule, set_revision_application, update_price_item
from .models import MarketFormula, RevisionGroup


def serializer_errors(serializer):
    return {field: [str(error) for error in errors] for field, errors in serializer.errors.items()}


def accessible_markets(user):
    queryset = Market.objects.select_related("company", "holder_company", "consortium", "authority").prefetch_related("lots", "consortium__members__company")
    if user.is_superuser:
        return queryset
    return queryset.filter(Q(company__memberships__user=user, company__memberships__active=True) | Q(consortium__members__company__memberships__user=user, consortium__members__company__memberships__active=True, consortium__members__active=True)).distinct()


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


def accessible_market(user, market_id):
    return accessible_markets(user).filter(id=market_id).first()


class RevisionApplicationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        group = market.global_revision_group
        formula = None
        if group is not None:
            formula = group.formulas.exclude(status=MarketFormula.Status.INACTIVE).order_by("-version_number").first()
        return Response({
            "revision_application_mode": market.revision_application_mode,
            "global_revision_group": group.id if group else None,
            "global_formula": MarketFormulaSerializer(formula, context={"request": request}).data if formula else None,
            "price_schedule_required": market.revision_application_mode == Market.RevisionApplicationMode.PRICE_ASSIGNMENT,
            "updated_at": market.updated_at,
        })

    def post(self, request, market_id):
        return self._save(request, market_id)

    def patch(self, request, market_id):
        return self._save(request, market_id)

    def _save(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = RevisionApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            saved = set_revision_application(
                market_id=market.id,
                mode=serializer.validated_data["revision_application_mode"],
                global_revision_group_id=getattr(serializer.validated_data.get("global_revision_group"), "pk", serializer.validated_data.get("global_revision_group")),
                expected_updated_at=serializer.validated_data.get("expected_updated_at"),
            )
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "La configuration de révision est invalide.", {"revision": exc.messages})
        return self.get(request, saved.id)


class PriceScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    def get_market(self, request, market_id):
        return accessible_market(request.user, market_id)

    def get(self, request, market_id):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        schedule = PriceSchedule.objects.filter(market=market).first()
        return Response({
            "required": market.revision_application_mode == Market.RevisionApplicationMode.PRICE_ASSIGNMENT,
            "schedule": PriceScheduleSerializer(schedule).data if schedule else None,
        })

    @transaction.atomic
    def post(self, request, market_id):
        market = self.get_market(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = PriceScheduleSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            schedule = create_price_schedule(market=market, validated_data=serializer.validated_data)
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "Le bordereau est invalide.", {"price_schedule": exc.messages})
        return Response(PriceScheduleSerializer(schedule).data, status=status.HTTP_201_CREATED)


class PriceScheduleDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_schedule(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        return market, PriceSchedule.objects.filter(market=market).first()

    def patch(self, request, market_id):
        market, schedule = self.get_schedule(request, market_id)
        if market is None or schedule is None:
            return error_response("NOT_FOUND", "Bordereau introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = PriceScheduleSerializer(schedule, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        with transaction.atomic():
            schedule = PriceSchedule.objects.select_for_update().get(pk=schedule.pk)
            for field, value in serializer.validated_data.items():
                setattr(schedule, field, value)
            schedule.change_version += 1
            schedule.save(update_fields=[*serializer.validated_data.keys(), "change_version", "updated_at"])
        return Response(PriceScheduleSerializer(schedule).data)


class PriceItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_schedule(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        return market, PriceSchedule.objects.filter(market=market).first()

    def get(self, request, market_id):
        market, schedule = self.get_schedule(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if schedule is None:
            return Response({"count": 0, "next": None, "previous": None, "results": []})
        items = schedule.items.select_related("lot", "revision_group").all()
        query = request.query_params.get("q", "").strip()
        if query:
            items = items.filter(Q(price_number__icontains=query) | Q(designation__icontains=query))
        if request.query_params.get("lot"):
            items = items.filter(lot_id=request.query_params["lot"])
        if request.query_params.get("classification_status"):
            items = items.filter(classification_status=request.query_params["classification_status"])
        if request.query_params.get("revision_group"):
            items = items.filter(revision_group_id=request.query_params["revision_group"])
        if request.query_params.get("active") in {"true", "false"}:
            items = items.filter(active=request.query_params["active"] == "true")
        try:
            page = max(int(request.query_params.get("page", 1)), 1)
            page_size = min(max(int(request.query_params.get("page_size", 50)), 1), 100)
        except ValueError:
            return error_response("VALIDATION_ERROR", "La pagination est invalide.", {"page": ["page et page_size doivent être numériques."]})
        total = items.count()
        start, end = (page - 1) * page_size, page * page_size
        return Response({"count": total, "next": page + 1 if end < total else None, "previous": page - 1 if page > 1 else None, "results": PriceItemSerializer(items[start:end], many=True).data})

    @transaction.atomic
    def post(self, request, market_id):
        market, schedule = self.get_schedule(request, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if schedule is None:
            return error_response("NOT_FOUND", "Bordereau introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = PriceItemSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            item = create_price_item(schedule=schedule, validated_data=serializer.validated_data)
        except (ValidationError, IntegrityError) as exc:
            return error_response("VALIDATION_ERROR", "Le prix est invalide ou existe déjà.", {"price_item": getattr(exc, "messages", [str(exc)])})
        return Response(PriceItemSerializer(item).data, status=status.HTTP_201_CREATED)


class PriceItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_item(self, request, market_id, item_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        item = PriceItem.objects.select_related("price_schedule", "lot", "revision_group").filter(id=item_id, price_schedule__market=market).first()
        return market, item

    def get(self, request, market_id, item_id):
        market, item = self.get_item(request, market_id, item_id)
        if market is None or item is None:
            return error_response("NOT_FOUND", "Prix introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(PriceItemSerializer(item).data)

    @transaction.atomic
    def patch(self, request, market_id, item_id):
        market, item = self.get_item(request, market_id, item_id)
        if market is None or item is None:
            return error_response("NOT_FOUND", "Prix introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = PriceItemSerializer(item, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            item = update_price_item(item=item, validated_data=serializer.validated_data)
        except (ValidationError, IntegrityError) as exc:
            return error_response("VALIDATION_ERROR", "Le prix est invalide ou existe déjà.", {"price_item": getattr(exc, "messages", [str(exc)])})
        return Response(PriceItemSerializer(item).data)


class PriceMatrixView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        schedule = PriceSchedule.objects.filter(market=market).first()
        groups = market.revision_groups.filter(active=True).prefetch_related("formulas__terms")
        items = schedule.items.select_related("lot", "revision_group").all() if schedule else PriceItem.objects.none()
        return Response({
            "mode": market.revision_application_mode,
            "price_schedule_required": market.revision_application_mode == Market.RevisionApplicationMode.PRICE_ASSIGNMENT,
            "formulas": [{"id": group.id, "name": group.name, "code": group.code, "formulas": MarketFormulaSerializer(group.formulas.exclude(status=MarketFormula.Status.INACTIVE), many=True).data} for group in groups],
            "items": PriceItemSerializer(items, many=True).data,
        })


class PriceAssignmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        if market.revision_application_mode != Market.RevisionApplicationMode.PRICE_ASSIGNMENT:
            return error_response("VALIDATION_ERROR", "L'affectation des prix n'est disponible que pour un marché en mode Plusieurs formules.", http_status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        price_item_ids = data.get("price_item_ids")
        if price_item_ids is not None and not isinstance(price_item_ids, list):
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"price_item_ids": ["La valeur doit être une liste."]})
        try:
            result = bulk_assign_price_items(
                market=market,
                action=str(data.get("action") or "").upper(),
                revision_group_id=data.get("revision_group_id"),
                price_item_ids=price_item_ids,
                filters=data.get("filter") or {},
                expected_version=data.get("expected_version"),
            )
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "L'affectation est invalide.", {"assignment": exc.messages})
        return Response(result)


class RevisionGroupListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        groups = market.revision_groups.prefetch_related("formulas__terms")
        return Response(RevisionGroupSerializer(groups, many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request, market_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = RevisionGroupSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            group = serializer.save(market=market)
        except IntegrityError:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"code": ["Ce code existe déjà pour ce marché."]})
        return Response(RevisionGroupSerializer(group, context={"request": request}).data, status=status.HTTP_201_CREATED)


class RevisionGroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_group(self, request, market_id, group_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        return market, market.revision_groups.filter(id=group_id).prefetch_related("formulas__terms").first()

    def get(self, request, market_id, group_id):
        market, group = self.get_group(request, market_id, group_id)
        if market is None or group is None:
            return error_response("NOT_FOUND", "Groupe de révision introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(RevisionGroupSerializer(group, context={"request": request}).data)

    def patch(self, request, market_id, group_id):
        market, group = self.get_group(request, market_id, group_id)
        if market is None or group is None:
            return error_response("NOT_FOUND", "Groupe de révision introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = RevisionGroupSerializer(group, data=request.data, partial=True, context={"request": request})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            serializer.save()
        except IntegrityError:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"code": ["Ce code existe déjà pour ce marché."]})
        return Response(RevisionGroupSerializer(group, context={"request": request}).data)


class MarketFormulaListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_group(self, request, market_id, group_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        return market, market.revision_groups.filter(id=group_id).first()

    def get(self, request, market_id, group_id):
        market, group = self.get_group(request, market_id, group_id)
        if market is None or group is None:
            return error_response("NOT_FOUND", "Groupe de révision introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(MarketFormulaSerializer(group.formulas.prefetch_related("terms"), many=True, context={"request": request}).data)

    @transaction.atomic
    def post(self, request, market_id, group_id):
        market, group = self.get_group(request, market_id, group_id)
        if market is None or group is None:
            return error_response("NOT_FOUND", "Groupe de révision introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = MarketFormulaSerializer(data=request.data, context={"request": request, "revision_group": group})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            formula = serializer.save()
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"formula": exc.messages})
        except IntegrityError:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"version_number": ["Cette version existe déjà pour ce groupe."]})
        return Response(MarketFormulaSerializer(formula, context={"request": request}).data, status=status.HTTP_201_CREATED)


class MarketFormulaDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_formula(self, request, market_id, group_id, formula_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return None, None
        formula = MarketFormula.objects.filter(revision_group__market=market, revision_group_id=group_id, id=formula_id).prefetch_related("terms").first()
        return market, formula

    def get(self, request, market_id, group_id, formula_id):
        market, formula = self.get_formula(request, market_id, group_id, formula_id)
        if market is None or formula is None:
            return error_response("NOT_FOUND", "Formule introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(MarketFormulaSerializer(formula, context={"request": request}).data)

    @transaction.atomic
    def patch(self, request, market_id, group_id, formula_id):
        market, formula = self.get_formula(request, market_id, group_id, formula_id)
        if market is None or formula is None:
            return error_response("NOT_FOUND", "Formule introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        serializer = MarketFormulaSerializer(formula, data=request.data, partial=True, context={"request": request, "revision_group": formula.revision_group})
        if not serializer.is_valid():
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", serializer_errors(serializer))
        try:
            serializer.save()
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"formula": exc.messages})
        return Response(MarketFormulaSerializer(formula, context={"request": request}).data)


class FormulaTemplateListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not can_read_global_resources(request.user):
            return error_response("PERMISSION_DENIED", "Une Membership active est requise.", http_status=status.HTTP_403_FORBIDDEN)
        templates = FormulaTemplate.objects.filter(scope=FormulaTemplate.Scope.GLOBAL).prefetch_related("terms")
        query = request.query_params.get("q", "").strip()
        if query:
            templates = templates.filter(
                Q(code__icontains=query) | Q(designation__icontains=query) | Q(domain__icontains=query) | Q(source_title__icontains=query)
            )
        requested_status = request.query_params.get("status")
        if requested_status:
            templates = templates.filter(status=requested_status)
        return Response(FormulaTemplateSerializer(templates, many=True, context={"request": request}).data)


class FormulaTemplateDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, template_id):
        if not can_read_global_resources(request.user):
            return error_response("PERMISSION_DENIED", "Une Membership active est requise.", http_status=status.HTTP_403_FORBIDDEN)
        template = FormulaTemplate.objects.filter(id=template_id, scope=FormulaTemplate.Scope.GLOBAL).prefetch_related("terms").first()
        if template is None:
            return error_response("NOT_FOUND", "Template introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        return Response(FormulaTemplateSerializer(template, context={"request": request}).data)


class MarketFormulaFromTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, market_id, group_id):
        market = accessible_market(request.user, market_id)
        if market is None:
            return error_response("NOT_FOUND", "Marché introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        if not can_update_market(request.user, market):
            return error_response("PERMISSION_DENIED", "Action non autorisée.", http_status=status.HTTP_403_FORBIDDEN)
        template_id = request.data.get("template_id")
        if not template_id or set(request.data) != {"template_id"}:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"template_id": ["Le template_id est obligatoire."]})
        if not RevisionGroup.objects.filter(id=group_id, market=market).exists():
            return error_response("NOT_FOUND", "Groupe de révision introuvable.", http_status=status.HTTP_404_NOT_FOUND)
        try:
            formula = copy_formula_template(template_id=template_id, revision_group_id=group_id, user=request.user)
        except ValidationError as exc:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"template": exc.messages})
        return Response(MarketFormulaSerializer(formula, context={"request": request}).data, status=status.HTTP_201_CREATED)
