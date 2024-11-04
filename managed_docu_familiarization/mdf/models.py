import uuid

import django.contrib.auth.models
from django.db import models
from django.utils.translation import gettext_lazy as _

import managed_docu_familiarization.users.models


class DocumentsManager(models.Manager):

    def get_queryset(self):
        related_fields = [
            ]

        return super(DocumentsManager, self).get_queryset() \
            .select_related(*related_fields)

    def for_user(self, user):
        return self.filter(owner=user)

FORMAT_CHOICES = (
    (1, 'Private documents'),
    (2, 'Public documents'),
    (3, 'Documents for certain groups'),
)

"""
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
"""

class Document(models.Model):
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.CharField(max_length=255)
    doc_url = models.CharField(max_length=500, blank=True, null=True)
    category = models.PositiveSmallIntegerField('Category', choices=FORMAT_CHOICES)
    release_date = models.DateTimeField(auto_now_add=True)
    # release_date = models.DateField(blank=False, null=False)
    owner = models.ForeignKey(managed_docu_familiarization.users.models.User, on_delete=models.CASCADE)
    #contact_users = models.ManyToManyField(managed_docu_familiarization.users.models.User)
    #groups = models.ManyToManyField(Group, related_name='documents')

    #groups = models.ManyToManyField(managed_docu_familiarization.users.models.Group, related_name='documents', blank=False, null=False)
    groups = models.ManyToManyField(managed_docu_familiarization.users.models.Group, related_name='documents', blank=True, null=True)
    #secure_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    #objects = DocumentsManager()

    def __str__(self):
        return self.doc_name

    @property
    def part_title(self):
        return f'{self.doc_name}'

    def save(self, **kwargs):
        # Add what you want here
        super().save(**kwargs)

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')


class DocumentAgreement(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(managed_docu_familiarization.users.models.User, on_delete=models.CASCADE, related_name='document_agreements')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='agreements')
    agreed_at = models.DateTimeField(auto_now_add=True)  # Automatically saves the timestamp when a user agrees

    class Meta:
        unique_together = ('user', 'document')  # Ensures one agreement per user per document

    def __str__(self):
        return f"{self.user.zf_id} agreed to {self.document.doc_name}"



