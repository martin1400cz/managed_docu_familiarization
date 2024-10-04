from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.views.generic import View
from django.shortcuts import render
from django.utils.translation import gettext as _

from managed_docu_familiarization.emp.models import HRPerson

class EMPView(View):
    """
    """

    template_name = ""

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context=context)

class EMPPeopleOverview(View):
    """
    Display EMPPeople overview
    """

    template_name = 'emp/emp_people_overview.html'

    # Decorator for checking if the user passes test
    # @method_decorator(user_passes_test(user_is_TL_HR, login_url=redirect_url))
    def get(self, request, *args, **kwargs):
        # select only people that have an active contract
        emp_people = HRPerson.objects.all()

        context = {
            'emp_people' : emp_people,
            }

        return render(request, self.template_name, context=context)
