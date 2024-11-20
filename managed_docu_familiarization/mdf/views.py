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
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
import os
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from .utils import send_document_link, get_documents_by_category, send_agreement, getUsersFromGroups
from django.http import HttpResponse

from ..users.models import User


#import requests


class MDFDocumentDetailView(TemplateView):
    model = Document
    template_name = 'doc_page.html'  # Šablona pro zobrazení dokumentu
    def post(self, request, *args, **kwargs):
        doc_url = self.request.GET.get('doc_url')
        user = self.request.user
        document = Document.objects.get(doc_url=doc_url)
        if 'consent' in request.POST:
            if doc_url is None:
                raise Http404("URL dokumentu nebyla poskytnuta.")
            # Zde můžete přidat logiku, co dělat po přijetí souhlasu (např. ukládání do databáze)
            message = "Děkujeme za váš souhlas."
            send_agreement(document, user)
            return render(request, 'doc_page.html', {'file_url': doc_url, 'message': message})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Získání doc_url z GET parametrů
        doc_url = self.request.GET.get('doc_url')
        category = None

        if doc_url is None:
            raise Http404("URL dokumentu nebyla poskytnuta.")

        # Ověření, že dokument existuje
        try:
            document = Document.objects.get(doc_url=doc_url)
            category = document.category
        except Document.DoesNotExist:
            raise Http404("Dokument nebyl nalezen nebo k němu nemáte přístup.")

        context['document_url'] = doc_url
        context['category'] = category
        return context

'''
Function for getting a direct link to file saved on Google drive
'''
def getDirectDownloadLink(fileId):
    directLink = f"https://drive.google.com/uc?export=download&id={fileId}"
    return directLink
'''
Function for getting a file id from link
'''
def getFileIdFromLink(sharedLink):
    return sharedLink.split('/d/')[1].split('/')[0]

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
'''
View for document owner to show stats about who agreed with his document
'''
def MDFDocumentAgreementView(request, document_id):
    document = get_object_or_404(Document, doc_id=document_id)
    #users = getUsersFromGroups(document.groups)
    # Zkontrolujeme, jestli je přihlášený uživatel vlastníkem dokumentu
    if request.user != document.owner:
        return render(request, 'error.html', {'message': 'Nemáte oprávnění zobrazit tuto stránku.'})

    # Načtení souhlasů spojených s dokumentem
    agreements = DocumentAgreement.objects.filter(document=document).select_related('user')
    agreements_count = len(agreements)
    #users_count = len(users)
    users_count = 3
    context = {
        'agreements_count': agreements_count,
        'users_count':users_count,
        'document': document,
        'agreements': agreements,
    }

    return render(request, 'document_stats.html', context)


# Prepared function for sending document link to owner.
# Not used!
def send_link_to_owner(request, owner, generated_link):
    logger = logging.getLogger(__name__)

    owner_email = owner.email
    logger.error(f"Owners mail: {owner_email}")
    # Text e-mailu
    subject = "Dokument k doplnění informací"
    message = f"Ahoj {owner.first_name} {owner.last_name},\n\n" \
              f"Prosím klikni na následující odkaz a doplň informace o dokumentu:\n{generated_link}\n\n" \
              f"Děkujeme!"
    from_email = settings.EMAIL_HOST_USER
    logger.error(f"From mail: {from_email}")
    # Odeslání e-mailu
    send_mail(subject, message, from_email, [owner_email],fail_silently=False)
    success_url = '/mdf/mdfdocuments/admin-file-search/'
    # Zobrazení zprávy o úspěšném odeslání
    messages.success(request, f"E-mail s odkazem byl odeslán na adresu {owner_email}")
    return redirect(success_url)  # Vrátíme se na stránku se seznamem dokumentů

# View for admin to search a document and generate link for owner
# This is demo version - without using emails, just display the link!
class MDFAdminSearchDocument(TemplateView):
    template_name = 'admin_file_search_page.html'
    # @login_required
    generated_link = None   # link for user, contains document url

    def get_context_data(self, **kwargs):
        generated_link = None
        #BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        #DOCUMENTS_DIRECTORY = os.path.join(BASE_DIR, 'TestDocs/')
        #DOCUMENTS_DIRECTORY = settings.DOCUMENTS_DIRECTORY
        context = super().get_context_data(**kwargs)
        context['form'] = FileSearchForm()

        # Load a list of files in DOCUMENTS_DIRECTORY
        '''available_files = os.listdir(DOCUMENTS_DIRECTORY)  # Assuming a flat structure for simplicity
        document_links = [
            {
                "name": file_name,
                "url": f"{reverse('mdf:publishing_page')}?document_url={os.path.join(DOCUMENTS_DIRECTORY, file_name)}"
            }
            for file_name in available_files
        ]'''

        #context['documents'] = document_links
        context['generated_link'] =  generated_link
        #context['available_files'] = available_files
        #context['DOCUMENTS_PATH'] = DOCUMENTS_DIRECTORY
        return context

    def post(self, request, *args, **kwargs):
        form = FileSearchForm(request.POST)
        generated_link = None

        if form.is_valid():
            doc_url = form.cleaned_data['document_path']
            #BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            #document_url = getFileIdFromLink(doc_url)
            owner = form.cleaned_data['owner']
            # Generování URL s parametrem `doc_url`
            generated_link = request.build_absolute_uri(
                reverse('mdf:publishing_page') + f"?doc_url={doc_url}"
            )
            send_link_to_owner(request, owner, generated_link)


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
            tab = request.GET.get('tab', 'user')
            logger = logging.getLogger(__name__)
            logger.error(f"Tab: {tab}")
            is_admin = request.user.groups.filter(name="MDF_admin").exists()
            is_owner = request.user.groups.filter(name="MDF_authors").exists()
            documents = Document.objects.all()
            my_documents = []
            documents_list = []
            if tab == 'admin' and is_admin:
                logger.error("I am in admin")
                documents = Document.objects.all()
            elif tab == 'author' and is_owner:
                logger.error("I am in author")
                my_documents = Document.objects.filter(owner=request.user)
            else:
                document_filter = Document.objects.filter(groups__users=request.user, category=3).distinct()


                for document in document_filter:
                    consent_exists = DocumentAgreement.objects.filter(user=request.user, document=document).exists()
                    documents_list.append({
                        'document': document,
                        'agree_exists': consent_exists
                    })

            #mdf_documents1 = Document.objects.filter(groups__users=request.user).distinct()
            #mdf_documents2 = Document.objects.filter(owner=request.user)
            # Combination of two querysets for documents for user in certain groups and for request user's documents
            #combined_queryset = mdf_documents1.union(mdf_documents2)

            #print(mdf_documents)
            context = {
                'mdf_documents': documents,
                'my_documents': my_documents,
                'documents_list': documents_list,
                'is_admin': is_admin,
                'is_author': is_owner,
                'active_tab': tab,
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
    '''
    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")
        user_ids = self.request.POST.get('contact_users', '').split(',')
        users = User.objects.filter(id__in=user_ids)
        post_data = self.request.POST.copy()
        post_data.setlist('contact_users', [str(user.id) for user in users])
        if self.request.user.is_authenticated:

            logger.error("User authenticated...")
            doc_owner = self.request.user
            # Uložení záznamu do databáze
            document = Document.objects.create(
                doc_name=form.cleaned_data['name'],
                doc_url=form.cleaned_data['url'],
                category=form.cleaned_data['category'],
                owner=doc_owner
            )
            document.contact_users.set(users)
            if form.cleaned_data['groups']:
                groups = form.cleaned_data['groups']
                if not isinstance(groups, list):
                    logger.error("'Groups' is not a list...")
                    groups_list = list(groups)
                    if groups_list:
                        document.groups.set(groups_list)
                        return redirect(self.success_url)

                if groups:
                    document.groups.set(groups)

            return redirect(self.success_url)
        '''

    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("User being authenticated...")

        # Načíst ID uživatelů z POST dat
        user_ids = self.request.POST.get('contact_users', '').split(',')

        try:
            # Načíst odpovídající uživatele jako instance
            users = User.objects.filter(id__in=user_ids)

            # Kopírovat POST data a nastavit validní hodnoty pro contact_users
            post_data = self.request.POST.copy()
            post_data.setlist('contact_users', [str(user.id) for user in users])

            # Aktualizovat formulář daty s validní hodnotou
            form = self.get_form(self.form_class)
            form.data = post_data
        except Exception as e:
            logger.error(f"Error processing users: {e}")
            return self.form_invalid(form)

        if not self.request.user.is_authenticated:
            logger.error("User not authenticated.")
            return self.form_invalid(form)

        logger.error("User authenticated...")
        doc_owner = self.request.user

        # Uložení dokumentu
        document = Document.objects.create(
            doc_name=form.cleaned_data['name'],
            doc_url=form.cleaned_data['url'],
            category=form.cleaned_data['category'],
            owner=doc_owner
        )
        document.contact_users.set(users)  # Nastavení uživatelů

        # Zpracování skupin, pokud existují
        groups = form.cleaned_data.get('groups', [])
        if groups:
            document.groups.set(groups if isinstance(groups, list) else list(groups))

        return redirect(self.success_url)

    def form_invalid(self, form):
        logger = logging.getLogger(__name__)
        logger.error("Form is invalid!")
        logger.error(f"Errors: {form.errors}")
        logger.error(f"POST data: {self.request.POST}")
        print("Form errors:", form.errors)  # Vypsání chyb do konzole
        return super().form_invalid(form)
