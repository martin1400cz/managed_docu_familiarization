from celery import shared_task
from django.utils.timezone import now
from .models import Document
from .utils import notify_users_about_document_deadline, notify_owner_about_document_deadline

@shared_task
def check_document_deadlines():
    """
    Periodic task function - checks the expiration of deadline documents
    :return: text - how many documents were processed
    """
    # Get actual time
    current_time = now()
    # Finding all expired documents
    expired_documents = Document.objects.filter(deadline__lte=current_time,
                                                status='pending')
    print("Checking for expired deadlines...")
    for document in expired_documents:
        # We inform the owner and target users about the expiration of the document deadline
        notify_users_about_document_deadline(document)
        notify_owner_about_document_deadline(document)

        # We update the document status to prevent the same action from happening again.
        document.status = 'processed'
        document.save()
    return f"{len(expired_documents)} documents processed."
