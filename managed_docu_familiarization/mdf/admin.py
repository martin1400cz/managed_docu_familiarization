from django.contrib import admin
from .models import Document
from managed_docu_familiarization.mdf.forms import DocumentForm

# Register the Document model
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    add_form = DocumentForm
    list_display = [
        'doc_name',
        'release_date',
        'doc_url',
        'owner',
    ]

    list_filter = [
        'release_date',
    ]

    search_fields = [
        'doc_name',
    ]

    filter_horizontal = [
        'groups',
    ]

    ordering = [
        '-release_date',
    ]

    def get_form(self, request, obj=None, **kwargs):
        """overrides some fields for permissions

        https://realpython.com/manage-users-in-django-admin/#django-admin-and-model-permissions
        """
        form = super().get_form(request, obj, **kwargs)

        return form
