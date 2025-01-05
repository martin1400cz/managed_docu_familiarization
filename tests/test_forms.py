from django.test import TestCase
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import Group

from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.users.models import User
from managed_docu_familiarization.mdf.forms import DocumentForm
from managed_docu_familiarization.mdf.models import Document

class DocumentFormTestCase(TestCase):


    def setUp(self):
        # Vytvoření uživatelů a skupin pro testování
        #self.user1 = User.objects.create(username='user1', email='user1@example.com')
        #self.user2 = User.objects.create(username='user2', email='user2@example.com')
        self.group1 = Group.objects.create(name="Test Group")
        self.user1 = User.objects.create_user(
            zf_id="Z123456",
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            is_staff=True,
        )
        self.group2 = Group.objects.create(name="Test Group 2")
        self.user2 = User.objects.create_user(
            zf_id="Z654321",
            email="test2@example.com",
            first_name="Adam",
            last_name="Oed",
            is_staff=True,
        )
        #self.user1 = User.objects.get(zf_id='ZADMIN')
        #self.user2 = User.objects.get(zf_id='ZUSER1')
        #self.group1 = Group.objects.get(name='allusers')
        #self.group2 = Group.objects.get(name='MDF_authors')

        # Mockovaný odkaz na dokument
        self.document_link = "http://example.com/document"

    def test_valid_form(self):
        # Platná data pro formulář
        form_data = {
            'name': 'Test Document',
            'url': 'http://example.com/test-doc',
            'contact_users': [self.user1.pk, self.user2.pk],
            'category': 3,  # Private documents
            'groups': [self.group1.pk],
            'deadline': (now() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'message': string_constants.email_message_for_users(self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_invalid_url(self):
        # Test s neplatnou URL
        form_data = {
            'name': 'Invalid URL Document',
            'url': 'not-a-valid-url',
            'contact_users': [self.user1.pk],
            'category': 3,  # Public documents
            'deadline': (now() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'message': string_constants.email_message_for_users(self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)

    def test_missing_required_fields(self):
        # Test chybějících povinných polí
        form_data = {
            'url': 'http://example.com/missing-fields',
            'contact_users': [self.user1.pk],
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('category', form.errors)

    def test_category_choices(self):
        # Test nepovolené kategorie
        form_data = {
            'name': 'Test Invalid Category',
            'url': 'http://example.com/invalid-category',
            'contact_users': [self.user1.pk],
            'category': 99,  # Neplatná volba
            'deadline': (now() + timedelta(days=7)).strftime('%d/%m/%Y'),
            'message': string_constants.email_message_for_users(self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_deadline_format(self):
        # Test neplatného formátu data
        form_data = {
            'name': 'Test Deadline',
            'url': 'http://example.com/deadline',
            'contact_users': [self.user1.pk],
            'category': 3,
            'deadline': '31-12-2025',  # Nesprávný formát
            'message': string_constants.email_message_for_users(self.document_link),
        }
        form = DocumentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('deadline', form.errors)

    def test_message_initialization(self):
        # Test inicializace pole 'message' pomocí `document_link`
        form = DocumentForm(document_link=self.document_link)
        expected_initial = f"This is your message template: {self.document_link}"
        expected_initial = string_constants.email_message_for_users(self.document_link)
        self.assertEqual(form.fields['message'].initial, expected_initial)

    def test_readonly_fields(self):
        # Ověření, že pole 'name' a 'url' mají atribut readonly
        form = DocumentForm()
        self.assertIn('readonly', form.fields['name'].widget.attrs)
        self.assertIn('readonly', form.fields['url'].widget.attrs)
