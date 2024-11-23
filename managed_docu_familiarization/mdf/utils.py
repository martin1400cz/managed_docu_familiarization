from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from managed_docu_familiarization.mdf.models import Document, DocumentAgreement
from managed_docu_familiarization.users.models import User

def user_is_admin(user):
    """Kontrola, zda je uživatel členem skupiny administrators."""
    return user.is_authenticated and user.groups.filter(name='MDF_admin').exists()

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
def getUsersFromGroups(document):
    unique_set = set()
    users = User.objects.filter(groups__in=document.groups.all()).distinct()
    unique_set.update(users)
    #for group in groups:
    #    users = User.objects.filter(groups__)
    #    unique_set.update(users)
    return list(unique_set)

def sendLinksToUsers(document, generated_link):
    users = getUsersFromGroups(document)
    subject = "Potvrzení o seznámení se s dokumentem"
    from_email = settings.EMAIL_HOST_USER
    message = f"Dobrý den,\n\n" \
              f"Prosíme vás o potvrzení o seznámení se s dokumentem:\n{generated_link}\n\n" \
              f"Děkujeme!"
    # Odeslání e-mailu
    for user in users:
        user_email = user.email
        send_mail(subject, message, from_email, [user_email], fail_silently=False)
