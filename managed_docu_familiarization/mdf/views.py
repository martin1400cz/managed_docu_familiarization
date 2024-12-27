import logging
import os
import json
from django.core.exceptions import PermissionDenied
from django.db.models import Subquery
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime, time

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView, FormView, DetailView
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.models import Group

from config import settings
from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.mdf.forms import DocumentForm
from managed_docu_familiarization.mdf.forms import FileSearchForm
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
import os
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from .utils import get_documents_by_category, send_agreement, sendLinksToUsers, user_is_admin, \
    getDirectDownloadLink, getFileIdFromLink, generate_secure_link, verify_secure_link, send_mail_to_user, \
    send_link_to_owner_and_responsible_users, generate_document_link
from django.http import HttpResponse

from ..users.models import User


#import requests

class MDFDocumentView(LoginRequiredMixin, TemplateView):
    """

    """
    model = Document
    template_name = 'document_view_page.html'
    #doc_time = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.doc_time = datetime.now()

    def post(self, request, *args, **kwargs):
        doc_url = self.request.GET.get('doc_url')
        user = self.request.user
        document = Document.objects.get(doc_url=doc_url)
        if 'consent' in request.POST:
            time_spent = int(request.POST.get('consent', 0))
            if doc_url is None:
                raise Http404("Document URL not provided")
            # Zde můžete přidat logiku, co dělat po přijetí souhlasu (např. ukládání do databáze)
            message = "Thank you for your consent."
            #time_user = datetime.now() - self.doc_time
            #formatted_time = time(hour=time_spent // 3600, minute=(time_spent % 3600) // 60, second=time_spent % 60)
            send_agreement(document, user, time_spent)
            return render(request, 'document_view_page.html', {'file_url': doc_url, 'message': message})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Získání doc_url z GET parametrů
        doc_url = self.request.GET.get('doc_url')
        category = None

        if doc_url is None:
            raise Http404("Document URL not provided.")

        # Ověření, že dokument existuje
        try:
            document = Document.objects.get(doc_url=doc_url)
            category = document.category
        except Document.DoesNotExist:
            raise Http404("The document was not found or you do not have access to it.")
        is_accepted = DocumentAgreement.objects.filter(document=document, user=self.request.user).exists()
        #is_ordinary_user = not self.request.user.groups.filter(name="MDF_admin").exists()
        context['document_url'] = doc_url
        context['category'] = category
        context['accepted'] = is_accepted
        #context['is_ordinary_user'] = is_ordinary_user
        context['document_google_id'] = getFileIdFromLink(doc_url)
        context['file_url'] = getDirectDownloadLink(getFileIdFromLink(doc_url))
        self.doc_time = datetime.now()
        return context


'''
def download_google_drive_file(file_url):
    response = requests.get(file_url)
    if response.status_code == 200:
        # Uložení souboru na disk
        with open('downloaded_file', 'wb') as file:
            file.write(response.content)
        print("Soubor byl úspěšně stažen.")
    else:
        print("Chyba při stahování souboru.")
'''


class MDFDocumentStatsView(LoginRequiredMixin, TemplateView):
    """
    View for administrator/authors of documents for detail informations about document agreements.
    """
    template_name = 'document_stats_page.html'
    document = None
    def get_context_data(self, **kwargs):
        doc_id = self.request.GET.get('doc_id')
        dec_id = verify_secure_link(doc_id) # Decrypted document id (doc_id)

        document = get_object_or_404(Document, doc_id=dec_id)
        self.document = document
        # groups = document.groups.all()
        is_uploaded = self.document.is_uploaded
        if document.category == 3:
            is_admin = self.request.user.groups.filter(name="MDF_admin").exists()
            agreements_list = []
            # Check if logged user is admin
            if self.request.user != document.owner and not is_admin:
                return render(self.request, 'error.html', {'message': 'You are not authorized to view this page.'})

            # Agreements...

            users = document.get_users_from_groups()
            agreements = DocumentAgreement.objects.filter(document=document).select_related('user')
            agreement_map = {agreement.user: agreement for agreement in agreements}
            agreements_count = len(agreements)
            users_count = len(users)
            responsible_users = document.get_responsible_users()

            for user in users:
                if user in agreement_map:
                    agreement = agreement_map[user]
                    reading_time = agreement.reading_time
                    open_count = agreement.open_count
                    formatted_date = agreement.agreed_at.strftime('%d/%m/%Y')
                    agreements_list.append({
                        'user': user,
                        'status': string_constants.user_agreed,
                        'agreed_at': formatted_date,
                        'reading_time': reading_time,
                        'open_count': open_count,
                    })
                else:
                    agreements_list.append({
                        'user': user,
                        'status': string_constants.user_no_agree_yet,
                        'agreed_at': '-',
                        'reading_time': '-',
                        'open_count': 0,
                    })
            context = {
                'agreements_count': agreements_count,
                'users_count': users_count,
                'document': document,
                'responsible_users': responsible_users,
                'agreements': agreements,
                'agreements_list': agreements_list,
                'is_uploaded': is_uploaded,
            }
        else:
            context = {
                'document': document,
                'is_uploaded': is_uploaded,
            }

        return context

    def post(self, request, *args, **kwargs):
        try:
            logger = logging.getLogger(__name__)
            logger.error("Stats - jsme v post!")
            data = json.loads(request.body)
            action = data.get('action')
            if action == 'send_email_user':
                user_id = data.get('user_id')
                logger.error(f"Stats - User id: {user_id}")
                document_id = data.get('document_id')
                logger.error(f"Stats - Doc id: {document_id}")

                user = get_object_or_404(User, zf_id=user_id)

                document = get_object_or_404(Document, doc_id=document_id)
                generated_link = generate_document_link(self.request, document)
                subject = string_constants.email_subject_notification
                message = f"Hello, please confirm that you have read the document.\nLink: {generated_link}"

                send_mail_to_user(user, subject, message)
                return JsonResponse({'status': 'success', 'message': 'E-mail sent.'})
            elif action == 'send_email_resp_users':
                document_id = data.get('document_id')
                document = get_object_or_404(Document, doc_id=document_id)
                encrypted_doc_id = generate_secure_link(document_id)
                generated_link = request.build_absolute_uri(
                    reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
                )
                send_link_to_owner_and_responsible_users(request, document, generated_link)
                return JsonResponse({'status': 'success', 'message': 'E-mail sent.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

class MDFAdminSearchDocument(LoginRequiredMixin, TemplateView):
    """
    View for admin to search a document and generate link for owner
    v0.1 - This is demo version - without using emails, just display the link!
    v0.2 - Advanced version - displays the link + sends the link to the owner.
    """

    template_name = 'document_admin_page.html'
    generated_link = None   # link for user, contains document url

    def dispatch(self, request, *args, **kwargs):
        if not user_is_admin(request.user):
            return HttpResponseForbidden("You do not have permission to view this page.")
            #raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        generated_link = None
        context = super().get_context_data(**kwargs)
        context['form'] = FileSearchForm()

        context['generated_link'] =  generated_link
        return context

    def post(self, request, *args, **kwargs):
        form = FileSearchForm(request.POST)
        generated_link = None

        if form.is_valid():
            doc_owner = form.cleaned_data['owner']
            document = Document.objects.create(
                doc_name=form.cleaned_data['document_name'],
                doc_url=form.cleaned_data['document_path'],
                category='1',
                owner=doc_owner
            )
            responsible_users = form.cleaned_data.get('responsible_users', [])
            if responsible_users:
                document.responsible_users.set(responsible_users if isinstance(responsible_users, list) else list(responsible_users))
                document.save()

            doc_id = document.doc_id
            encrypted_doc_id = generate_secure_link(doc_id)
            # Generování URL s parametrem `doc_url`
            generated_link = request.build_absolute_uri(
                reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
            )
            send_link_to_owner_and_responsible_users(request, document, generated_link)
            success_url = '/mdf/mdfdocuments/admin-file-search/'
            return redirect(success_url)


        # Opětovné načtení kontextu pro zobrazení stejné stránky
        context = self.get_context_data()
        context['form'] = form
        context['generated_link'] = generated_link
        return self.render_to_response(context)


class MDFDocumentsOverview(LoginRequiredMixin, View):
    """
    View for table of documents. Each user will see only documents for him. Owners will also see their documents
    Admin will see all documents.
    """
    template_name = 'document_overview_page.html'

    #@login_required
    def get(self, request, *args, **kwargs):
        tab = request.GET.get('tab', 'user')
        logger = logging.getLogger(__name__)
        logger.error(f"Tab: {tab}")
        is_admin = request.user.groups.filter(name="MDF_admin").exists()
        is_owner = request.user.groups.filter(name="MDF_authors").exists()
        if tab == 'admin' and is_admin:
            documents_list = []
            logger.error("I am in admin")
            documents = Document.objects.all()
            for document in documents:
                documents_list.append({
                    'document': document,
                    'encrypted_id': generate_secure_link(document.doc_id)
                })
        elif tab == 'author' and is_owner:
            documents_list = []
            logger.error("I am in author")
            my_documents = Document.objects.filter(owner=request.user)
            for document in my_documents:
                documents_list.append({
                    'document': document,
                    'encrypted_id': generate_secure_link(document.doc_id)
                })
        else:
            documents_list = []
            # document_filter = Document.objects.filter(groups__users=request.user, category=3).distinct()
            document_filter = Document.objects.filter(Q(groups__users=request.user),
                                                      Q(status='pending') | Q(status='processed')).distinct()
            for document in document_filter:
                if document.category == 3:
                    consent_exists = DocumentAgreement.objects.filter(user=request.user, document=document).exists()
                else:
                    consent_exists = '-'

                logger.error(f"doc name: {document.doc_name}, consent_exists: {consent_exists}")
                documents_list.append({
                    'document': document,
                    'encrypted_id': generate_secure_link(document.doc_id),
                    'agree_exists': consent_exists
                })

        # If request user is admin -> it should not open a basic view for user, however admin must see what other users do
        # if is_admin:
        #    #logger.error(f"Tab: {tab}")
        #    if tab is 'user':
        #        tab = 'admin'

        # print(mdf_documents)
        context = {
            # 'mdf_documents': documents,
            # 'my_documents': my_documents,
            'documents_list': documents_list,
            'is_admin': is_admin,
            'is_author': is_owner,
            'active_tab': tab,
        }

        return render(request, self.template_name, context=context)


class MDFDocumentsAdding(LoginRequiredMixin, FormView):
    """
    View for owners to add a document to database and add information. After adding a groups, program will choose certain users and will send them an email - this will be added later.
    """
    template_name = 'document_author_page.html'

    form_class = DocumentForm
    success_url = '/mdf/mdfdocuments/overview/'  # Po uložení záznamu do databáze
    document = None
    doc_id = None
    generated_link = None

    def dispatch(self, request, *args, **kwargs):
        doc_id = self.request.GET.get('doc_id', '')
        decrypted_id = verify_secure_link(doc_id)
        self.doc_id = decrypted_id
        try:
            self.document = Document.objects.get(doc_id=decrypted_id)
        except Document.DoesNotExist:
            return HttpResponseForbidden("Document not found!")
        self.generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_url={self.document.doc_url}"
        )
        #self.form_class = DocumentForm(request.POST, document_link=generated_link)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """
        Vrátí instanci formuláře s předvyplněnými hodnotami a generovaným odkazem.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(
            initial=self.get_initial(),
            document_link=self.generated_link
        )

    def get_initial(self):
        # Inicializuje formulář s hodnotou `doc_url` z URL parametrů

        initial = super().get_initial()
        #self.doc_url = self.request.GET.get('doc_url', '')
        #self.document = Document.objects.get(doc_id=decrypted_id)
        #self.document = get_object_or_404(Document, doc_id=decrypted_id)
        #if self.document is None:
            #return HttpResponseForbidden("Document not found!")

        initial['url'] = self.document.doc_url


        initial['name'] = self.document.doc_name
        #initial['message'] = string_constants.email_message_for_users
        return initial

    def get_context_data(self, **kwargs):
        #print("KWARGS:", kwargs)  # Debugging
        context = super().get_context_data(**kwargs)
        context['is_uploaded'] = self.document.is_uploaded  # If document is in 'uploaded' status - if it is in 'pending' status or another, user cannot add details about document
        return context

    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")
        if not self.request.user.is_authenticated:
            logger.error("User not authenticated.")
            return self.form_invalid(form)
        document = Document.objects.get(doc_id=self.doc_id)
        logger.error("User authenticated...")
        if document is None:
            return HttpResponseForbidden("Document not found!")
        doc_owner = self.request.user
        doc_category = form.cleaned_data['category']

        document.category = doc_category
        users = form.cleaned_data.get('contact_users', [])
        if users:
            document.contact_users.set(users if isinstance(users, list) else list(users))

        # Get groups
        groups = form.cleaned_data.get('groups', [])
        if groups:
            document.groups.set(groups if isinstance(groups, list) else list(groups))
        else:
            allusers_group = Group.objects.filter(name='allusers').first()
            if allusers_group:
                document.groups.set([allusers_group])
                document.save()
            else:
                logger.error("'allusers' group not found.")

        logger.error(f"Document category: {doc_category}")
        if doc_category == '1':
            logger.error("Private document...")
            allusers_group = Group.objects.filter(name='allusers').first()
            if allusers_group:
                document.groups.set([allusers_group])
                #document.save()
            else:
                logger.error("'allusers' group not found.")
        if doc_category == '3':
            logger.error("Setting deadline for category 3 document...")
            #document.deadline = form.cleaned_data.get('deadline')
            deadline_date = form.cleaned_data.get('deadline')
            if deadline_date:
                # Setting deadline time to 23:59
                deadline_datetime = timezone.make_aware(datetime.combine(deadline_date, time(23, 59)))
                document.deadline = deadline_datetime
        message = form.cleaned_data['message']
        generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_url={document.doc_url}"
        )
        document.status = 'pending'
        # Saving document
        document.save()
        sendLinksToUsers(document, generated_link, message)
        return redirect(self.success_url)

    def form_invalid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("Form is invalid!")
        logger.error(f"Errors: {form.errors}")
        logger.error(f"POST data: {self.request.POST}")
        print("Form errors:", form.errors)  # Vypsání chyb do konzole
        return super().form_invalid(form)
