from django.db import models
from django.utils.translation import gettext_lazy as _

import managed_docu_familiarization.users.models


class DocumentsManager(models.Manager):

    def get_queryset(self):
        related_fields = [
            ]

        return super(DocumentsManager, self).get_queryset() \
            .select_related(*related_fields)

FORMAT_CHOICES = (
    (1, 'Private documents'),
    (2, 'Public documents'),
    (3, 'Documents for certain groups'),
)

class Group(models.Model):
    name = models.CharField(max_length=100)
    users = models.ManyToManyField(managed_docu_familiarization.users.models.User)

    def __str__(self):
        return self.name

class Owner(models.Model):
    id = models.AutoField(primary_key=True)
    users = models.ManyToManyField(managed_docu_familiarization.users.models.User)

    def __str__(self):
        return self.users.models.User.last_name

class Document(models.Model):
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.CharField(max_length=255)
    category = models.PositiveSmallIntegerField('Category', choices=FORMAT_CHOICES)
    release_date = models.DateField()
    owner = models.ForeignKey(Group, on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, related_name='documents')

    def __str__(self):
        return self.doc_name

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')

class Publishing(models.Model):
    id = models.AutoField(primary_key=True)
    document = models.OneToOneField(Document, on_delete=models.CASCADE)  # Assuming each publishing relates to one document
    deadline = models.DateField()

    def __str__(self):
        return f"Publishing of {self.document.doc_name}"


