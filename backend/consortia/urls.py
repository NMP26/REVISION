from django.urls import path

from .views import ConsortiumDetailView, ConsortiumListCreateView

urlpatterns = [
    path("consortia/", ConsortiumListCreateView.as_view(), name="consortium-list-create"),
    path("consortia/<uuid:consortium_id>/", ConsortiumDetailView.as_view(), name="consortium-detail"),
]
