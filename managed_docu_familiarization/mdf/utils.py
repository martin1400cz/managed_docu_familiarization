import logging

from django.core.mail import send_mail
from datetime import timedelta
from django.urls import reverse
from django.conf import settings
from managed_docu_familiarization.static.Strings import string_constants
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
from managed_docu_familiarization.users.models import User
from django.core.signing import Signer, BadSignature


def generate_secure_link(doc_id):
    signer = Signer()
    signed_doc_id = signer.sign(doc_id)
    return signed_doc_id

def verify_secure_link(signed_doc_id):
    signer = Signer()
    try:
        doc_id = signer.unsign(signed_doc_id)
        return doc_id
    except BadSignature:
        return None

def generate_secure_id(n_id):
    signer = Signer()
    signed_id = signer.sign(n_id)
    return signed_id

def verify_secure_id(signed_id):
    signer = Signer()
    try:
        en_id = signer.unsign(signed_id)
        return en_id
    except BadSignature:
        return None

def getDirectDownloadLink(fileId):
    """
    Function for getting a direct link to file saved on Google drive
    """
    directLink = f"https://drive.google.com/uc?export=download&id={fileId}"
    return directLink

def generate_document_link(request, document):
    generated_link = request.build_absolute_uri(
        reverse('mdf:document_page') + f"?doc_url={document.doc_url}"
    )
    return generated_link


def generate_document_link_task(document, domain=None, protocol="https"):
    """

    """
    if not domain:
        domain = getattr(settings, "SITE_DOMAIN", "localhost:8000")

    relative_path = reverse('mdf:document_page') + f"?doc_url={document.doc_url}"
    return f"{protocol}://{domain}{relative_path}"

def getFileIdFromLink(sharedLink):
    """
    Function for getting a file id from link
    """
    try:
        return sharedLink.split('/d/')[1].split('/')[0]
    except IndexError as e:
        return 'testId'

def user_is_admin(user):
    """
    Checking if the user is a member of the administrators group.
    """
    return user.is_authenticated and user.groups.filter(name=string_constants.mdf_admin_group_name).exists()

def get_documents_by_category(category):
    return Document.objects.get(category=category)

def send_agreement(document, user, time_spent):
    DocumentAgreement.objects.create(
        user=user,
        document=document,
        reading_time=time_spent,
        open_count=1
    )
    return True

def get_users_accepted_count(document):
    return len(DocumentAgreement.objects.filter(document=document))

def get_users_accepted(document):
    return User.objects.filter(document_stats__document=document).distinct()

def get_users_without_agreements(document):
    all_users = document.get_users_from_groups()
    users_agreed = get_users_accepted(document)
    return list(set(all_users) - set(users_agreed))

def exists_users_agreement(user, document):
    return DocumentAgreement.objects.filter(user=user, document=document).exists()

# emails

def send_link_to_owner_and_responsible_users(request, document, generated_link):
    """
    Function for sending a generated link with document url to a document author for adding other informations
    """
    logger = logging.getLogger(__name__)
    owner = document.owner
    users = document.get_all_important_users()

    responsible_users_text = "\n".join(f"{user.first_name} {user.last_name}" for user in users)

    subject = "Adding information to a document"
    #from_email = settings.EMAIL_HOST_USER
    for user in users:
        message = f"Hello {user.first_name} {user.last_name},\n\n" \
              f"please click on the following link and complete the document information:\n{generated_link}\n" \
              f"Responsible users: \n{responsible_users_text}\n" \
              f"Thank you!"
        send_mail_to_user(user, subject, message)
        #send_mail(subject, message, from_email, [user.email],fail_silently=False)


def send_mail_to_user(user, subject, message):
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
    users = document.get_users_from_groups()
    subject = string_constants.email_subject_accept
    from_email = settings.DEFAULT_FROM_EMAIL
    #message = f"{mess}\n\nLink: {generated_link}"
    # Sending emails
    for user in users:
        send_mail_to_user(user, subject, mess)
        #user_email = user.email
        #send_mail(subject, mess, from_email, [user_email], fail_silently=False)

def notify_users_about_document_deadline(document):
    """
    Function to send notifications to users about the expiration of a document.
    """
    users = document.get_users_from_groups()
    subject = f'Deadline expired for document {document.doc_name}'
    message = f'Hello\n'\
              f'The deadline for the document "{document.doc_name}" has expired.\n' \
              f'Please confirm that you have read the document.\n' \
              f'Document link: {generate_document_link_task(document, None, "https")}'

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
        'date': current_date.strftime('%Y-%m-%d'),
        'count': agreed_count,
    })
    while current_date <= end_date:
        if responses.filter(agreed_at__date=current_date).count() > 0:
            agreed_count += responses.filter(agreed_at__date=current_date).count()
            data_points.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': agreed_count,
            })
        if document.deadline.date()  == current_date:
            data_points.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'count': agreed_count,
            })
        current_date += timedelta(days=1)

    # Data extraction
    labels = [point['date'] for point in data_points]
    counts = [point['count'] for point in data_points]

    return {
        'labels': labels,
        'counts': counts,
        'deadline': document.deadline.strftime('%Y-%m-%d'),
    }
