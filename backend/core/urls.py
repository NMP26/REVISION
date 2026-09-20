from django.urls import path
from accounts.views import CsrfView, CurrentUserView, LoginView, LogoutView, PasswordChangeView
from companies.views import CompanyDetailView, CompanyListCreateView
from authorities.urls import urlpatterns as authority_urlpatterns
from consortia.urls import urlpatterns as consortium_urlpatterns
from markets.urls import urlpatterns as market_urlpatterns
from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/csrf/", CsrfView.as_view(), name="auth-csrf"),
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", CurrentUserView.as_view(), name="auth-me"),
    path("auth/password/change/", PasswordChangeView.as_view(), name="auth-password-change"),
    path("companies/", CompanyListCreateView.as_view(), name="company-list-create"),
    path("companies/<uuid:company_id>/", CompanyDetailView.as_view(), name="company-detail"),
]

urlpatterns += market_urlpatterns
urlpatterns += authority_urlpatterns
urlpatterns += consortium_urlpatterns
