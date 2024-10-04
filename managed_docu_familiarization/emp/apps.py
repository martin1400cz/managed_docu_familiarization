from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DwhConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "managed_docu_familiarization.emp"
    verbose_name = _("Employee Planner")

    def ready(self):
        try:
            import managed_docu_familiarization.emp.signals  # noqa F401
        except ImportError:
            pass
