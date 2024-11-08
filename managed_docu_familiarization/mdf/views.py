import logging
import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.views.generic import View, TemplateView, FormView, DetailView
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib.auth.models import Group

from config import settings
from managed_docu_familiarization.mdf.forms import DocumentForm
from managed_docu_familiarization.mdf.forms import FileSearchForm
from managed_docu_familiarization.mdf.models import Document
import os
from django.conf import settings
from django.contrib import messages
from .utils import send_document_link


class MDFDocumentDetailView(TemplateView):
    model = Document
    template_name = 'doc_page.html'  # Šablona pro zobrazení dokumentu

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Získání doc_url z GET parametrů
        doc_url = self.request.GET.get('doc_url')

        if doc_url is None:
            raise Http404("URL dokumentu nebyla poskytnuta.")

        # Ověření, že dokument existuje
        try:
            document = Document.objects.get(doc_url=doc_url, owner=self.request.user)
        except Document.DoesNotExist:
            raise Http404("Dokument nebyl nalezen nebo k němu nemáte přístup.")

        context['document'] = document
        return context


# Prepared function for sending document link to owner.
# Not used!
def send_link_to_owner(request, file_name):
    # Assume you get the owner's email or username from the request context or through form input
    # owner_username = request.GET.get('owner_username')  # For example, you can pass this as a query parameter
    # You might want to validate the user, ensure they exist, etc.

    # Generate the document URL
    document_url = f"http://localhost:8000/mdf/mdfdocuments/overview/add/?file_name={file_name}"

    # Here you could send an email or just save the link to the session, etc.
    messages.success(request, f"Link generated: {document_url}")

    # Redirect back to file search or admin page
    return redirect('mdf:admin_file_search_page')  # Change to the appropriate URL name

# View for admin to search a document and generate link for owner
# This is demo version - without using emails, just display the link!
class MDFAdminSearchDocument(TemplateView):
    template_name = 'admin_file_search_page.html'
    # @login_required

    '''
    def get(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        if request.user.is_authenticated:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            DOCUMENTS_DIRECTORY = os.path.join(BASE_DIR, 'TestDocs/')
            # if not os.path.exists(settings.DOCUMENTS_DIRECTORY):
            if not os.path.exists(DOCUMENTS_DIRECTORY):
                messages.error(request, "Document directory does not exist. Neco se deje...")
                return render(request, 'mdf:admin_file_search_page.html', {'available_files': []})

            try:
                generated_link = None
                if request.method == 'POST':
                    logger.error("We are POST...")
                    form = FileSearchForm(request.POST)
                    if form.is_valid():
                        logger.error("We are valid...")
                        document_url = form.cleaned_data['document_path']
                        # owner = form.cleaned_data['owner']
                        # Ensure the document exists in the defined directory
                        # document_full_path = os.path.join(settings.DOCUMENTS_DIRECTORY, document_path)
                        document_full_path = os.path.join(DOCUMENTS_DIRECTORY, document_url)
                        if not os.path.exists(document_full_path):
                            messages.error(request, "Document not found.")
                            return redirect('mfd:admin_file_search_page')

                        # Create or update the document entry
                        #document, created = Document.objects.get_or_create(
                        #    doc_url=document_url,
                        #    defaults={'owner': owner, 'doc_name': os.path.basename(document_url)}
                        #)
                        #document.owner = owner
                        #document.save()
                        # document_url = f"http://localhost:8000/mdf/mdfdocuments/overview/add/?file_name={document_full_path}"
                        # Send the document link to the owner
                        # send_document_link(document)
                        # messages.success(request, f"Document link sent to {owner.email}")
                        generated_link = request.build_absolute_uri(
                            reverse('mdf:publishing_page') + f"?document_url={document_full_path}"
                        )
                        #return redirect('mdf:admin_file_search_page')
                else:
                    form = FileSearchForm()

                # List files for selection (adjust this part to fit your file structure)
                # available_files = os.listdir(settings.DOCUMENTS_DIRECTORY)  # Assuming a flat structure for simplicity
                available_files = os.listdir(DOCUMENTS_DIRECTORY)  # Assuming a flat structure for simplicity
                document_links = [
                    {
                        "name": file_name,
                        "url": f"{reverse('mdf:publishing_page')}?document_url={os.path.join(DOCUMENTS_DIRECTORY, file_name)}"
                    }
                    for file_name in available_files
                ]
                return render(request, self.template_name, {'form': form, 'generated_link': generated_link, 'available_files': available_files, 'document_links' : document_links})
            except FileNotFoundError:
                messages.error(request, "Unable to list files, directory may not exist.")
                available_files = []
    '''

    generated_link = None   # link for user, contains document url

    def get_context_data(self, **kwargs):
        generated_link = None
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DOCUMENTS_DIRECTORY = os.path.join(BASE_DIR, 'TestDocs/')
        #DOCUMENTS_DIRECTORY = settings.DOCUMENTS_DIRECTORY
        context = super().get_context_data(**kwargs)
        context['form'] = FileSearchForm()

        # Load a list of files in DOCUMENTS_DIRECTORY
        available_files = os.listdir(DOCUMENTS_DIRECTORY)  # Assuming a flat structure for simplicity
        document_links = [
            {
                "name": file_name,
                "url": f"{reverse('mdf:publishing_page')}?document_url={os.path.join(DOCUMENTS_DIRECTORY, file_name)}"
            }
            for file_name in available_files
        ]

        context['documents'] = document_links
        context['generated_link'] =  generated_link
        context['available_files'] = available_files
        context['DOCUMENTS_PATH'] = DOCUMENTS_DIRECTORY
        return context

    def post(self, request, *args, **kwargs):
        form = FileSearchForm(request.POST)
        generated_link = None

        if form.is_valid():
            doc_url = form.cleaned_data['document_path']
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            document_url = os.path.join(BASE_DIR, doc_url)
            # Generování URL s parametrem `doc_url`
            generated_link = request.build_absolute_uri(
                reverse('mdf:publishing_page') + f"?doc_url={document_url}"
            )

        # Opětovné načtení kontextu pro zobrazení stejné stránky
        context = self.get_context_data()
        context['form'] = form
        context['generated_link'] = generated_link
        return self.render_to_response(context)

# View for table of documents. Each user will see only documents for him. Owners will also see their documents
# Admin will see all documents.
class MDFDocumentsOverview(View):

    template_name = 'base_page.html'

    #@login_required
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            #mdf_documents = Document.objects.all()
            #mdf_documents = None
            is_admin = request.user.groups.filter(name="MDF_authors").exists()
            #if(is_admin):
            #    mdf_documents = Document.objects.all().distinct()
            #else:
            #    mdf_documents = Document.objects.filter(groups__users=request.user).distinct()

            mdf_documents = Document.objects.filter(groups__users=request.user).distinct()
            #print(mdf_documents)

            context = {
                'mdf_documents' : mdf_documents,
                'is_admin' : is_admin,
            }

            return render(request, self.template_name, context=context)
        else:
            return render(request, 'app/templates/registration/login.html')  # Redirect to login if not authenticated

# View for owners to add a document to database and add information. After adding a groups, program will choose certain users and will send them an email - this will be added later.
class MDFDocumentsAdding(FormView):

    template_name = 'publishing_page.html'

    form_class = DocumentForm
    success_url = '/mdf/mdfdocuments/overview/'  # Po uložení záznamu do databáze
    doc_owner = None

    def get_initial(self):
        # Inicializuje formulář s hodnotou `doc_url` z URL parametrů

        initial = super().get_initial()
        initial['url'] = self.request.GET.get('doc_url', '')
        return initial

    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")
        if self.request.user.is_authenticated:

            logger.error("User authenticated...")
            doc_owner = self.request.user
            # Uložení záznamu do databáze
            Document.objects.create(
                doc_name=form.cleaned_data['name'],
                doc_url=form.cleaned_data['url'],
                category=form.cleaned_data['category'],
                #groups=form.cleaned_data['groups'],
                #groups = filter(lambda t: t[0] in form.cleaned_data['groups'], form.fields['groups'].),
                owner=doc_owner
            )
            if form.cleaned_data['groups']:
                Document.groups.set(form.cleaned_data['groups'])

            return redirect(self.success_url)

    def form_invalid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("Invalid form!")
        # Zobrazíme chyby, pokud je formulář nevalidní
        print("Form is invalid:", form.errors)  # Zobrazí chyby formuláře v konzoli
        return super().form_invalid(form)
    '''
    # @login_required
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            owner = request.user
            # Handle the form for adding a new document
            doc_url = request.POST.get('document_url')
            # document = get_object_or_404(Document, doc_url=doc_url)
            document_url = request.GET.get('document_url')
            if request.method == 'POST':

                # form handling code here (e.g., saving a new document)
                form = DocumentForm(request.POST)
                # form.url.
                if form.is_valid():
                     document = form.save(commit=False)
                    if form.cleaned_data['category'] in [2, 3]:
                        form.cleaned_data['groups'] = form.cleaned_data['groups'] | Group.objects.filter('allusers')
                    document.save()
                    form.save_m2m()  # Save groups relation
                    return redirect('base_page')
            else:
                form = DocumentForm()
                context = {
                    'form': form,
                    'url': doc_url
                }
                return render(request, self.template_name, context=context)
        return redirect('base_page')
        '''
