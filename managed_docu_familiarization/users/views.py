from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.views.generic import View
from django.shortcuts import render
from django.utils.translation import gettext as _

from managed_docu_familiarization.users.forms import LoginForm

class MyLoginView(LoginView):
    form_class = LoginForm

class MyLogoutView(LogoutView):
    pass

class HomeView(View):
    """
    Display Home page
    """

    template_name = "pages/home.html"

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context=context)

