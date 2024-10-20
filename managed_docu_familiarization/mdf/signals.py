import datetime
import logging

from django.conf import settings
from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from managed_docu_familiarization.mdf.models import Document

log = logging.getLogger(__name__)

@receiver(pre_save, sender=Document)
def on_mdf_pre_save(sender, instance, **kwargs):
    """
    """

    if kwargs['raw']:  # raw is set when loading from fixture
        return

    # get the current instance from the database
    try:

        original_instance = sender.objects.get(pk=instance.pk)

    except sender.DoesNotExist:

        # the instance is new, not saved yet
        pass

    else:  # the object was edited

        pass



@receiver(post_save, sender=Document)
def on_mdf_save(sender, instance, **kwargs):
    """
    """

    if kwargs['raw']:  # raw is set when loading from fixture
        return

    if kwargs['created']:  # the record was created
        pass

    else:  # the record was edited
        pass
