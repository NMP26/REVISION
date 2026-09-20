from django.urls import path

from .views import (
    MarketDetailView, MarketFormulaDetailView, MarketFormulaListCreateView,
    MarketListCreateView, MarketLotDetailView, MarketLotListCreateView,
    RevisionGroupDetailView, RevisionGroupListCreateView,
)

urlpatterns = [
    path("markets/", MarketListCreateView.as_view(), name="market-list-create"),
    path("markets/<uuid:market_id>/", MarketDetailView.as_view(), name="market-detail"),
    path("markets/<uuid:market_id>/lots/", MarketLotListCreateView.as_view(), name="market-lot-list-create"),
    path("markets/<uuid:market_id>/lots/<uuid:lot_id>/", MarketLotDetailView.as_view(), name="market-lot-detail"),
    path("markets/<uuid:market_id>/revision-groups/", RevisionGroupListCreateView.as_view(), name="revision-group-list-create"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/", RevisionGroupDetailView.as_view(), name="revision-group-detail"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/formulas/", MarketFormulaListCreateView.as_view(), name="market-formula-list-create"),
    path("markets/<uuid:market_id>/revision-groups/<uuid:group_id>/formulas/<uuid:formula_id>/", MarketFormulaDetailView.as_view(), name="market-formula-detail"),
]
