import logging
import json
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta, datetime, time
from django.http import Http404, HttpResponseForbidden, JsonResponse
from django.views.generic import View, TemplateView, FormView, DetailView
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.models import Group

from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.mdf.forms import DocumentForm, DocumentApprovalForm
from managed_docu_familiarization.mdf.forms import FileSearchForm
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
from .AccessControlMixin import AccessControlMixin
from .tasks import check_document_deadlines
from .utils import get_documents_by_category, send_agreement, sendLinksToUsers, user_is_admin, \
    getDirectDownloadLink, getFileIdFromLink, generate_secure_link, verify_secure_link, send_mail_to_user, \
    send_link_to_complete_document, generate_document_link, verify_secure_id, document_progress_chart, \
    get_users_without_agreements, send_mail_to_multiple_user, get_embed_url_sharepoint, generate_preview_link, \
    is_from_google, get_sharepoint_url, fix_sharepoint_download_url, generate_secure_id
from django.http import HttpResponse

from ..users.models import User

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied


def open_document_base_page(request, enc_doc_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_page template
    :param request:
    :param enc_doc_id: encrypted document id (doc_id)
    :return: Redirect to a page document_page
    """
    request.session['selected_doc_id'] = enc_doc_id
    return redirect('mdf:document_page')  # Redirect to a page document_page

def open_document_stats(request, enc_doc_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_stats template
    :param request:
    :param enc_doc_id: encrypted document id (doc_id)
    :return: Redirect to a page document_stats
    """
    request.session['selected_doc_id'] = enc_doc_id
    return redirect('mdf:document_stats')  # Redirect to a page document_stats

def open_document_user_detail(request, user_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_stats template
    :param request:
    :param user_id: user id (zf_id)
    :return: Redirect to a page user_stats
    """
    request.session['selected_user_id'] = user_id
    return redirect('mdf:user_stats')  # Redirect to a page user_stats

def open_admin_add_document_page(request, doc_id):
    """
    Function saves value doc_id to request.session and redirects to mdf:admin_add_document_page template
    :param request:
    :param doc_id: document id (doc_id)
    :return: Redirect to a page admin_add_document_page
    """
    request.session['selected_doc_id_update'] = doc_id
    action = request.GET.get('action')
    base_url = reverse('mdf:admin_add_document_page',kwargs={'action': action})

    redirect_url = f"{base_url}?action={action}"
    return redirect(redirect_url)     # Redirect to a page admin_add_document_page

def open_document_approval(request, enc_doc_id):
    """
    Function saves value enc_doc_id to request.session and redirects to mdf:document_page template
    :param request:
    :param enc_doc_id: encrypted document id (doc_id)
    :return: Redirect to a page document_approval
    """
    request.session['selected_doc_id'] = enc_doc_id
    return redirect('mdf:document_approval')  # Redirect to a page document_approval


class MDFDocumentApprovalView(AccessControlMixin, LoginRequiredMixin, FormView):
    """
    View for responsible users to approve a document.
    This view handles the approval of a document by responsible users,
    checking permissions, and sending emails for further actions.
    """
    template_name = 'document_approval_page.html'

    form_class = DocumentApprovalForm
    document = None
    doc_id = None
    generated_link = None
    is_author = None
    is_approver = None

    permission_required = []  # List of required permissions for the view
    required_groups = [string_constants.mdf_admin_group_name, string_constants.mdf_authors_group_name]

    def check_user_groups(self, request):
        self.is_author = request.user.groups.filter(name="MDF_authors").exists()
        self.is_approver = request.user.groups.filter(name="MDF_approvers").exists()

        # If user is not in both required groups, return a forbidden response
        if not self.is_author or not self.is_approver:
            return HttpResponseForbidden("You do not have permission to view this page!")

    def dispatch(self, request, *args, **kwargs):
        # Check if the user belongs to the "MDF_authors" or "MDF_approvers" groups
        self.check_user_groups(request)

        # Retrieve document ID from the GET parameter or session
        get_doc_id = self.request.GET.get('enc_doc_id')
        if get_doc_id is None:
            get_doc_id = self.request.session.get('selected_doc_id')

        # If no document ID is provided, raise a 404 error
        if get_doc_id is None:
            raise Http404("Document URL not provided.")

        # Verify if the document exists using the decoded document ID
        doc_id = verify_secure_id(get_doc_id)
        self.doc_id = doc_id
        try:
            self.document = Document.objects.get(doc_id=doc_id)
        except Document.DoesNotExist:
            return HttpResponseForbidden("Document not found!")

        # Generate a link to the document approval page
        self.generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_id={generate_secure_link(self.document.doc_id)}"
        )

        # Proceed to dispatch the request to the next handler
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        # Initializes the form with the `document_url` and `document_name` values from the document
        initial = super().get_initial()
        initial['document_url'] = self.document.doc_url
        initial['document_name'] = self.document.doc_name
        return initial

    def get_context_data(self, **kwargs):
        # Adds document-related data to the context for rendering
        context = super().get_context_data(**kwargs)
        context['document'] = self.document
        context['document_category'] = Document.get_document_category_text(self.document)
        context['is_waiting_owner'] = self.document.is_waiting_owner
        context['is_owner'] = self.document.owner == self.request.user
        return context

    def post(self, request, *args, **kwargs):
        form = DocumentApprovalForm(request.POST)

        # If the form is valid, proceed with approval actions
        if form.is_valid():
            print("Form is valid")
            doc_id = request.POST.get('document_id')
            try:
                document = Document.objects.get(doc_id=doc_id)
            except Document.DoesNotExist:
                return HttpResponseForbidden("Document not found!")

            if document.is_waiting_owner:
                # Handle the case where the document is waiting for the owner's approval
                responsible_users = form.cleaned_data.get('responsible_users', [])
                if responsible_users:
                    document.responsible_users.set(
                        responsible_users if isinstance(responsible_users, list) else list(responsible_users))
                document.status = 'waiting'

                if request.user in set(responsible_users):
                    document.approved_by_users.add(request.user)
                encrypted_doc_id = generate_secure_link(document.doc_id)
                generated_link = request.build_absolute_uri(
                    reverse('mdf:document_approval') + f"?enc_doc_id={encrypted_doc_id}"
                )
                subject = "Document for approval"
                mess = string_constants.email_message_to_approve_document(generated_link)
                send_mail_to_multiple_user(responsible_users, subject, mess)
                document.save()
            else:
                # Handle the case where the document is not waiting for the owner
                if request.user in set(Document.get_responsible_users(document)):
                    if request.user not in set(document.approved_by_users):
                        document.approved_by_users.add(request.user)
                document.save()

            responsible_users = sorted(document.responsible_users.all(), key=lambda user: user.zf_id)
            approved_by_users = sorted(document.approved_by_users.all(), key=lambda user: user.zf_id)

            # Check if all responsible users have approved the document
            if responsible_users == approved_by_users:
                encrypted_doc_id = generate_secure_link(document.doc_id)
                generated_link = request.build_absolute_uri(
                    reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
                )
                # Send a link to the owner to complete the document
                send_link_to_complete_document(document, generated_link)
                document.status = 'uploaded'
                document.save()

            # Redirect to the success page after successful approval
            success_url = 'mdf:base_page'
            return redirect(success_url)

        # If form is invalid, render the form with errors
        print("Something went wrong")
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)

class MDFDocumentView(AccessControlMixin, LoginRequiredMixin, TemplateView):
    """
    View for user to display a document and send consent or download the document.
    User must be logged.
    """
    model = Document  # Document model
    template_name = 'document_view_page.html'
    doc_time = None  # Time of reading document
    permission_required = []  # Required permissions (if any)
    group_required = []  # Required user groups (if any)

    def __init__(self, **kwargs):
        # Initialize reading time to the current time
        super().__init__(**kwargs)
        self.doc_time = datetime.now()

    def post(self, request, *args, **kwargs):
        # Loading doc_id from request.GET
        get_doc_id = self.request.GET.get('doc_id')
        if get_doc_id is None:
            # If doc_id from request.GET is None, doc_id is loaded from request.session
            get_doc_id = self.request.session.get('selected_doc_id')

        # If get_doc_id is None, raise 404 error
        if get_doc_id is None:
            raise Http404("Document URL not provided.")

        # Decrypting doc_id from get_doc_id
        doc_id = verify_secure_id(get_doc_id)
        user = self.request.user
        document = Document.objects.get(doc_id=doc_id)

        # Submitting consent from form
        if 'consent' in request.POST:
            time_spent = int(request.POST.get('consent', 0))
            message = "Thank you for your consent."
            send_agreement(document, user, time_spent)
            return render(request, 'document_view_page.html', {'file_url': document.doc_url, 'message': message})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Getting doc_id from request.GET
        get_doc_id = self.request.GET.get('doc_id')
        if get_doc_id is None:
            # Getting doc_id from request.session
            get_doc_id = self.request.session.get('selected_doc_id')

        # If get_doc_id is None, raise 404 error
        if get_doc_id is None:
            raise Http404("Document URL not provided.")

        # Decrypting doc_id from get_doc_id
        doc_id = verify_secure_id(get_doc_id)

        try:
            # Loading document with doc_id
            document = Document.objects.get(doc_id=doc_id)
            category = document.category
        except Document.DoesNotExist:
            # Document does not exist - show error page
            raise Http404("The document was not found or you do not have access to it.")

        # Check if user has already sent consent to the document
        is_accepted = DocumentAgreement.objects.filter(document=document, user=self.request.user).exists()

        timestamp = now().timestamp()
        context['document'] = document
        context['is_from_google'] = is_from_google(document)
        context['doc_url_shp'] = get_sharepoint_url(document)
        context['document_url'] = generate_preview_link(document.doc_url) + f"?cache-bust={timestamp}"  # Embed URL to document in Google Drive
        context['category'] = category
        context['accepted'] = is_accepted
        context['file_url'] = getDirectDownloadLink(getFileIdFromLink(document.doc_url))
        context['file_url_sharepoint'] = fix_sharepoint_download_url(document)

        self.doc_time = datetime.now()

        return context

class MDFDocumentStatsView(AccessControlMixin, LoginRequiredMixin, TemplateView):
    """
    View for administrators and authors of documents to add details about document agreements.
    This view shows the document's agreement status, the users who have agreed to it,
    and provides the ability to send notifications.
    """
    template_name = 'document_stats_page.html'
    document = None
    permission_required = []  # List of required permissions for the view
    required_groups = [string_constants.mdf_admin_group_name, string_constants.mdf_authors_group_name]

    def get_context_data(self, **kwargs):
        # Get the encrypted document ID from the session
        enc_doc_id = self.request.session.get('selected_doc_id')
        if enc_doc_id is None:
            raise Http404("Document URL not provided.")

        # Decrypt the document ID
        doc_id = verify_secure_link(enc_doc_id)

        # Retrieve the document object or raise a 404 error if not found
        document = get_object_or_404(Document, doc_id=doc_id)
        self.document = document

        # Check if the document is uploaded
        is_uploaded = self.document.is_uploaded

        # If the document category is 3, process agreements
        if document.category == 3:
            is_admin = self.request.user.groups.filter(name="MDF_admin").exists()
            agreements_list = []

            # Check if the logged-in user is the document owner or an admin
            if self.request.user != document.owner and not is_admin:
                return render(self.request, 'error.html', {'message': 'You are not authorized to view this page.'})

            # Retrieve users associated with the document and their agreements
            users = document.get_users_from_groups()
            agreements = DocumentAgreement.objects.filter(document=document).select_related('user')
            agreement_map = {agreement.user: agreement for agreement in agreements}
            agreements_count = len(agreements)
            users_count = len(users)
            responsible_users = document.get_responsible_users()

            # Process each user to check their agreement status
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

            # Calculate the progress percentage of agreements
            progress_percentage = (agreements_count / users_count) * 100

            # Prepare context with the document details and agreements status
            context = {
                'agreements_count': agreements_count,
                'users_count': users_count,
                'document': document,
                'responsible_users': responsible_users,
                'agreements': agreements,
                'agreements_list': agreements_list,
                'is_uploaded': is_uploaded,
                'progress_percentage': progress_percentage,
                'graph_details': document_progress_chart(document),
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

            # Handle 'send_email_user' action to send email notifications to users without agreements
            if action == 'send_email_user':
                document_id = data.get('document_id')
                logger.error(f"Stats - Doc id: {document_id}")
                document = get_object_or_404(Document, doc_id=document_id)
                users = get_users_without_agreements(document)
                generated_link = generate_document_link(self.request, document)

                subject = string_constants.email_subject_notification
                message = f"Hello, please confirm that you have read the document.\nLink: {generated_link}"

                # Send email to users
                send_mail_to_multiple_user(users, subject, message)
                return JsonResponse({'status': 'success', 'message': 'E-mail sent.'})

            # Handle 'send_email_resp_users' action to send completion link to responsible users
            elif action == 'send_email_resp_users':
                document_id = data.get('document_id')
                document = get_object_or_404(Document, doc_id=document_id)
                encrypted_doc_id = generate_secure_link(document_id)
                generated_link = request.build_absolute_uri(
                    reverse('mdf:publishing_page') + f"?doc_id={encrypted_doc_id}"
                )

                # Send link to responsible users to complete document approval
                send_link_to_complete_document(document, generated_link)
                return JsonResponse({'status': 'success', 'message': 'E-mail sent.'})

        except Exception as e:
            # Handle any exceptions and return an error response
            return JsonResponse({'status': 'error', 'message': str(e)})


class MDFAdminDocumentAdd(AccessControlMixin, LoginRequiredMixin, FormView):
    """
    View for the admin to search for a document and generate a link for the owner.
    v0.1 - Demo version: without using emails, just displays the link.
    v0.2 - Advanced version: displays the link and sends the link to the owner.
    """

    template_name = 'document_admin_adding_page.html'
    form_class = FileSearchForm
    generated_link = None  # The link for the user, containing the document URL
    document = None
    action = None
    permission_required = []  # List of required permissions for the view
    required_groups = [string_constants.mdf_admin_group_name]

    def dispatch(self, request, *args, **kwargs):
        # Ensure that the user is an admin to access this view
        if not user_is_admin(request.user):
            return HttpResponseForbidden("You do not have permission to view this page.")

        # Get the action from the URL parameters
        self.action = self.request.GET.get('action')
        print(f"action = {self.action}")

        # If the action is 'update', retrieve the document to be updated from the session
        if self.action == 'update':
            doc_id = self.request.session.get('selected_doc_id_update')

            if doc_id is not None:
                self.document = Document.objects.get(doc_id=doc_id)
                # If document is not found, raise 404
                # raise Http404("Document not found!")

        # Continue the request handling
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        # Initializes the form with document details when updating an existing document
        initial = super().get_initial()

        if self.action == 'update' and self.document is not None:
            initial['document_path'] = self.document.doc_url
            initial['document_name'] = self.document.doc_name
            initial['owner'] = self.document.owner
            initial['responsible_users'] = self.document.responsible_users.all()

        return initial

    def get_context_data(self, **kwargs):
        """
        Prepares the context for the template to display the document details and generated link.
        """
        context = super().get_context_data(**kwargs)
        generated_link = None

        # Store the action in the session to retain it across requests
        context['action'] = self.action
        self.request.session['action'] = self.action

        # If the action is 'update', generate a secure link for the document
        if self.action == 'update' and self.document is not None:
            context['document'] = generate_secure_id(self.document.doc_id)

        context['generated_link'] = generated_link
        return context

    def post(self, request, *args, **kwargs):
        # Handle form submission to either add or update a document
        form = FileSearchForm(request.POST)
        generated_link = None

        if form.is_valid():
            # Retrieve action from session
            get_action = self.request.session.get('action')
            print(f"action is {get_action}")

            # Get form data for document details
            doc_name = form.cleaned_data['document_name']
            doc_url = form.cleaned_data['document_path']
            doc_owner = form.cleaned_data['owner']
            doc_category = form.cleaned_data['document_category']
            new_doc_version = form.cleaned_data['version']
            new_document = None
            responsible_users = form.cleaned_data.get('responsible_users', [])

            print("Valid form...")

            # If the action is 'add', create a new document
            if get_action == 'add':
                print("Adding new document...")
                new_document = Document.objects.create(
                    doc_name=doc_name,
                    doc_url=doc_url,
                    category='1',
                    owner=doc_owner,
                    doc_category=doc_category,
                    doc_ver=new_doc_version
                )
                new_document.status = 'waiting_owner'
                new_document.save()

            # If the action is 'update', update an existing document
            elif get_action == 'update':
                get_document = request.POST.get('document')
                document = Document.objects.get(doc_id=verify_secure_id(get_document))
                if document is None:
                    return HttpResponse("Something went wrong...")

                print("Updating document...")
                new_document = Document.save_new_version(document, doc_name, doc_url, doc_owner, responsible_users,
                                                         new_doc_version)
                new_document.status = 'waiting_owner'
                new_document.save()

            # If no document was created or updated, return an error message
            if new_document is None:
                return HttpResponse("Something went wrong...")

            # Create a secure link for the document owner
            doc_id = new_document.doc_id
            encrypted_doc_id = generate_secure_link(doc_id)  # Encrypt the document ID
            generated_link = request.build_absolute_uri(
                reverse('mdf:document_approval') + f"?enc_doc_id={encrypted_doc_id}"
            )

            # Send an email with the link to the document owner for approval
            message = string_constants.email_message_to_approve_document(generated_link)
            subject = "Document for approval"
            send_mail_to_user(new_document.owner, subject, message)

            # Redirect to the admin file search page after the document is processed
            success_url = 'mdf:admin_file_search_page'
            return redirect(success_url)

        # If the form is not valid, render the page with the form errors
        context = self.get_context_data()
        context['form'] = form
        context['generated_link'] = generated_link
        return self.render_to_response(context)


class MDFAdminDocumentList(AccessControlMixin, LoginRequiredMixin, TemplateView):
    """
    View for the admin to search for a document, add a document, or update/delete a document.
    """

    template_name = 'document_admin_view_page.html'
    generated_link = None  # The link for the user, which contains the document URL
    permission_required = []  # List of required permissions for this view
    required_groups = [string_constants.mdf_admin_group_name]  # Required group for access (admin only)

    def dispatch(self, request, *args, **kwargs):
        # Ensure that the user is an admin to access this view
        if not user_is_admin(request.user):
            return HttpResponseForbidden("You do not have permission to view this page.")
            # Raise PermissionDenied if needed: raise PermissionDenied
        # Continue handling the request if the user is an admin
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        # Prepares the context for the template to display the document list
        context = super().get_context_data(**kwargs)

        # Retrieve the latest documents from the database
        documents = Document.get_latest_documents()
        documents_list = []

        # For each document, create a list of dictionaries containing document details
        for document in documents:
            documents_list.append({
                'document': document,
                'document_category': Document.get_category_text(document),  # Get the document category text
                'document_status': Document.get_document_status_text(document),  # Get the document status text
                'encrypted_id': generate_secure_link(document.doc_id),  # Generate a secure link for the document ID
            })

        # Add the documents list and actions to the context
        context['documents_list'] = documents_list
        context['action_add'] = 'add'  # Action for adding a document
        context['action_update'] = 'update'  # Action for updating a document

        return context


class MDFDocumentsOverview(AccessControlMixin, LoginRequiredMixin, View):
    """
    View for displaying a table of documents. Each user will only see documents relevant to them.
    Owners will also see their documents, while admins can view all documents.
    """

    template_name = 'document_overview_page.html'  # Template for rendering the document overview page
    permission_required = []  # List of required permissions for access
    required_groups = []  # No specific groups required for this view

    def get(self, request, *args, **kwargs):
        # Retrieves the selected tab from the request (default is 'user' tab)
        tab = request.GET.get('tab', 'user')
        logger = logging.getLogger(__name__)  # Logger for debugging and tracking
        logger.error(f"Tab: {tab}")  # Logs the selected tab for reference

        # Check if the user belongs to the 'MDF_authors' and 'MDF_approvers' groups
        is_author = request.user.groups.filter(name="MDF_authors").exists()
        is_approver = request.user.groups.filter(name="MDF_approvers").exists()
        documents_list = []  # Initialize an empty list to store documents to be displayed

        # If the 'author' tab is selected and the user is an author
        if tab == 'author' and is_author:
            logger.error("I am in author")  # Logs when the user is in the author tab
            # Fetch the documents where the user is the owner
            my_documents = Document.get_latest_documents().filter(owner=request.user)
            for document in my_documents:
                # Prepare each document for the list with its category and a secure link
                documents_list.append({
                    'document': document,
                    'document_category': Document.get_category_text(document),
                    'encrypted_id': generate_secure_link(document.doc_id)
                })

        # If the 'approver' tab is selected and the user is an approver
        elif tab == 'approver' and is_approver:
            logger.error("I am in approver")  # Logs when the user is in the approver tab
            # Fetch documents assigned to the user for approval
            approving_documents = Document.get_latest_documents().filter(
                (Q(responsible_users=request.user) & Q(status='waiting')) |
                (Q(status='waiting_owner') & Q(owner=request.user))
            ).distinct()
            for document in approving_documents:
                # Prepare each document for the list with its category and a secure link
                documents_list.append({
                    'document': document,
                    'document_category': Document.get_category_text(document),
                    'encrypted_id': generate_secure_link(document.doc_id)
                })

        # For the default case, show documents the user is associated with
        else:
            document_filter = Document.get_latest_documents().filter(
                Q(groups__users=request.user),
                Q(status='pending') | Q(status='processed')
            ).distinct()
            for document in document_filter:
                # For category 3 documents, check if the user has already agreed to the document
                if document.category == 3:
                    consent_exists = DocumentAgreement.objects.filter(user=request.user, document=document).exists()
                else:
                    consent_exists = '-'

                # Logs the document name and consent status for debugging
                logger.error(f"doc name: {document.doc_name}, consent_exists: {consent_exists}")
                # Add document to the list with consent status (if applicable)
                documents_list.append({
                    'document': document,
                    'encrypted_id': generate_secure_link(document.doc_id),
                    'agree_exists': consent_exists
                })

        # Prepare the context to be passed to the template for rendering
        context = {
            'documents_list': documents_list,  # The list of documents to be displayed
            'is_author': is_author,  # Boolean to indicate if the user is an author
            'is_approver': is_approver,  # Boolean to indicate if the user is an approver
            'active_tab': tab,  # The currently active tab (author, approver, or user)
        }

        # Render the template with the provided context
        return render(request, self.template_name, context=context)


class MDFDocumentsAdding(AccessControlMixin, LoginRequiredMixin, FormView):
    """
    View for owners to add a document to the database and add additional information.
    After adding a document, the program will choose certain users and send them an email (this feature will be added later).
    """
    template_name = 'document_author_page.html'  # Template for rendering the page

    form_class = DocumentForm  # Form for document details
    success_url = '/mdf/mdfdocuments/overview/'  # Redirect URL after successfully saving the document
    document = None  # Placeholder for document object
    doc_id = None  # Document ID
    generated_link = None  # Generated secure link for the document
    permission_required = []  # List of required permissions (not used here)
    required_groups = [string_constants.mdf_authors_group_name]  # Only users in this group can access the page

    def dispatch(self, request, *args, **kwargs):
        """
        Handles the incoming request. Ensures the user is an author and has access to the document.
        """
        is_author = request.user.groups.filter(name="MDF_authors").exists()  # Check if the user is in the authors group
        if not is_author:
            return HttpResponseForbidden("You do not have permission to view this page!")  # Deny access if not an author

        # Retrieve and decrypt the document ID from the URL
        doc_id = self.request.GET.get('doc_id', '')
        decrypted_id = verify_secure_link(doc_id)
        self.doc_id = decrypted_id

        try:
            self.document = Document.objects.get(doc_id=decrypted_id)  # Get the document using the decrypted ID
        except Document.DoesNotExist:
            return HttpResponseForbidden("Document not found!")  # Return an error if the document doesn't exist

        # Generate a secure link for the document
        self.generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_id={generate_secure_link(self.document.doc_id)}"
        )

        # Proceed with rendering the page
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Pass additional arguments to the form (document link and name).
        """
        kwargs = super().get_form_kwargs()
        kwargs['document_link'] = self.generated_link  # Pass the generated document link to the form
        kwargs['document_name'] = self.document.doc_name  # Pass the document name to the form
        return kwargs

    def get_initial(self):
        """
        Initialize the form with the document's URL and name.
        """
        initial = super().get_initial()
        initial['url'] = self.document.doc_url  # Pre-fill the form with the document URL
        initial['name'] = self.document.doc_name  # Pre-fill the form with the document name
        return initial

    def get_context_data(self, **kwargs):
        """
        Pass additional context data to the template.
        """
        context = super().get_context_data(**kwargs)
        context['is_uploaded'] = self.document.is_uploaded  # Indicates if the document is uploaded or not
        context['info_text'] = string_constants.info_text  # Pass some informational text to the template
        return context

    def form_valid(self, form):
        """
        Handle form submission when the form is valid.
        Saves the document and sends notifications to users.
        """
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")
        if not self.request.user.is_authenticated:  # Ensure the user is authenticated
            logger.error("User not authenticated.")
            return self.form_invalid(form)

        # Fetch the document from the database
        document = Document.objects.get(doc_id=self.doc_id)
        if document is None:
            return HttpResponseForbidden("Document not found!")

        # Retrieve the category from the form
        doc_category = form.cleaned_data['category']
        logger.error(f"Document category: {doc_category}")

        document.category = doc_category  # Set the document category
        users = form.cleaned_data.get('contact_users', [])  # Get the users to be contacted

        # If users are selected, set them as the contact users for the document
        if users:
            document.contact_users.set(users if isinstance(users, list) else list(users))

        # Handling for different document categories
        if doc_category == '1':  # Private document
            logger.error("Private document...")
            allusers_group = Group.objects.filter(name=string_constants.all_users_group_name).first()
            if allusers_group:
                document.groups.set([allusers_group])
            else:
                logger.error("'allusers' group not found.")
            document.status = 'processed'

        elif doc_category == '2':  # Category 2 document
            document.status = 'processed'

        elif doc_category == '3':  # Category 3 document with a deadline
            logger.error("Setting deadline for category 3 document...")
            deadline_date = form.cleaned_data.get('deadline')
            if deadline_date:
                # Set the deadline time to 23:59
                deadline_datetime = timezone.make_aware(datetime.combine(deadline_date, time(23, 59)))
                document.deadline = deadline_datetime
            document.status = 'pending'

        # Save the document and send links to users
        message = form.cleaned_data['message']
        generated_link = self.request.build_absolute_uri(
            reverse('mdf:document_page') + f"?doc_id={generate_secure_link(document.doc_id)}"
        )
        document.save()  # Save the document to the database
        sendLinksToUsers(document, generated_link, message)  # Send the generated link to users
        return redirect(self.success_url)  # Redirect to the success page

    def form_invalid(self, form):
        """
        Handle form submission when the form is invalid.
        Logs form errors for debugging.
        """
        logger = logging.getLogger(__name__)
        logger.error("Form is invalid!")
        logger.error(f"Form errors: {form.errors}")
        logger.error(f"POST data: {self.request.POST}")
        print("Form errors:", form.errors)  # Print errors to the console
        print("Form data:", form.data)  # Print form data to the console
        return super().form_invalid(form)  # Render the form with errors


class MDFDocumentsUserDetailView(AccessControlMixin, LoginRequiredMixin, TemplateView):
    """
    View for administrators to display details about a user's document agreements.
    Admins can see the documents a user has agreed to and their agreement details.
    """
    template_name = 'document_user_detail_page.html'  # Template for rendering the page
    model = Document  # Model to use (Document in this case)
    permission_required = []  # List of required permissions (not used here)
    required_groups = [string_constants.mdf_admin_group_name]  # Only users in the admin group can access

    def get_context_data(self, **kwargs):
        """
        Retrieves the context data for rendering the page, including the user's document agreements.
        """
        context = super().get_context_data(**kwargs)

        # Retrieve the selected user ID from the session
        user_id = self.request.session.get('selected_user_id')

        if user_id is None:
            raise Http404("User ID not provided.")  # Raise error if no user ID is found in the session

        # Fetch the user based on the provided user ID
        user = User.objects.filter(zf_id=user_id).first()  # Retrieve the user by 'zf_id'

        if user is None:
            raise Http404("User does not exist!")  # Raise error if the user is not found

        documents_list = []  # List to store the documents and their agreement details

        # Filter documents assigned to the user with category 3 (documents requiring user agreement)
        document_filter = Document.objects.filter(groups__users=user, category=3).distinct()

        # Iterate over the filtered documents
        for document in document_filter:
            # Check if the user has agreed to the document
            consent_exists = DocumentAgreement.objects.filter(user=user, document=document).exists()

            if consent_exists:
                # If agreement exists, retrieve it and the agreement date
                agreement = DocumentAgreement.objects.get(user=user, document=document)
                agreed_at = agreement.agreed_at.strftime('%d.%m.%Y')  # Format the agreement date
            else:
                # If no agreement exists, set placeholders
                agreement = '-'
                agreed_at = '-'

            # Add document and agreement information to the documents list
            documents_list.append({
                'document': document,  # The document object
                'agreement_exists': consent_exists,  # Whether the user has agreed to the document
                'agreement': agreement,  # The agreement object (if exists)
                'agreed_at': agreed_at,  # Date of agreement (if exists)
            })

        # Add the documents list and user object to the context
        context['documents_list'] = documents_list
        context['user'] = user

        return context  # Return the context for rendering the template
