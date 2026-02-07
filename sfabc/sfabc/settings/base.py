"""
Django settings for sfabc project — base commune (dev & prod).

Les valeurs spécifiques (BDD, email, debug…) sont dans
development.py et production.py.
"""

import os
from pathlib import Path

# -----------------------------------------------------------------
# BASE_DIR  — pointe vers le dossier contenant manage.py
# (un .parent supplémentaire car on est maintenant dans settings/)
# -----------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# -----------------------------------------------------------------
# Sécurité
# -----------------------------------------------------------------
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-kov%t&_@z5&dcx)(9cwxua-z@9oys#ewyl8yg8+7eocuckp0od",
)

ALLOWED_HOSTS = (
    os.environ.get("ALLOWED_HOSTS", "").split(",")
    if os.environ.get("ALLOWED_HOSTS")
    else []
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 4 * 60 * 60


# -----------------------------------------------------------------
# Applications
# -----------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_bootstrap5",
    "colorfield",
    "django_cleanup",
    "apps.core",
    "apps.products",
    "apps.reviews",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sfabc.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "sfabc" / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sfabc.context_processors.style_processor",
            ],
        },
    },
]

WSGI_APPLICATION = "sfabc.wsgi.application"


# -----------------------------------------------------------------
# Validation des mots de passe
# -----------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -----------------------------------------------------------------
# Internationalisation
# -----------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------
# Fichiers statiques & uploads
# -----------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
DATA_UPLOAD_MAX_NUMBER_FILES = 2000


# -----------------------------------------------------------------
# Authentification (admin custom)
# -----------------------------------------------------------------
LOGIN_URL = "/admin/login/"
LOGIN_REDIRECT_URL = "/admin/"


# -----------------------------------------------------------------
# Divers
# -----------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------------------------------------------
# Email — formulaire de contact
# -----------------------------------------------------------------
CONTACT_RECIPIENT_EMAIL = os.environ.get("CONTACT_RECIPIENT_EMAIL", "contact@example.com")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@example.com")
