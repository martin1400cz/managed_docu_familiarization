from django import forms

from django.contrib.admin.widgets import AutocompleteSelect
from django.contrib import admin
from django.contrib.admin import widgets
import logging

from config.settings.base import DATE_INPUT_FORMATS

log = logging.getLogger(__name__)

"""
class EMPPersonUpdateIntForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        widget=AutocompleteSelectCustom(HRPerson._meta.get_field('location')),
        required=True
    )

    fieldsets = [
        ("Internal location and IT Roles", {'fields': [
            ('location', 'building', 'floor')
        ],'description': 'field_1'
        }),
        ("Note", {'fields': [
            'note'
        ], 'description': 'field_2'
        }),
    ]

    class Media:
        extend = False
        css = {
            'all': [
                'css/django_custom/select2.css',
                'css/django_custom/autocomplete_custom.css',
                'admin/css/autocomplete.css',
            ]
        }
        js = (
            "admin/js/vendor/jquery/jquery.min.js",
            "js/django_custom/select2.full.js",
            "admin/js/jquery.init.js",
            "admin/js/autocomplete.js",
            "js/jquery.dirty.js",
            "js/django_custom/autocomplete_custom.js",
        )

    class Meta:
        model = HRPerson
        fields = [
            'location',
            'building',
            'floor',
            'note'
        ]
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }
"""
