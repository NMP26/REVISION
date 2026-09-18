from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CurrentUserSerializer


def error_response(code, message, fields=None, http_status=status.HTTP_400_BAD_REQUEST):
    payload = {"code": code, "message": message}
    if fields:
        payload["fields"] = fields
    return Response(payload, status=http_status)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = request.data.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is None or not user.is_active:
            return error_response("INVALID_CREDENTIALS", "Identifiants invalides.", http_status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        return Response(CurrentUserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")
        if not request.user.check_password(current_password):
            return error_response("INVALID_PASSWORD", "Le mot de passe actuel est incorrect.", http_status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(new_password, str) or len(new_password) < 8:
            return error_response("VALIDATION_ERROR", "Les données sont invalides.", {"new_password": ["Le mot de passe doit contenir au moins 8 caractères."]})
        request.user.set_password(new_password)
        request.user.save(update_fields=["password", "updated_at"])
        update_session_auth_hash(request, request.user)
        return Response({"message": "Mot de passe modifié."})
