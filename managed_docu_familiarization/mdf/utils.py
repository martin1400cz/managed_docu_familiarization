import logging

from django.core.mail import send_mail
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

'''
Functions returns a list of users from certain groups, if some users are in more than one group, they are picked only once.
'''
def getUsersFromGroups(document):
    unique_set = set()
    users = User.objects.filter(groups__in=document.groups.all())
    owner = document.owner
    # removing admin
    #admin_user = None
    #for user in users:
    #    if user_is_admin(user):
    #        admin_user = user
    unique_set.update(users)
    #removing document owner
    unique_set.remove(owner)
    #unique_set.remove(admin_user)
    #for group in groups:
    #    users = User.objects.filter(groups__)
    #    unique_set.update(users)
    return list(unique_set)

def send_mail_to_user(user, subject, message):
    from_email = settings.EMAIL_HOST_USER
    send_mail(subject, message, from_email, [user.email], fail_silently=False)

def sendLinksToUsers(document, generated_link, mess):
    users = getUsersFromGroups(document)
    subject = string_constants.email_subject_accept
    from_email = settings.EMAIL_HOST_USER
    message = f"{mess}\n\nLink: {generated_link}"
    # Odeslání e-mailu
    for user in users:
        user_email = user.email
        send_mail(subject, message, from_email, [user_email], fail_silently=False)

"""
Function to send notifications to users about the expiration of a document.
"""
def notify_users_about_document_deadline(document):
    logger = logging.getLogger(__name__)
    users = getUsersFromGroups(document)
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
