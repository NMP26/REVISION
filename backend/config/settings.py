import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_ENV = os.environ.get("DJANGO_ENV", "").lower()
DJANGO_SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "").strip()
if not DJANGO_SECRET_KEY and DJANGO_ENV not in {"development", "local", "test"}:
    raise RuntimeError("DJANGO_SECRET_KEY est obligatoire hors développement local.")
SECRET_KEY = DJANGO_SECRET_KEY or "local-development-only-key"
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [h.strip() for h in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "rest_framework",
    "axes",
    "accounts",
    "companies",
    "authorities",
    "consortia",
    "markets",
    "core",
]
MIDDLEWARE = [
    "core.middleware.ApiInternalErrorMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "revision_prix"),
    "USER": os.environ.get("POSTGRES_USER", "revision_prix"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
    "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
    "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    "CONN_MAX_AGE": 60,
}}
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = DJANGO_ENV not in {"development", "local", "test"}
SESSION_COOKIE_SAMESITE = os.environ.get("DJANGO_SESSION_COOKIE_SAMESITE", "Lax")
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
CSRF_COOKIE_SAMESITE = SESSION_COOKIE_SAMESITE
CSRF_COOKIE_HTTPONLY = False
AXES_FAILURE_LIMIT = int(os.environ.get("AXES_FAILURE_LIMIT", "5"))
AXES_COOLOFF_TIME = float(os.environ.get("AXES_COOLOFF_TIME_HOURS", "1"))
AXES_RESET_ON_SUCCESS = True
AXES_ENABLED = os.environ.get("AXES_ENABLED", "True").lower() in {"1", "true", "yes"}
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["core.authentication.ApiSessionAuthentication"],
    "EXCEPTION_HANDLER": "core.exceptions.api_exception_handler",
}
CSRF_FAILURE_VIEW = "core.views.csrf_failure"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
