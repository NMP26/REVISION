import logging

from django.http import JsonResponse


logger = logging.getLogger(__name__)


class ApiInternalErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            if request.path.startswith("/api/"):
                logger.exception("Unhandled API exception")
                return JsonResponse(
                    {"code": "INTERNAL_ERROR", "message": "Une erreur interne est survenue."},
                    status=500,
                )
            raise
