from analizator_wydatkow import settings as base_settings
from analizator_wydatkow.settings import *  # noqa: F403

# Local-only static behavior: keep URL prefix explicit and use non-manifest staticfiles backend.
STATIC_URL = "/static/"
STORAGES = {  # noqa: F405
    **base_settings.STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
