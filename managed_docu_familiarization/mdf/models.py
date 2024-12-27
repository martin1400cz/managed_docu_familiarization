import uuid

import django.contrib.auth.models
from django.db import models
from django.utils.translation import gettext_lazy as _

from managed_docu_familiarization.users.models import User as User
from managed_docu_familiarization.users.models import Group as Group


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

STATUS_CHOICES = (
    ('uploaded', 'Uploaded'),  # Document has been uploaded by admin
    ('pending', 'Pending'),    # Document has been published by owner
    ('processed', 'Processed'),# Document has been processed
    ('expired', 'Expired')     # Document has been expired
)

class Document(models.Model):
    """

    """
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.CharField(max_length=255)
    doc_url = models.CharField(max_length=500, blank=True, null=True)
    category = models.PositiveSmallIntegerField('Category', choices=FORMAT_CHOICES)
    release_date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_owner')
    responsible_users = models.ManyToManyField(User, related_name='document_responsible_users', null=True, blank=True)
    contact_users = models.ManyToManyField(User, related_name='document_contact_users')
    deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='uploaded')
    groups = models.ManyToManyField(Group, related_name='document_groups', blank=True, null=True)

    @property
    def is_uploaded(self):
        return self.status == 'uploaded'

    def get_all_important_users(self):
        all_users = set(self.responsible_users.all())
        all_users.add(self.owner)
        return list(all_users)

    def get_responsible_users(self):
        all_users = set(self.responsible_users.all())
        return list(all_users)


    def get_users_from_groups(self):
        """
        Functions returns a list of users from certain groups, if some users are in more than one group, they are picked only once.
        """
        unique_set = set()
        users = User.objects.filter(groups__in=self.groups.all())
        owner = self.owner
        unique_set.update(users)
        unique_set.remove(owner)
        return list(unique_set)

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_stats')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='agreements')
    agreed_at = models.DateTimeField(auto_now_add=True)  # Automatically saves the timestamp when a user agrees
    reading_time = models.PositiveIntegerField(default=0)
    open_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'document')  # Ensures one agreement per user per document

    def __str__(self):
        return f"{self.user.zf_id} agreed to {self.document.doc_name}"

    def save(self, **kwargs):
        # Add what you want here
        super().save(**kwargs)



