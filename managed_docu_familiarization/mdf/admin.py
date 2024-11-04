from django.contrib import admin

from .forms import DocumentFormAdmin
from .models import Document


# Register the Document model
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    add_form = DocumentFormAdmin
    list_display = [
        'doc_name',
        'doc_url',
        'owner',
        'category',
    ]

    list_filter = [
        'owner',
    ]

    search_fields = [
        'doc_name',
    ]

    filter_horizontal = [
        'groups',
    ]

    ordering = [
        '-doc_name',
    ]

    def get_form(self, request, obj=None, **kwargs):
        """overrides some fields for permissions

        https://realpython.com/manage-users-in-django-admin/#django-admin-and-model-permissions
        """
        form = super().get_form(request, obj, **kwargs)

        return form
