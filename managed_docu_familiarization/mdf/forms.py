from django import forms

from managed_docu_familiarization.users.models import User
from .models import Document, DocumentAgreement
from django.contrib.auth.models import Group
from django.contrib.admin.widgets import FilteredSelectMultiple

class FileSearchForm(forms.Form):
    document_path = forms.CharField(label="Document Path", max_length=255)
    owner = forms.ModelChoiceField(queryset=User.objects.all(), label="Select Owner")

class DocumentForm(forms.ModelForm):

    name = forms.CharField(widget=forms.TextInput(),
                           max_length=255,
                           required=True)
    url = forms.CharField(widget=forms.TextInput(
                            attrs={'readonly': 'readonly'}),
                            max_length=500,
                            required=True)

    choices = [
        (1, "Private documents"),
        (2, "Public documents"),
        (3, "Documents for certain groups"),
    ]

    category = forms.ChoiceField(
        choices=choices,
        widget=forms.RadioSelect(attrs={'class': 'category-choice'}),
        label="Document Category"
    )

    groups = forms.ModelMultipleChoiceField(
        label="Select Groups",
        queryset=Group.objects.all(),
        #widget=forms.SelectMultiple(attrs={'class': 'admin-style-select'}),  # Customize styling as needed
        widget=FilteredSelectMultiple("Groups", is_stacked=False),
        #filter_horizontal=['Groups'],
        required=False
    )
    #filter_horizontal = ('groups',)

    class Media:
        css = {
            'all': ['admin/css/widgets.css',
                    'css/uid-manage-form.css'],
        }
        # Adding this javascript is crucial
        js = ['/admin/jsi18n/']

    class Meta:
        model = Document
        fields = ['doc_url', 'category', 'groups']


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
