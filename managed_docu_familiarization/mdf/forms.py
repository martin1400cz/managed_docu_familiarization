from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('doc_name', 'owner', 'category', 'release_date')

    def save(self, commit=True):
        doc = super().save()
        return doc
