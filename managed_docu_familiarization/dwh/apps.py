from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DwhConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "managed_docu_familiarization.dwh"
    verbose_name = _("Data Warehouse")
