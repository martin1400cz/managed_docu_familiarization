import logging

from celery import shared_task
from django.utils.timezone import now
from .models import Document
from django.core.mail import send_mail

from .utils import getUsersFromGroups


#@shared_task
#def shared_task_custom():
#    pass


@shared_task
def check_document_deadlines():
    logger = logging.getLogger(__name__)
    # Získáme aktuální čas
    current_time = now()
    logger.error("Mame aktualni cas")
    # Najdeme všechny dokumenty, jejichž deadline uplynul
    expired_documents = Document.objects.filter(deadline__lte=current_time,
                                                status='pending')  # status kontroluje např. "čekající"
    logger.error("Mame dokumenty")
    for document in expired_documents:
        # Provádíme akci (např. odesílání e-mailu)
        logger.error("Provadime akci")
        notify_users_about_document(document)

        # Aktualizujeme stav dokumentu, aby se stejná akce neopakovala
        document.status = 'processed'  # Příklad stavu: "zpracováno"
        document.save()

    return f"{len(expired_documents)} documents processed."


def notify_users_about_document(document):
    """
    Funkce pro odeslání upozornění uživatelům o uplynutí lhůty pro dokument.
    """
    users = getUsersFromGroups(document)
    for user in users:
        send_mail(
            subject=f'Deadline expired for document: {document.doc_name}',
            message=f'The deadline for the document "{document.doc_name}" has expired. Please take necessary action.',
            from_email='noreply@zf.com',
            recipient_list=user.email,
        )
