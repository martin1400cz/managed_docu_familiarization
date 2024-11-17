from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement


def send_document_link(document):
    link = reverse('document_add_info', args=[document.secure_token])
    full_link = f"{settings.SITE_URL}{link}"

    send_mail(
        subject="Access Your Document",
        message=f"Click the link to view and add information to your document: {full_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[document.owner.email],
    )

def get_documents_by_category(category):
    return Document.objects.get(category=category)

def send_agreement(document, user):
    agreement = DocumentAgreement.objects.create(
        user=user,
        document=document
    )

'''
Functions returns a list of users from certain groups, if some users are in more than one group, they are picked only once.
'''
def getUsersFromGroups(groups):
    unique_set = set()
    for group in groups:
        unique_set.update(group)
    return list(unique_set)
