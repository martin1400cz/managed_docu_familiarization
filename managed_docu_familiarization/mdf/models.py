import uuid

import django.contrib.auth.models
from django.db import models
from django.db.models import Subquery, OuterRef, Max, Exists
from django.utils.translation import gettext_lazy as _

from managed_docu_familiarization.users.models import User as User
from managed_docu_familiarization.users.models import Group as Group


class DocumentsManager(models.Manager):
    """
    A custom manager for the Document model.
    """
    def get_queryset(self):
        related_fields = [
            ]

        return super(DocumentsManager, self).get_queryset() \
            .select_related(*related_fields)

    def for_user(self, user):
        return self.filter(owner=user)

"""
Document category choices (document types)
"""
DOCUMENT_CATEGORY_CHOICES = (
    (1, "Standard"),
    (2, "Guideline"),
    (3, "Workflows"),
    (4, "Manual"),
)

"""
Category formats
"""
FORMAT_CHOICES = (
    (1, 'Private documents'),
    (2, 'Public documents'),
    (3, 'Documents for certain groups'),
)

"""
Document's status
"""
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

    Main parameters:

    doc_id - primary key - id of the document

    doc_name - name of the document

    doc_url - url (path) to the document

    doc_category - document category (type of the document)

    category - publishing category, i.e. category which is chosen by user when publishing document for other users

    release_date - automatically added when the document is created

    owner - foreign key to the managed_docu_familiarization.users.models.user - it represents an owner of the document (or author)

    responsible_users - ManyToMany parameter (for users). It represents users who were chosen to approve the document

    approved_by_users - ManyToMany parameter, users from responsible_users who approved the document

    contact_users - ManyToMany parameter, users who were chosen to answer questins, etc.

    deadline - timestamp added by user who chose the document to be category 3

    status - document status

    groups - ManyToMany parameter (for user.groups) - represents chosen groups of users

    doc_ver - version of document added by admin

    previos_version - foreign key to Document model - represents an previous version of the document
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
        """
        :return: if document status is waiting_owner
        """
        return self.status == 'waiting_owner'

    def is_waiting(self):
        """
        :return: if dokument status is waiting
        """
        return self.status == 'waiting'

    @property
    def is_uploaded(self):
        """
        :return: if document status is uploaded
        """
        return self.status == 'uploaded'

    def get_all_important_users(self):
        """
        :return: all users from responsible_users and owner
        """
        all_users = set(self.responsible_users.all())
        all_users.add(self.owner)
        return list(all_users)

    def get_responsible_users(self):
        """
        :return: all users from responsible_users
        """
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
        """
        :return: Name of category for publishing
        """
        for key, value in FORMAT_CHOICES:
            if key == self.category:
                return value
        return 'Unknown category'

    def get_document_category_text(self):
        """
        :return: name of document category
        """
        for key, value in DOCUMENT_CATEGORY_CHOICES:
            if key == self.doc_category:
                return value
        return 'Unknown document category'

    def get_document_status_text(self):
        """
        :return: name of document status
        """
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
    """
    DocumentAgreement model - represents an agreement from user for certain document

    Main parameters:

    document - foreign key to Document model

    user - foreign key to managed_docu_model.users.models.user

    agreet_at - automatically added timestamp when a user agrees
    """
    id = models.AutoField(primary_key=True) # id of the agreement
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_stats')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='agreements')
    agreed_at = models.DateTimeField(auto_now_add=True)  # Automatically saves the timestamp when a user agrees
    reading_time = models.PositiveIntegerField(default=0) # time user spend with reading the document
    # open_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'document')  # Ensures one agreement per user per document

    def __str__(self):
        return f"{self.user.zf_id} agreed to {self.document.doc_name}"

    def save(self, **kwargs):
        # Add what you want here
        super().save(**kwargs)



