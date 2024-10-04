"""Custom middleware classes to enable specific behaviour.

ref: https://docs.djangoproject.com/en/4.2/topics/http/middleware/
"""
import logging

from django.shortcuts import redirect
from django.urls import reverse

log = logging.getLogger(__name__)

# exemptions
EXEMPT_PATHS = [reverse('login'), reverse('logout'), '/static/', '/help/', '/api/', '/auth-token/']


class LoginRequiredMiddleware:
    """
    Make the whole website accessible only after login
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not request.user.is_authenticated and not any(request.path.startswith(path) for path in EXEMPT_PATHS):
            return redirect('login')  # Redirect to the login page if not authenticated

        return self.get_response(request)
