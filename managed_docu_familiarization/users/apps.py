import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "managed_docu_familiarization.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import managed_docu_familiarization.users.signals  # noqa: F401
        except ImportError:
            pass
