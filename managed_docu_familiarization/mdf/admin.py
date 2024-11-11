from django.contrib import admin

from .forms import DocumentFormAdmin, DocumentAgreementAdmin
from .models import Document, DocumentAgreement


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

# Register the DocumentAgreement model
@admin.register(DocumentAgreement)
class DocumentAgreementAdmin(admin.ModelAdmin):
    add_form = DocumentAgreementAdmin
    list_display = [
        'id',
        'user',
        'document',
    ]

    list_filter = [
        'document',
    ]

    search_fields = [
        'id',
    ]

    ordering = [
        '-id',
    ]

    def get_form(self, request, obj=None, **kwargs):
        """overrides some fields for permissions

        https://realpython.com/manage-users-in-django-admin/#django-admin-and-model-permissions
        """
        form = super().get_form(request, obj, **kwargs)

        return form
