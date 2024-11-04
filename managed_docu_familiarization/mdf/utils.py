from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

def send_document_link(document):
    link = reverse('document_add_info', args=[document.secure_token])
    full_link = f"{settings.SITE_URL}{link}"

    send_mail(
        subject="Access Your Document",
        message=f"Click the link to view and add information to your document: {full_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[document.owner.email],
    )
