from django import forms
from traitlets import default

from managed_docu_familiarization.users.models import User
from .models import Document, DocumentAgreement
from django.contrib.auth.models import Group
from django.contrib.admin.widgets import FilteredSelectMultiple
from managed_docu_familiarization.static.Strings import string_constants

class FileSearchForm(forms.Form):
    document_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control w-75'}),
                                    max_length=255,
                                    required=True,
                                    label=string_constants.admin_page_form_document_name)
    document_path = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control w-75'}),
                                    label=string_constants.admin_page_form_document_path,
                                    max_length=255,
                                    required=True)
    owner = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'form-control w-75'}),
                                   queryset=User.objects.all(),
                                   label=string_constants.admin_page_form_document_owner,
                                   required=True)
    responsible_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=FilteredSelectMultiple("Responsible_users", is_stacked=False, attrs={'class': 'form-select form-control'}),
        required=False,
        label=string_constants.publishing_page_form_responsible_users,
        help_text="Enter user IDs separated by commas.",
    )
    class Media:
        css = {
            'all': ['admin/css/widgets.css'],
        }
        # Adding this javascript is crucial
        js = ['/admin/jsi18n/']


class DocumentForm(forms.Form):
    def __init__(self, *args, document_name=None, document_link=None, **kwargs):
        super().__init__(*args, **kwargs)
        if document_link:
            prefilled_text = (string_constants.email_message_for_users(document_name, document_link))
            self.fields['message'].initial = prefilled_text
    #filter_horizontal = ('groups',)

    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
                           max_length=255,
                           required=True)
    url = forms.CharField(widget=forms.TextInput(
                            attrs={'class': 'form-control', 'readonly': 'readonly'}),
                            max_length=500,
                            required=True)

    contact_users = forms.ModelMultipleChoiceField(
        #    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        queryset=User.objects.all(),
        widget=FilteredSelectMultiple("Users", is_stacked=False, attrs={
            'class': 'form-select form-control' ,
            'id': 'id_contact_users'}),
        required=False,  # It may be empty
        label=string_constants.publishing_page_form_contact_users,
        help_text="Enter user IDs separated by commas.",
    )

    #contact_users = forms.Textarea(queryset=User.objects.all(), attrs={'cols': 80, 'rows': 2})

    choices = [
        (1, "Private documents"),
        (2, "Public documents"),
        (3, "Documents for certain groups"),
    ]

    category = forms.ChoiceField(
        choices=choices,
        #widget=forms.RadioSelect(attrs={'class': 'form-check-input category-choice'}),
        widget=forms.RadioSelect,
        label="Document Category",
        required=True,
    )

    groups = forms.ModelMultipleChoiceField(
        label="Select Groups",
        queryset=Group.objects.all(),
        #widget=forms.SelectMultiple(attrs={'class': 'admin-style-select'}),  # Customize styling as needed
        widget=FilteredSelectMultiple("Groups", is_stacked=False, attrs={'class': 'form-select form-control'}),
        #filter_horizontal=['Groups'],
        required=False
    )

    deadline = forms.DateTimeField(
        required=False,
        #widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'dd.mm.yyyy', 'class': 'form-control col col-md-3', 'id': 'id_deadline'}),
        input_formats=['%d.%m.%Y'],  # The format we expect
        label='Set a deadline for this document',  # Custom label
        help_text="Select a date and time when the document should be finalized."  # Help text
    )

    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 15,
            'cols': 150,
            'placeholder': 'Write here a message for users...',
            'id': 'id_message',
            'class': 'form-control',
        }),
        #initial=string_constants.email_message_for_users,
        label="Email message:",
    )

    class Media:
        css = {
            #'all': ['admin/css/widgets.css',
            #        'css/uid-manage-form.css'],
            'all': ['admin/css/widgets.css'],
        }
        # Adding this javascript is crucial
        js = ['/admin/jsi18n/']

    #class Meta:
    #    model = Document
    #    fields = ['name', 'url',  'contact_users', 'category', 'groups', 'deadline']

    def save(self, commit=True):
        doc = super().save()
        return doc
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    self.fields['contact_users'].queryset = User.objects.all()


class DocumentFormAdmin(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('doc_name', 'doc_url', 'owner', 'category')


    def save(self, commit=True):
        doc = super().save()
        return doc


class DocumentAgreementAdmin(forms.ModelForm):
    class Meta:
        model = DocumentAgreement
        fields = ('user', 'document')

    def save(self, commit=True):
        agr = super().save()
        return agr
