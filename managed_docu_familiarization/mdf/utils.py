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

def generate_secure_id(id):
    signer = Signer()
    signed_id = signer.sign(id)
    return signed_id



def verify_secure_id(signed_id):
    signer = Signer()
    try:
        en_id = signer.unsign(signed_id)
        return en_id
    except BadSignature:
        return None

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
    try:
        return sharedLink.split('/d/')[1].split('/')[0]
    except IndexError as e:
        return 'testId'

"""
Checking if the user is a member of the administrators group.
"""
def user_is_admin(user):

    return user.is_authenticated and user.groups.filter(name='MDF_admin').exists()

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

def generate_document_link(request, document):
    generated_link = request.build_absolute_uri(
        reverse('mdf:document_page') + f"?doc_url={document.doc_url}"
    )
    return generated_link

def send_link_to_owner_and_responsible_users(request, document, generated_link):
    """
    Function for sending a generated link with document url to a document author for adding other informations
    """
    logger = logging.getLogger(__name__)
    owner = document.owner
    users = document.get_all_important_users()

    responsible_users_text = "\n".join(f"{user.first_name} {user.last_name}" for user in users)

    subject = "Adding information to a document"
    from_email = settings.EMAIL_HOST_USER
    for user in users:
        message = f"Hello {user.first_name} {user.last_name},\n\n" \
              f"please click on the following link and complete the document information:\n{generated_link}\n" \
              f"Responsible users: \n{responsible_users_text}\n" \
              f"Thank you!"
        send_mail(subject, message, from_email, [user.email],fail_silently=False)


def send_mail_to_user(user, subject, message):
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [user.email], fail_silently=False)

def sendLinksToUsers(document, generated_link, mess):
    users = document.get_users_from_groups()
    subject = string_constants.email_subject_accept
    from_email = settings.EMAIL_HOST_USER
    #message = f"{mess}\n\nLink: {generated_link}"
    # Odeslání e-mailu
    for user in users:
        user_email = user.email
        send_mail(subject, mess, from_email, [user_email], fail_silently=False)

"""
Function to send notifications to users about the expiration of a document.
"""
def notify_users_about_document_deadline(document):
    logger = logging.getLogger(__name__)
    users = document.get_users_from_groups()
    subject = f'Deadline expired for document {document.doc_name}'
    message = f'The deadline for the document "{document.doc_name}" has expired. Please take necessary action.'

    for user in users:
        logger.error(f"User: {user.first_name}")
        from_email = 'noreply@zf.com'
        to_email = user.email
        send_mail(
            subject,
            message,
            from_email,
            [to_email],
            fail_silently=False
        )

def get_users_accepted(document):
    return len(DocumentAgreement.objects.filter(document=document))
"""
Function to send notifications to document owner about the expiration of a document.
"""
def notify_owner_about_document_deadline(document):
    subject = f'Deadline expired for document {document.doc_name}'
    message = f'The deadline for the document "{document.doc_name}" has expired. Please take necessary action.'
    from_email = 'noreply@zf.com'
    to_email = document.owner.email
    send_mail(
        subject,
        message,
        from_email,
        [to_email],
        fail_silently=False
    )


def document_progress_chart(request, document):
    # Získání rozsahu dat
    responses = DocumentAgreement.objects.filter(document=document).order_by('-agreed_at')

    # Zjištění posledního data souhlasu
    if responses.exists():
        last_agreement_date = responses.order_by('-agreed_at').first().agreed_at.date()
    else:
        last_agreement_date = document.deadline.date()  # Výchozí hodnota, pokud nejsou žádné souhlasy

    # Získání rozsahu dat (od data vydání do posledního souhlasu nebo deadlinu)
    start_date = document.release_date.date()
    end_date = max(last_agreement_date, document.deadline.date())

    # Vytvoření časového rozsahu a počítání souhlasů
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

    # Extrakce dat pro graf
    labels = [point['date'] for point in data_points]
    counts = [point['count'] for point in data_points]

    return {
        'labels': labels,
        'counts': counts,
        'deadline': document.deadline.strftime('%Y-%m-%d'),
    }
