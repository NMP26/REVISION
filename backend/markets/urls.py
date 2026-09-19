from django.urls import path

from .views import MarketDetailView, MarketListCreateView, MarketLotDetailView, MarketLotListCreateView

urlpatterns = [
    path("markets/", MarketListCreateView.as_view(), name="market-list-create"),
    path("markets/<uuid:market_id>/", MarketDetailView.as_view(), name="market-detail"),
    path("markets/<uuid:market_id>/lots/", MarketLotListCreateView.as_view(), name="market-lot-list-create"),
    path("markets/<uuid:market_id>/lots/<uuid:lot_id>/", MarketLotDetailView.as_view(), name="market-lot-detail"),
]
