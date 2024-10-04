import logging

from django.contrib.auth.backends import BaseBackend

from .models import User

log = logging.getLogger(__name__)

class PlainTextBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects.get(zf_id=username)
            if user.password == password:
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
