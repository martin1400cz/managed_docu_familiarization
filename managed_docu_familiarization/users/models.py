from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.models import Group  # Import your custom Group model from the authentication app
from django.core.validators import validate_email
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Methods behind Model.objects.*** """

    def get_queryset(self):
        """Optimize queries to speed up loading time."""
        related_fields = [
            'groups',
        ]

        return super(UserManager, self).get_queryset() \
            .prefetch_related(*related_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Default custom user model for Staff Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    zf_id = models.CharField(
        verbose_name=_('Z id'),
        help_text=_('Unique ZF identifier (Z-ID, Z123456)'),
        max_length=20,
        unique=True,
    )

    email = models.EmailField(
        verbose_name=_('email'),
        help_text=_("employee's company email"),
        max_length=60,
        unique=True,
        validators=[
            validate_email,
            ]
        )

    first_name = models.CharField(
        verbose_name=_('first name'),
        help_text=_("employee's first name"),
        max_length=20
        )

    last_name = models.CharField(
        verbose_name=_('last name'),
        help_text=_("employee's last name, family name"),
        max_length=20
        )

    is_staff = models.BooleanField(
        verbose_name=_('is staff'),
        help_text=_('staff status on top of the one granted by the role'),
        default=False,
        )

    groups = models.ManyToManyField(
        Group, related_name='users',
        blank=True
        )

    USERNAME_FIELD = "zf_id"
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f'{self.zf_id} - {self.get_full_name()}'

    def __repr__(self):
        return self.__str__()

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.first_name
