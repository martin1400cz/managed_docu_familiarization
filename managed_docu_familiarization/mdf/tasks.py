import logging

from celery import shared_task
from django.utils.timezone import now
from .models import Document
from django.core.mail import send_mail

from .utils import notify_users_about_document_deadline, notify_owner_about_document


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
        notify_users_about_document_deadline(document)
        notify_owner_about_document(document)

        # Aktualizujeme stav dokumentu, aby se stejná akce neopakovala
        document.status = 'processed'  # Příklad stavu: "zpracováno"
        document.save()

    return f"{len(expired_documents)} documents processed."
