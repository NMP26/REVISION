from django.urls import path

from .views import AuthorityDetailView, AuthorityListCreateView

urlpatterns = [
    path("authorities/", AuthorityListCreateView.as_view(), name="authority-list-create"),
    path("authorities/<uuid:authority_id>/", AuthorityDetailView.as_view(), name="authority-detail"),
]
