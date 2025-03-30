from django.test import TestCase
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import Group

from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.users.models import User
from managed_docu_familiarization.mdf.forms import DocumentForm, DocumentApprovalForm, FileSearchForm
from managed_docu_familiarization.mdf.models import Document

class FormTests(TestCase):
    """
    Class with unit tests for each form in forms.py
    """
    def setUp(self):
        """Testing data initialisation"""
        self.group_admin = Group.objects.create(name=string_constants.mdf_admin_group_name)
        self.group_authors = Group.objects.create(name=string_constants.mdf_authors_group_name)
        self.group_responsibles = Group.objects.create(name=string_constants.mdf_responsible_users_group_name)

        self.user_admin = User.objects.create_user(
            zf_id="ZADMIN",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )
        self.user_admin.groups.add(self.group_admin)

        self.user_author = User.objects.create_user(
            zf_id="ZAUTHOR",
            email="author@example.com",
            first_name="Author",
            last_name="User",
            is_staff=True,
        )
        self.user_author.groups.add(self.group_authors)

        self.user_responsible = User.objects.create_user(
            zf_id="ZRESPONSIBLE",
            email="responsible@example.com",
            first_name="Responsible",
            last_name="User",
            is_staff=True,
        )
        self.user_responsible.groups.add(self.group_responsibles)

        self.user_ordinary = User.objects.create_user(
            zf_id="ZORDINARY",
            email="ordinary@example.com",
            first_name="Ordinary",
            last_name="User",
            is_staff=True,
        )

        self.document_link = "http://example.com/document"
        self.document = Document.objects.create(
            doc_name="Test Document",
            doc_url="http://example.com/test-document",
            category=3,
            doc_category=1,
            doc_ver="1.0",  # Přidáno
            status="uploaded",  # Přidáno
            owner=self.user_admin,
            deadline=now() + timedelta(days=7),
        )

    def test_valid_form(self):
        """Test valid DocumentForm"""
        form_data = {
            'name': 'Test Document',
            'url': 'http://example.com/test-doc',
            'contact_users': [self.user_admin.pk, self.user_author.pk],
            'category': 3,  # Private documents
            'groups': [self.group_admin.pk],
            'deadline': (now() + timedelta(days=7)),
            'message': string_constants.email_message_for_users(self.document.doc_name, self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")


    def test_invalid_url(self):
        """Test invalid document url DocumentForm"""
        form_data = {
            'name': 'Invalid URL Document',
            'url': None,
            'contact_users': [self.user_author.pk],
            'category': 3,  # Public documents
            'deadline': (now() + timedelta(days=7)),
            'message': string_constants.email_message_for_users(self.document.doc_name, self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)


    def test_missing_required_fields(self):
        """Test missing required field DocumentForm"""
        form_data = {
            'url': 'http://example.com/missing-fields',
            'contact_users': [self.user_admin.pk],
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('category', form.errors)

    def test_category_choices(self):
        """Test invalid category choice DocumentForm"""
        form_data = {
            'name': 'Test Invalid Category',
            'url': 'http://example.com/invalid-category',
            'contact_users': [self.user_admin.pk],
            'category': 99,  # invalid choice
            'deadline': (now() + timedelta(days=7)),
            'message': string_constants.email_message_for_users(self.document.doc_name, self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_deadline_format(self):
        """Test invalid deadline format DocumentForm"""
        form_data = {
            'name': 'Test Deadline',
            'url': 'http://example.com/deadline',
            'contact_users': [self.user_admin.pk],
            'category': 3,
            'deadline': '31-12-2025',  # invalid format
            'message': string_constants.email_message_for_users(self.document.doc_name, self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('deadline', form.errors)

    def test_document_form_readonly_fields(self):
        """Verify that the 'document_name' and 'document_url' fields have the readonly attribute"""
        form = DocumentForm()
        self.assertIn('readonly', form.fields['name'].widget.attrs)
        self.assertIn('readonly', form.fields['url'].widget.attrs)

    def test_valid_document_approval_form(self):
        """Test valid DocumentApprovalForm"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_url': self.document.doc_url,
            'responsible_users': [self.user_responsible.pk],
        }
        form = DocumentApprovalForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_invalid_document_approval_form_missing_document_name(self):
        """Test invalid DocumentApprovalForm with missing document name"""
        form_data = {
            'document_url': self.document.doc_url,
            'responsible_users': [self.user_responsible.pk],
        }
        form = DocumentApprovalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('document_name', form.errors)

    def test_invalid_document_approval_form_missing_document_url(self):
        """Test invalid DocumentApprovalForm with missing document url"""
        form_data = {
            'document_name': self.document.doc_name,
            'responsible_users': [self.user_responsible.pk],
        }
        form = DocumentApprovalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('document_url', form.errors)

    def test_invalid_document_approval_form_missing_responsible_users(self):
        """Test invalid DocumentApprovalForm with missing responsible users"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_url': self.document.doc_url,
        }
        form = DocumentApprovalForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('responsible_users', form.errors)

    def test_document_approval_form_readonly_fields(self):
        """Verify that the 'document_name' and 'document_url' fields have the readonly attribute"""
        form = DocumentApprovalForm()
        self.assertIn('readonly', form.fields['document_name'].widget.attrs)
        self.assertIn('readonly', form.fields['document_url'].widget.attrs)

    def test_valid_file_search_form(self):
        """Test valid FileSearchForm"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_path': self.document.doc_url,
            'owner': self.user_admin.pk,
            'version': self.document.doc_ver,
            'document_category' : self.document.doc_category,
        }
        form = FileSearchForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_invalid_file_search_form_missing_document_name(self):
        """Test invalid FileSearchForm with missing document name"""
        form_data = {
            'document_path': self.document.doc_url,
            'owner': self.user_admin.pk,
            'version': self.document.doc_ver,
            'document_category' : self.document.doc_category,
        }
        form = FileSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('document_name', form.errors)

    def test_invalid_file_search_form_missing_document_path(self):
        """Test invalid FileSearchForm with missing document path(url)"""
        form_data = {
            'document_name': self.document.doc_name,
            'owner': self.user_admin.pk,
            'version': self.document.doc_ver,
            'document_category' : self.document.doc_category,
        }
        form = FileSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('document_path', form.errors)

    def test_invalid_file_search_form_missing_document_owner(self):
        """Test invalid FileSearchForm with missing document owner"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_path': self.document.doc_url,
            'version': self.document.doc_ver,
            'document_category' : self.document.doc_category,
        }
        form = FileSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('owner', form.errors)

    def test_invalid_file_search_form_missing_document_version(self):
        """Test invalid FileSearchForm with missing document version"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_path': self.document.doc_url,
            'owner': self.user_admin.pk,
            'document_category' : self.document.doc_category,
        }
        form = FileSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('version', form.errors)

    def test_invalid_file_search_form_missing_document_category(self):
        """Test invalid FileSearchForm with missing document category"""
        form_data = {
            'document_name': self.document.doc_name,
            'document_path': self.document.doc_url,
            'owner': self.user_admin.pk,
            'version': self.document.doc_ver,
        }
        form = FileSearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('document_category', form.errors)

