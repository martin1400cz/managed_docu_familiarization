import uuid

import django.contrib.auth.models
from django.db import models
from django.db.models import Subquery, OuterRef, Max, Exists
from django.utils.translation import gettext_lazy as _

from managed_docu_familiarization.users.models import User as User
from managed_docu_familiarization.users.models import Group as Group


class DocumentsManager(models.Manager):
    """
    A custom manager for the document model.
    """
    def get_queryset(self):
        related_fields = [
            ]

        return super(DocumentsManager, self).get_queryset() \
            .select_related(*related_fields)

    def for_user(self, user):
        return self.filter(owner=user)


DOCUMENT_CATEGORY_CHOICES = (
    (1, "Standard"),
    (2, "Guideline"),
    (3, "Workflows"),
    (4, "Manual"),
)

# Category formats
FORMAT_CHOICES = (
    (1, 'Private documents'),
    (2, 'Public documents'),
    (3, 'Documents for certain groups'),
)

# Document's status
STATUS_CHOICES = (
    ('uploaded', 'Uploaded'),
    ('waiting_owner', 'Waiting for owner'),
    ('waiting', 'Waiting'),
    ('pending', 'Pending'),             # Document has been published by owner
    ('processed', 'Processed'),         # Document has been processed
    ('expired', 'Expired'),             # Document has been expired
)

class Document(models.Model):
    """
    Document model - represents a document using a reference to it
    """
    doc_id = models.AutoField(primary_key=True) # Document id
    doc_name = models.CharField(max_length=255) # Document name
    doc_url = models.CharField(max_length=500, blank=True, null=True) # Document url
    doc_category = models.PositiveSmallIntegerField('Document category', choices=DOCUMENT_CATEGORY_CHOICES, null=True, blank=True) # Document type category
    category = models.PositiveSmallIntegerField('Category', choices=FORMAT_CHOICES, default=1) # Publication category
    release_date = models.DateTimeField(auto_now_add=True) # Release date
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_owner') # Document owner
    responsible_users = models.ManyToManyField(User, related_name='document_responsible_users', null=True, blank=True) # Responsible users to document approval
    approved_by_users = models.ManyToManyField(User, related_name='document_users_approved', null=True, blank=True) # List of user who approved document
    contact_users = models.ManyToManyField(User, related_name='document_contact_users', null=True, blank=True) # Contact users
    deadline = models.DateTimeField(null=True, blank=True) # Deadline of collecting consents
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded') # Document status
    groups = models.ManyToManyField(Group, related_name='document_groups', blank=True, null=True) # Groups of target users
    #doc_ver = models.PositiveIntegerField(default=1)  # document version
    doc_ver = models.CharField(max_length=25)  # document version
    previous_version = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL) # instance of previous document

    def save_new_version(self, new_doc_name, new_doc_url, new_owner, responsible_users, new_doc_version):
        """
        Creates a new version of document
        """
        new_version = Document.objects.create(
            doc_name=new_doc_name,
            doc_url=new_doc_url,
            owner=new_owner,
            doc_category=self.doc_category,
            doc_ver=new_doc_version,
            previous_version=self
        )

        new_version.groups.set(self.groups.all())
        new_version.responsible_users.set(responsible_users)
        return new_version

    def get_all_versions(self):
        """
        Returns a list of all versions of a document.
        """
        versions = []
        doc = self
        while doc:
            versions.append(doc)
            doc = doc.previous_version
        return versions[::-1]  # Returns versions from oldest to newest

    def get_latest_version(self):
        """
        Returns the latest version of the document.
        """
        doc = self
        while Document.objects.filter(previous_version=doc).exists():
            doc = Document.objects.get(previous_version=doc)
        return doc

    @classmethod
    def get_latest_documents(cls):
        """
        Returns latest version documents
        """
        return cls.objects.filter(
            ~Exists(cls.objects.filter(previous_version=OuterRef('pk')))
        )

    @property
    def is_waiting_owner(self):
        return self.status == 'waiting_owner'

    def is_waiting(self):
        return self.status == 'waiting'

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
        #unique_set.remove(owner)
        return list(unique_set)

    def get_category_text(self):
        for key, value in FORMAT_CHOICES:
            if key == self.category:
                return value
        return 'Unknown category'

    def get_document_category_text(self):
        for key, value in DOCUMENT_CATEGORY_CHOICES:
            if key == self.doc_category:
                return value
        return 'Unknown document category'

    def get_document_status_text(self):
        for key, value in STATUS_CHOICES:
            if key == self.status:
                return value
        return 'Unknown status'

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



