import logging

from django.core.mail import send_mail
from datetime import timedelta
from django.urls import reverse
from django.conf import settings
from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
from managed_docu_familiarization.users.models import User
from django.core.signing import Signer, BadSignature
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
import re



def generate_secure_link(doc_id):
    """
    Function returns encrypted doc_id
    :param doc_id:
    :return:
    """
    signer = Signer()
    signed_doc_id = signer.sign(doc_id)
    return signed_doc_id

def verify_secure_link(signed_doc_id):
    """
    Function returns decrypted doc_id
    :param signed_doc_id:
    :return:
    """
    signer = Signer()
    try:
        doc_id = signer.unsign(signed_doc_id)
        return doc_id
    except BadSignature:
        return None

def generate_secure_id(n_id):
    """
    Function returns encrypted id
    :param n_id:
    :return:
    """
    signer = Signer()
    signed_id = signer.sign(n_id)
    return signed_id

def verify_secure_id(signed_id):
    """
    Function returns decrypted id
    :param signed_id:
    :return:
    """
    signer = Signer()
    try:
        en_id = signer.unsign(signed_id)
        return en_id
    except BadSignature:
        return None

# Google Drive
def is_from_google(document):
    """
    Function returns if a document is from Google Drive
    :param document:
    :return:
    """
    return string_constants.google_drive_prefix in document.doc_url

def get_sharepoint_url(document):
    """
    Function returns transformed document url from Sharepoint
    :param document:
    :return:
    """
    # URL parsing
    parsed_url = urlparse(document.doc_url)
    # removing an /r/ parameter from path "/r/"
    fixed_path = re.sub(r"/r/", "/", parsed_url.path)
    # Parameter processing
    query_params = parse_qs(parsed_url.query)
    # Let's make sure it contains "?web=1"
    query_params["web"] = ["1"]
    # Build a fixed URL
    fixed_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        fixed_path,
        parsed_url.params,
        urlencode(query_params, doseq=True),
        parsed_url.fragment
    ))
    return fixed_url

def fix_sharepoint_download_url(document):
    """
    Opraví SharePoint URL tak, aby soubor byl přímo stažen místo otevření v prohlížeči.
    """
    parsed_url = urlparse(document.doc_url)

    # Oprava cesty – odstranění "/r/"
    fixed_path = re.sub("", "", parsed_url.path)

    # Úprava parametrů – odstranění nepotřebných a přidání "download=1"
    query_params = parse_qs(parsed_url.query)

    # Odstraníme nepotřebné parametry
    query_params.pop("csf", None)
    query_params.pop("e", None)

    # Přidáme "download=1"
    query_params["download"] = ["1"]

    # Vytvoření nové URL
    fixed_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        fixed_path,
        parsed_url.params,
        urlencode(query_params, doseq=True),
        parsed_url.fragment
    ))
    print(f"Fixed URL: {fixed_url}")
    return fixed_url

def getFileIdFromLink(sharedLink):
    """
    Function returns a file id from url - Google drive
    """
    try:
        return sharedLink.split('/d/')[1].split('/')[0]
    except IndexError as e:
        return 'testId'

def getDirectDownloadLink(fileId):
    """
    Function for getting a direct link to file saved on Google drive
    """
    directLink = f"https://drive.google.com/uc?export=download&id={fileId}"
    return directLink

def generate_preview_link(file_url):
    """
    Creates a preview link based on a shared Google Drive link.
    """
    parsed_url = urlparse(file_url)
    if 'drive.google.com' in parsed_url.netloc and '/file/d/' in parsed_url.path:
        file_id = parsed_url.path.split('/d/')[1].split('/')[0]
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return file_url  # Returns the original URL if it is not a Google Drive link

# Sharepoint
def get_embed_url_sharepoint(document):
    """
    Transforms a URL obtained from SharePoint into an Embed URL.
    """
    base_embed_url = "https://trw1.sharepoint.com/sites/ManagedDocumentationFamiliarization-shared/_layouts/15/Doc.aspx"
    # Extracting a filename from a URL
    file_name = document.doc_url.split("/")[-1].split("?")[0]

    document_id = get_document_id_from_sharepoint(document)
    # Creating an Embed URL
    embed_url = f"{base_embed_url}?sourcedoc={document_id}&file={file_name}&action=embedview"
    return embed_url

def get_document_id_from_sharepoint(document):
    """
    Function returns an ID of file on SharePoint
    :param document:
    :return: Document id from document url
    """
    return "PLACEHOLDER_DOCUMENT_ID"

def extract_document_id_from_embed_url_sharepoint(document):
    """
    Extracts the unique document ID (if needed) from a relative or absolute URL.
    Prerequisite: Documents are at an absolute URL that contains the sourcedoc ID
    """
    if "sourcedoc=" in document.doc_url:
        return document.doc_url.split("sourcedoc=")[1].split("&")[0]
    # If sourcedoc is not available, it returns a placeholder or work with another extraction method.
    return "PLACEHOLDER_DOCUMENT_ID"

###################################################################
def generate_document_link(request, document):
    """
    Function generates a link for a document
    :param request:
    :param document:
    :return:
    """
    generated_link = request.build_absolute_uri(
        reverse('mdf:document_page') + f"?doc_id={generate_secure_link(document.doc_id)}"
    )
    return generated_link


def generate_document_link_task(document, domain=None, protocol="https"):
    """
    function generates a link for document to document view page
    """
    if not domain:
        domain = getattr(settings, "SITE_DOMAIN", "localhost:8000")

    relative_path = reverse('mdf:document_page') + f"?doc_id={generate_secure_link(document.doc_id)}"
    return f"{protocol}://{domain}{relative_path}"

def user_is_admin(user):
    """
    Checking if the user is a member of the administrators group.
    """
    return user.is_authenticated and user.groups.filter(name=string_constants.mdf_admin_group_name).exists()

def get_documents_by_category(category):
    """
    Function returns a documents by publishing category
    :param category:
    :return:
    """
    return Document.objects.get(category=category)

def send_agreement(document, user, time_spent):
    """
    Function creates a new record of a document agreement
    :param document:
    :param user:
    :param time_spent:
    :return:
    """
    DocumentAgreement.objects.create(
        user=user,
        document=document,
        reading_time=time_spent,
    )
    return True

def get_users_accepted_count(document):
    """
    Function returns a count of users who has sent an agreement
    :param document:
    :return:
    """
    return len(DocumentAgreement.objects.filter(document=document))

def get_users_accepted(document):
    """
    Function returns users who has sent an agreement
    :param document:
    :return:
    """
    return User.objects.filter(document_stats__document=document).distinct()

def get_users_without_agreements(document):
    """
    Function returns users who have not sent an agreement
    :param document:
    :return:
    """
    all_users = document.get_users_from_groups()
    users_agreed = get_users_accepted(document)
    return list(set(all_users) - set(users_agreed))

def exists_users_agreement(user, document):
    """
    Function returns if user has send an agreement
    :param user:
    :param document:
    :return:
    """
    return DocumentAgreement.objects.filter(user=user, document=document).exists()

# emails

def send_link_to_complete_document(document, generated_link):
    """
    Function for sending a generated link with document url to a document author for adding other informations
    """
    subject = "Adding information to a document"
    #from_email = settings.EMAIL_HOST_USER
    send_mail_to_user(document.owner, subject, string_constants.email_message_to_complete_document(generated_link, document.doc_name))


def send_mail_to_user(user, subject, message):
    """
    Function sends an email to an user
    :param user:
    :param subject:
    :param message:
    :return:
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [user.email], fail_silently=False)

def send_mail_to_multiple_user(users, subject, message):
    """
    Function sends email to multiple users using send_email_to_user function
    :param users: list of users
    :param subject: email subject
    :param message: email message
    """
    for user in users:
        send_mail_to_user(user, subject, message)

def sendLinksToUsers(document, generated_link, mess):
    """
    Function send emails with link to users
    :param document:
    :param generated_link:
    :param mess:
    :return:
    """
    users = document.get_users_from_groups()
    subject = string_constants.email_subject_accept
    # Sending emails
    for user in users:
        send_mail_to_user(user, subject, mess)

def notify_users_about_document_deadline(document):
    """
    Function to send notifications to users about the expiration of a document.
    """
    users = document.get_users_from_groups()
    subject = f'Deadline expired for document {document.doc_name}'
    message = f'Hello\n'\
              f'The deadline for the document "{document.doc_name}" has expired.\n' \
              f'Please confirm that you have read the document.\n'
    for user in users:
        if not exists_users_agreement(user, document):
            send_mail_to_user(user, subject, message)

def notify_owner_about_document_deadline(document):
    """
    Function to send notifications to document owner about the expiration of a document.
    :param document: Document from which the necessary data is obtained
    """
    subject = f'Deadline expired for document {document.doc_name}'
    message = f'The deadline for the document "{document.doc_name}" has expired. Please take necessary action.'
    send_mail_to_user(document.owner, subject, message)


def document_progress_chart(document):
    """
    The method processes data for a progress chart
    :param document: The document for which the data is intended
    :return: Dictionary for context
    """
    # Get data range
    responses = DocumentAgreement.objects.filter(document=document).order_by('-agreed_at')

    # Last agreement (by date)
    if responses.exists():
        last_agreement_date = responses.order_by('-agreed_at').first().agreed_at.date()
    else:
        last_agreement_date = document.deadline.date()  # Default value

    # Getting date range
    start_date = document.release_date.date()
    end_date = max(last_agreement_date, document.deadline.date())

    current_date = start_date
    data_points = []
    agreed_count = 0
    data_points.append({
        'date': current_date.strftime('%d.%m.%Y'),
        'count': agreed_count,
    })
    while current_date <= end_date:

        if responses.filter(agreed_at__date=current_date).count() > 0:
            agreed_count += responses.filter(agreed_at__date=current_date).count()
            data_points.append({
                'date': current_date.strftime('%d.%m.%Y'),
                'count': agreed_count,
            })
        elif document.deadline.date() == current_date:
            data_points.append({
                'date': current_date.strftime('%d.%m.%Y'),
                'count': agreed_count,
            })
        current_date += timedelta(days=1)

    # Data extraction
    labels = [point['date'] for point in data_points]
    counts = [point['count'] for point in data_points]

    return {
        'labels': labels,
        'counts': counts,
        'deadline': document.deadline.strftime('%d.%m.%Y'),
    }
