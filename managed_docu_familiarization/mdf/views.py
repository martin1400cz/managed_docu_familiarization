import logging
import os
import json
from django.core.exceptions import PermissionDenied
from django.db.models import Subquery
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta, datetime, time

from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView, FormView, DetailView
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.models import Group

from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.mdf.forms import DocumentForm
from managed_docu_familiarization.mdf.forms import FileSearchForm
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
from .utils import get_documents_by_category, send_agreement, sendLinksToUsers, user_is_admin, \
    getDirectDownloadLink, getFileIdFromLink, generate_secure_link, verify_secure_link, send_mail_to_user, \
    send_link_to_owner_and_responsible_users, generate_document_link, verify_secure_id, document_progress_chart, \
    get_users_without_agreements, send_mail_to_multiple_user, get_embed_url_sharepoint, generate_preview_link, \
    is_from_google, get_sharepoint_url, fix_sharepoint_download_url
from django.http import HttpResponse

from ..users.models import User


#import requests

class MDFDocumentView(LoginRequiredMixin, TemplateView):
    """
    View for user to display a document and send consent or download the document
    User must be logged
    """
    model = Document
    template_name = 'document_view_page.html'
    #doc_time = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.doc_time = datetime.now()

    def post(self, request, *args, **kwargs):
        doc_id = self.request.GET.get('doc_id')
        if doc_id is None:
            raise Http404("Document URL not provided")
        user = self.request.user
        document = Document.objects.get(doc_id=verify_secure_id(doc_id))
        if 'consent' in request.POST:
            time_spent = int(request.POST.get('consent', 0))
            message = "Thank you for your consent."
            #time_user = datetime.now() - self.doc_time
            #formatted_time = time(hour=time_spent // 3600, minute=(time_spent % 3600) // 60, second=time_spent % 60)
            send_agreement(document, user, time_spent)
            return render(request, 'document_view_page.html', {'file_url': document.doc_url, 'message': message})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Getting doc_id from request session
        enc_doc_id = self.request.session.get('selected_doc_id')

        category = None

        if enc_doc_id is None:
            raise Http404("Document URL not provided.")
        # check if document exists
        doc_id = verify_secure_id(enc_doc_id)
        try:
            #document = Document.objects.get(doc_url=doc_url)
            document = Document.objects.get(doc_id=doc_id)
            category = document.category
        except Document.DoesNotExist:
            #document does not exist - show error page
            raise Http404("The document was not found or you do not have access to it.")
        is_accepted = DocumentAgreement.objects.filter(document=document, user=self.request.user).exists()
        timestamp = now().timestamp()
        context['document'] = document
        context['is_from_google'] = is_from_google(document)
        context['doc_url_shp'] = get_sharepoint_url(document)
        context['document_url'] = generate_preview_link(document.doc_url) + f"?cache-bust={timestamp}"  # Embed url to document in Google Drive
        print(f"Doc_url: {get_sharepoint_url(document)}")
        context['category'] = category
        context['accepted'] = is_accepted
        #context['embed_url'] = get_embed_url_sharepoint(document) # Sharepoint embed url
        context['file_url'] = getDirectDownloadLink(getFileIdFromLink(document.doc_url))
        context['file_url_sharepoint'] = fix_sharepoint_download_url(document)
        #print(f"embed Doc_url: {get_embed_url_sharepoint(document)}")
        self.doc_time = datetime.now()
        return context

class MDFDocumentStatsView(LoginRequiredMixin, TemplateView):
    """
    View for administrator/authors of documents for detail informations about document agreements.
    """
    template_name = 'document_stats_page.html'
    document = None
    def get_context_data(self, **kwargs):
        #doc_id = self.request.GET.get('doc_id')
        enc_doc_id = self.request.session.get('selected_doc_id')
        if enc_doc_id is None:
            raise Http404("Document URL not provided.")
        doc_id = verify_secure_link(enc_doc_id) # Decrypted document id (doc_id)

        document = get_object_or_404(Document, doc_id=doc_id)
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
                    formatted_date = agreement.agreed_at.strftime('%d.%m.%Y')
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
            progress_percentage = (agreements_count/users_count)*100
            context = {
                'agreements_count': agreements_count,
                'users_count': users_count,
                'document': document,
                'responsible_users': responsible_users,
                'agreements': agreements,
                'agreements_list': agreements_list,
                'is_uploaded': is_uploaded,
                'progress_percentage': progress_percentage,
                'graph_details' : document_progress_chart(document),
                'document_category': Document.get_category_text(document),
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
            data = json.loads(request.body)
            action = data.get('action')
            if action == 'send_email_user':
                document_id = data.get('document_id')
                logger.error(f"Stats - Doc id: {document_id}")
                document = get_object_or_404(Document, doc_id=document_id)
                users = get_users_without_agreements(document)
                generated_link = generate_document_link(self.request, document)

                subject = string_constants.email_subject_notification
                message = f"Hello, please confirm that you have read the document.\nLink: {generated_link}"

                send_mail_to_multiple_user(users, subject, message)
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

class MDF_admin_document_add(LoginRequiredMixin, TemplateView):
    """
    View for admin to search a document and generate link for owner
    v0.1 - This is demo version - without using emails, just display the link!
    v0.2 - Advanced version - displays the link + sends the link to the owner.
    """

    template_name = 'document_admin_adding_page.html'
    generated_link = None   # link for user, contains document url
    document = None

    def dispatch(self, request, *args, **kwargs):
        if not user_is_admin(request.user):
            return HttpResponseForbidden("You do not have permission to view this page.")
            #raise PermissionDenied
        doc_id = self.request.session.get('selected_doc_id_update')

        if doc_id is not None:
            self.document = Document.objects.get(doc_id=doc_id)
            #raise Http404("Document not find!")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        generated_link = None
        action = self.request.GET.get('a')
        print(f"Action: {action}")
        if action == 'set':
            print("Setting....")
            documents = Document.get_latest_documents()
            context['documents'] = documents
            context['is_updating'] = True
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
            generated_link = request.build_absolute_uri(
                reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
            )
            send_link_to_owner_and_responsible_users(request, document, generated_link)
            success_url = '/mdf/mdfdocuments/admin-file-search/'
            return redirect(success_url)


        context = self.get_context_data()
        context['form'] = form
        context['generated_link'] = generated_link
        return self.render_to_response(context)

class MDF_admin_document_list(LoginRequiredMixin, TemplateView):
    """
    View for admin to search a document, add document or update/delete document
    """

    template_name = 'document_admin_view_page.html'
    generated_link = None   # link for user, contains document url

    def dispatch(self, request, *args, **kwargs):
        if not user_is_admin(request.user):
            return HttpResponseForbidden("You do not have permission to view this page.")
            #raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documents = Document.get_latest_documents()
        documents_list = []
        for document in documents:
            documents_list.append({
                'document': document,
                'encrypted_id': generate_secure_link(document.doc_id),
            })
        context['documents_list'] = documents_list
        context['is_updating'] = True
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
            generated_link = request.build_absolute_uri(
                reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
            )
            send_link_to_owner_and_responsible_users(request, document, generated_link)
            success_url = '/mdf/mdfdocuments/admin-file-search/'
            return redirect(success_url)


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
        is_author = request.user.groups.filter(name="MDF_authors").exists()
        if tab == 'admin' and is_admin:
            documents_list = []
            logger.error("I am in admin")
            documents = Document.objects.all()
            for document in documents:
                documents_list.append({
                    'document': document,
                    'document_category': Document.get_category_text(document),
                    'encrypted_id': generate_secure_link(document.doc_id)
                })
        elif tab == 'author' and is_author:
            documents_list = []
            logger.error("I am in author")
            my_documents = Document.objects.filter(owner=request.user)
            for document in my_documents:
                documents_list.append({
                    'document': document,
                    'document_category': Document.get_category_text(document),
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
            'is_author': is_author,
            'active_tab': tab,
        }

        return render(request, self.template_name, context=context)


def open_document_base_page(request, enc_doc_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_page template
    :param request:
    :param enc_doc_id: encrypted document id (doc_id)
    :return:
    """
    request.session['selected_doc_id'] = enc_doc_id
    return redirect('mdf:document_page')  # Redirect to a page document_page

def open_document_stats(request, enc_doc_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_stats template
    :param request:
    :param enc_doc_id: encrypted document id (doc_id)
    :return:
    """
    request.session['selected_doc_id'] = enc_doc_id
    return redirect('mdf:document_stats')  # Redirect to a page document_page

def open_document_user_detail(request, user_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_stats template
    :param request:
    :param user_id: user id (zf_id)
    :return:
    """
    request.session['selected_user_id'] = user_id
    return redirect('mdf:user_stats')  # Redirect to a page document_page

def open_admin_file_search(request, doc_id):
    """
    Function saves value doc_id to request.session and redirects to mdf:admin_add_document_page template
    :param request:
    :param doc_id: document id (doc_id)
    :return:
    """
    request.session['selected_doc_id_update'] = doc_id
    return redirect('mdf:admin_add_document_page')  # Redirect to a page document_page


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
        is_author = request.user.groups.filter(name="MDF_authors").exists()
        if not is_author:
            return HttpResponseForbidden("You do not have permission to view this page!")
        doc_id = self.request.GET.get('doc_id', '')
        decrypted_id = verify_secure_link(doc_id)
        self.doc_id = decrypted_id
        try:
            self.document = Document.objects.get(doc_id=decrypted_id)
        except Document.DoesNotExist:
            return HttpResponseForbidden("Document not found!")
        self.generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_id={generate_secure_link(self.document.doc_id)}"
        )
        #self.form_class = DocumentForm(request.POST, document_link=generated_link)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['document_link'] = self.generated_link
        kwargs['document_name'] = self.document.doc_name
        return kwargs

    def get_initial(self):
        # Initializes the form with the `doc_url` and `doc_name` values from the URL parameters

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
        context['info_text'] = string_constants.info_text
        return context

    def form_valid(self, form):
        print("We are in valid form!")
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")
        if not self.request.user.is_authenticated:
            logger.error("User not authenticated.")
            return self.form_invalid(form)
        document = Document.objects.get(doc_id=self.doc_id)
        #document = self.document
        #logger.error("User authenticated...")
        if document is None:
            return HttpResponseForbidden("Document not found!")
        doc_category = form.cleaned_data['category']
        logger.error(f"Document category: {doc_category}")

        document.category = doc_category
        users = form.cleaned_data.get('contact_users', [])
        if users:
            document.contact_users.set(users if isinstance(users, list) else list(users))

        # Document category 1
        if doc_category == '1':
            logger.error("Private document...")
            allusers_group = Group.objects.filter(name=string_constants.all_users_group_name).first()
            if allusers_group:
                document.groups.set([allusers_group])
                #document.save()
            else:
                logger.error("'allusers' group not found.")

            document.status = 'processed'
            # Saving document
            document.save()
            return redirect(self.success_url)

        # Get groups
        groups = form.cleaned_data.get('groups', [])
        if groups:
            document.groups.set(groups if isinstance(groups, list) else list(groups))
        else:
            allusers_group = Group.objects.filter(name=string_constants.all_users_group_name).first()
            if allusers_group:
                document.groups.set([allusers_group])
                document.save()
            else:
                logger.error("'allusers' group not found.")

        # Document category 3
        if doc_category == '2':
            document.status = 'processed'

        # Document category 3
        if doc_category == '3':
            logger.error("Setting deadline for category 3 document...")
            #document.deadline = form.cleaned_data.get('deadline')
            deadline_date = form.cleaned_data.get('deadline')
            if deadline_date:
                # Setting deadline time to 23:59
                deadline_datetime = timezone.make_aware(datetime.combine(deadline_date, time(23, 59)))
                document.deadline = deadline_datetime
            document.status = 'pending'

        message = form.cleaned_data['message']
        generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_id={generate_secure_link(document.doc_id)}"
        )
        # Saving document
        document.save()
        sendLinksToUsers(document, generated_link, message)
        return redirect(self.success_url)

    def form_invalid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("Form is invalid!")
        logger.error(f"Form errors: {form.errors}")
        logger.error(f"POST data: {self.request.POST}")
        print("Form errors:", form.errors)  # Writing errors to the console
        print("Form data:", form.data)
        return super().form_invalid(form)

class MDFDocumentsUserDetailView(LoginRequiredMixin, TemplateView):
    """
    View for administrators to display details about user's document agreements
    """
    template_name = 'document_user_detail_page.html'
    model = Document
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #user_id = self.request.GET.get('user_id')
        user_id = self.request.session.get('selected_user_id')
        if user_id is None:
            raise Http404("User id not provided.")
        # Verifying that a document exists
        user = User.objects.filter(zf_id=user_id).first()
        if user_id is None:
            raise Http404("User not exists!")
        documents_list = []
        document_filter = Document.objects.filter(groups__users=user, category=3).distinct()
        print(Document.objects.filter(groups__users=user, category=3).distinct())
        # document_filter = Document.objects.filter(groups__users=user, category=3).all()
        for document in document_filter:
            consent_exists = DocumentAgreement.objects.filter(user=user, document=document).exists()
            print(f"Consent exists: {consent_exists}")
            if consent_exists:
                agreement = DocumentAgreement.objects.get(user=user, document=document)
                print(f"Agreement: {agreement}")
                agreed_at = agreement.agreed_at.strftime('%d.%m.%Y')
            else:
                agreement = '-'
                agreed_at = '-'
            documents_list.append({
                'document': document,
                'agreement_exists': consent_exists,
                'agreement': agreement,
                'agreed_at': agreed_at,
            })
        context['documents_list'] = documents_list
        context['user'] = user
        return context
