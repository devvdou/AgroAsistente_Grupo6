import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# La ruta de Firebase siempre se interpreta desde la carpeta del proyecto.
firebase_credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()
if firebase_credentials_path:
    credentials_file = Path(firebase_credentials_path)
    if not credentials_file.is_absolute():
        credentials_file = BASE_DIR / credentials_file
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_file.resolve())

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "solo-desarrollo-cambiar-en-produccion")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() in {"1", "true", "yes", "si"}
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "agro",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "agroasistente.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]
WSGI_APPLICATION = "agroasistente.wsgi.application"
ASGI_APPLICATION = "agroasistente.asgi.application"

# La persistencia funcional está en Firebase. Django no usa una base SQL de negocio.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
