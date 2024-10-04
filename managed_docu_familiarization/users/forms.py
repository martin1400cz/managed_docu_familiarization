import logging

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

from managed_docu_familiarization.users.backends import PlainTextBackend

from .models import User

log = logging.getLogger(__name__)


class LoginForm(AuthenticationForm):

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        backend = PlainTextBackend()
        user = backend.authenticate(self.request, username=username, password=password)
        if user is None:
            raise self.get_invalid_login_error()
        else:
            self.user_cache = user
            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def clean_username(self):
        """All usernames (Z_IDs) must be uppercase."""
        username = self.cleaned_data.get('username')
        return username.upper()


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields."""

    class Meta:
        model = User
        fields = (
            'zf_id',
            'email',
            'first_name',
            'last_name',
            )

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on the user.
    """

    class Meta:
        model = User
        fields = (
            'zf_id',
            'email',
            'first_name',
            'last_name',
            )
