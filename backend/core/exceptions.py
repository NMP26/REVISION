from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    detail = response.data.get("detail", "Une erreur est survenue.") if hasattr(response.data, "get") else "Une erreur est survenue."
    code = "REQUEST_ERROR"
    if response.status_code == 401:
        code = "AUTHENTICATION_REQUIRED"
    elif response.status_code == 403:
        code = "PERMISSION_DENIED"
    elif response.status_code == 404:
        code = "NOT_FOUND"
    elif response.status_code == 400:
        code = "VALIDATION_ERROR"
    fields = None
    if response.status_code == 403 and str(detail).lower().startswith("csrf failed"):
        code = "CSRF_FAILED"
        detail = "La vérification CSRF a échoué."
    if response.status_code == 400 and hasattr(response.data, "items"):
        fields = {key: [str(item) for item in value] if isinstance(value, list) else [str(value)] for key, value in response.data.items() if key != "detail"}
    payload = {"code": code, "message": str(detail)}
    if fields:
        payload["fields"] = fields
    response.data = payload
    return response
