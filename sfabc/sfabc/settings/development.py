"""
Settings de développement — python manage.py runserver
  • SQLite
  • Media local (dossier media/)
  • Emails affichés dans la console
"""

from .base import *  # noqa: F401,F403

# -----------------------------------------------------------------
# Debug
# -----------------------------------------------------------------
DEBUG = True


# -----------------------------------------------------------------
# Base de données — SQLite
# -----------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
        },
    }
}


# -----------------------------------------------------------------
# Fichiers média
# -----------------------------------------------------------------
MEDIA_ROOT = BASE_DIR / "media"


# -----------------------------------------------------------------
# Email — tout s'affiche dans le terminal, rien n'est envoyé
# -----------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
