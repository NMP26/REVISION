from django.urls import path

from .views import (
    MarketDetailView, MarketFormulaDetailView, MarketFormulaListCreateView,
    MarketListCreateView, MarketLotDetailView, MarketLotListCreateView,
    RevisionGroupDetailView, RevisionGroupListCreateView,
    FormulaTemplateDetailView, FormulaTemplateListView, MarketFormulaFromTemplateView,
    PriceAssignmentView, PriceItemDetailView, PriceItemListCreateView, PriceMatrixView,
    PriceScheduleDetailView, PriceScheduleView, RevisionApplicationView,
)

urlpatterns = [
    path("markets/", MarketListCreateView.as_view(), name="market-list-create"),
    path("markets/<uuid:market_id>/", MarketDetailView.as_view(), name="market-detail"),
    path("markets/<uuid:market_id>/lots/", MarketLotListCreateView.as_view(), name="market-lot-list-create"),
    path("markets/<uuid:market_id>/lots/<uuid:lot_id>/", MarketLotDetailView.as_view(), name="market-lot-detail"),
    path("markets/<uuid:market_id>/revision-application/", RevisionApplicationView.as_view(), name="revision-application"),
    path("markets/<uuid:market_id>/price-schedule/", PriceScheduleView.as_view(), name="price-schedule"),
    path("markets/<uuid:market_id>/price-schedule/detail/", PriceScheduleDetailView.as_view(), name="price-schedule-detail"),
    path("markets/<uuid:market_id>/price-schedule/items/", PriceItemListCreateView.as_view(), name="price-item-list-create"),
    path("markets/<uuid:market_id>/price-schedule/items/<uuid:item_id>/", PriceItemDetailView.as_view(), name="price-item-detail"),
    path("markets/<uuid:market_id>/price-schedule/matrix/", PriceMatrixView.as_view(), name="price-matrix"),
    path("markets/<uuid:market_id>/price-schedule/assignments/", PriceAssignmentView.as_view(), name="price-assignment"),
    path("markets/<uuid:market_id>/revision-groups/", RevisionGroupListCreateView.as_view(), name="revision-group-list-create"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/", RevisionGroupDetailView.as_view(), name="revision-group-detail"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/formulas/", MarketFormulaListCreateView.as_view(), name="market-formula-list-create"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/formulas/from-template/", MarketFormulaFromTemplateView.as_view(), name="market-formula-from-template"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/formulas/<uuid:formula_id>/", MarketFormulaDetailView.as_view(), name="market-formula-detail"),
    path("formula-templates/", FormulaTemplateListView.as_view(), name="formula-template-list"),
    path("formula-templates/<uuid:template_id>/", FormulaTemplateDetailView.as_view(), name="formula-template-detail"),
]
