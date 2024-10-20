from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MDFConfig(AppConfig):
    name = "managed_docu_familiarization.mdf"
    verbose_name = _("MDF")

    def ready(self):
        try:
            import managed_docu_familiarization.mdf.signals
        except ImportError:
            pass
