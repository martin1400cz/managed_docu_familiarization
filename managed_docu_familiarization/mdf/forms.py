from django import forms
from traitlets import default

from managed_docu_familiarization.users.models import User
from .models import Document, DocumentAgreement
from django.contrib.auth.models import Group
from django.contrib.admin.widgets import FilteredSelectMultiple
from managed_docu_familiarization.static.Strings import string_constants


# Form for document approval
class DocumentApprovalForm(forms.Form):
    """
    Form for approvers to approve a document.
    Parameters document_name and document_url are automatically filled from GET parameters

    responsible_users is required parameter when document is in 'waiting' status
    """

    # Field for document name (read-only)
    document_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
                                    max_length=255,
                                    required=True)

    # Field for document URL (read-only, clickable to open in a new tab)
    document_url = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly', 'onclick': "window.open(this.value, '_blank')"}),
        max_length=500,
        required=True)

    # Field for selecting responsible users (filtered select multiple widget)
    responsible_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name=string_constants.mdf_responsible_users_group_name),
        widget=FilteredSelectMultiple("Responsible_users", is_stacked=False,
                                      attrs={'class': 'form-select form-control'}),
        required=True,
        label=string_constants.publishing_page_form_responsible_users,
        help_text="Enter user IDs separated by commas.",
    )

    def __init__(self, *args, document=None, **kwargs):
        super().__init__(*args, **kwargs)
        # If the document is in 'waiting' status, responsible users are not required
        if document and document.status == 'waiting':
            self.fields['responsible_users'].required = False

    class Media:
        css = {
            'all': ['admin/css/widgets.css'],
        }
        # JavaScript for additional functionalities
        js = ['/admin/jsi18n/']


# Form for searching files/documents
class FileSearchForm(forms.Form):
    """
    Form for administrator to add a new document
    """
    document_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control w-75'}),
                                    max_length=255,
                                    required=True,
                                    label=string_constants.admin_page_form_document_name)
    document_path = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control w-75'}),
                                    label=string_constants.admin_page_form_document_path,
                                    max_length=255,
                                    required=True)
    owner = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'form-control w-75'}),
                                   queryset=User.objects.filter(groups__name=string_constants.mdf_authors_group_name),
                                   label=string_constants.admin_page_form_document_owner,
                                   required=True)

    version = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control w-25'}),
                              label="Document version:",
                              max_length=25,
                              required=True)

    # Choices for document categories
    choices = [
        (1, "Standard"),
        (2, "Guideline"),
        (3, "Workflows"),
        (4, "Manual"),
    ]

    document_category = forms.ChoiceField(
        choices=choices,
        widget=forms.RadioSelect,
        label="Document Category",
        required=True,
    )


# Form for document management
class DocumentForm(forms.Form):
    """
    Form for a document author(owner) to fill an information about document.
    """
    def __init__(self, *args, document_name=None, document_link=None, **kwargs):
        super().__init__(*args, **kwargs)
        if document_link:
            prefilled_text = (string_constants.email_message_for_users(document_name, document_link))
            self.fields['message'].initial = prefilled_text

    # Document name (read-only)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
                           max_length=255,
                           required=True)

    # Document URL (read-only)
    url = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'readonly': 'readonly'}),
        max_length=500,
        required=True)

    # Field for selecting contact users
    contact_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=FilteredSelectMultiple("Users", is_stacked=False, attrs={
            'class': 'form-select form-control',
            'id': 'id_contact_users'}),
        required=False,  # Optional field
        label=string_constants.publishing_page_form_contact_users,
        help_text="Enter user IDs separated by commas.",
    )

    # Choices for publication category
    choices = [
        (1, "Private documents"),
        (2, "Public documents"),
        (3, "Documents for certain groups"),
    ]

    category = forms.ChoiceField(
        choices=choices,
        widget=forms.RadioSelect,
        label="Publication category",
        required=True,
    )

    # Field for selecting user groups
    groups = forms.ModelMultipleChoiceField(
        label="Select Groups",
        queryset=Group.objects.all(),
        widget=FilteredSelectMultiple("Groups", is_stacked=False, attrs={'class': 'form-select form-control'}),
        required=False
    )

    # Field for setting a deadline for document approval
    deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd.mm.yyyy', 'class': 'form-control col col-md-3',
                                      'id': 'id_deadline'}),
        input_formats=['%d.%m.%Y'],
        label='Set a deadline for this document',
        help_text="Select a date and time when the document should be finalized."
    )

    # Field for an email message
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 15,
            'cols': 150,
            'placeholder': 'Write here a message for users...',
            'id': 'id_message',
            'class': 'form-control',
        }),
        label="Email message:",
    )

    class Media:
        css = {
            'all': ['admin/css/widgets.css'],
        }
        js = ['/admin/jsi18n/']

    def save(self, commit=True):
        doc = super().save()
        return doc


# Admin form for Document model
class DocumentFormAdmin(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('doc_name', 'doc_url', 'owner', 'category')

    def save(self, commit=True):
        doc = super().save()
        return doc


# Admin form for DocumentAgreement model
class DocumentAgreementAdmin(forms.ModelForm):
    class Meta:
        model = DocumentAgreement
        fields = ('user', 'document')

    def save(self, commit=True):
        agr = super().save()
        return agr
