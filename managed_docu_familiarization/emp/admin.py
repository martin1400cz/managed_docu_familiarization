from django.contrib import admin
from managed_docu_familiarization.emp.models import HRPerson


# Register your models here.
@admin.register(HRPerson)
class HRPersonAdmin(admin.ModelAdmin):

    autocomplete_fields = [
    ]

    search_fields = [
        'family_name',
        'first_name',
        ]

    list_display = [
        'family_name',
        'first_name',
        ]

    list_filter = [
        ]

    @admin.display(
        boolean=True,
        ordering='deleted'
        )
    def _is_deleted(self, obj):
        return bool(obj.deleted)
