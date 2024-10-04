import datetime
from decimal import Decimal
import logging
import unicodedata

from django.core import validators
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

log = logging.getLogger(__name__)


class HRPersonManager(models.Manager):
    """Default HR Person Manager"""

    def get_queryset(self):
        """Optimize queries to speed up loading time."""
        related_fields = [
            ]

        return super(HRPersonManager, self).get_queryset() \
            .select_related(*related_fields)

"""
class VACREQEMPs(HRPersonManager):
    def get_queryset(self):
        return super(VACREQEMPs, self).get_queryset() \
            .filter(
            Q(emp_cat__abbrev='VAC') | Q(emp_cat__abbrev='REQ')
            )
"""

class HRPerson(models.Model):
    """
    """

    @staticmethod
    def append_error(errors, field, value):
        if field not in errors:
            errors[field] = [value]
        else:
            errors[field] = [errors[field], value]

        return errors

    def clean(self):
        """
        # List of errors - initialize date fields for stacking messages
        errors = {}


        # Try to get previous values, if we are editing record
        previous_values = None
        if self.pk is not None:
            try:
                previous_values = self.__class__.objects.get(pk=self.pk)
            except: # e.g. we are crating a new record via MHRS
                previous_values = None

        # Validate 'first work day' - 'contract start date'
        if self.first_work_day is not None and self.contract_start_date is not None and self.first_work_day < self.contract_start_date:
            if previous_values is None or previous_values.first_work_day is None or previous_values.first_work_day != self.first_work_day:
                errors = self.append_error(errors, 'first_work_day',
                                           f"'First work day' ({self.first_work_day}) must be after 'Contract start date' ({self.contract_start_date}).")
            else:
                errors = self.append_error(errors, 'contract_start_date',
                                           f"'Contract start date' ({self.contract_start_date}) must be equal or before 'First work day' ({self.first_work_day}).")

        if errors:
            raise ValidationError(errors)
        """

    #:
    first_name = models.CharField(
        verbose_name=_('First name'),
        help_text=_('First name of the person'),
        max_length=40,
        blank=True,
        null=True,
        )

    #:
    family_name = models.CharField(
        verbose_name=_('Family name'),
        help_text=_('Family name of the person'),
        max_length=40,
        blank=True,
        null=True,
        )

    """
    #:
    contract_type = models.ForeignKey(
        ContractType,
        verbose_name=_("Contract type"),
        on_delete=models.PROTECT,
        default=get_default_contract_type,
        blank=False,
        null=False,
        )
    """

    """
    #:
    weekly_working_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=40,
        validators=[
            validators.MaxValueValidator(Decimal('40')),
            validators.MinValueValidator(Decimal('0'))
            ]
        )
    """

    """
    EQ_LAPTOP = 'LAPTOP'
    EQ_CITRIX = 'CITRIX'
    EQ_NOT_NEEDED = 'Not needed'
    EQUIPMENT_CHOICES = (
        ('', ''),
        (EQ_NOT_NEEDED, 'Not needed'),
        (EQ_LAPTOP, 'Laptop'),
        (EQ_CITRIX, 'Citrix'),
        )
    externist_equipment = models.CharField(
        max_length=10,
        choices=EQUIPMENT_CHOICES,
        verbose_name=_('Externist equipment'),
        default=EQ_NOT_NEEDED,
        blank=False,
        null=False,
        )
    """

    objects = HRPersonManager()
    # vacreq = VACREQEMPs()

    def __str__(self):
        return f'{self.family_name}, {self.first_name}'

    @property
    def part_title(self):
        return f'{self.family_name}, {self.first_name}'

    def save(self, **kwargs):
        # Add what you want here
        super().save(**kwargs)

    class Meta:
        verbose_name = _('HR Person')
        verbose_name_plural = _('HR People')
        ordering = ['family_name']
