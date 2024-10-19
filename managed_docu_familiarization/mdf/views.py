from django.views.generic import View
from django.shortcuts import render

from managed_docu_familiarization.mdf.models import Document

class MDFView(View):
    """
    """

    template_name = ""

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context=context)

class MDFDocumentsOverview(View):
    """
    Display EMPPeople overview
    """

    template_name = 'base_page.html'

    # Decorator for checking if the user passes test
    # @method_decorator(user_passes_test(user_is_TL_HR, login_url=redirect_url))
    def get(self, request, *args, **kwargs):
        # select only people that have an active contract
        mdf_documents = Document.objects.all()

        context = {
            'mdf_documents' : mdf_documents,
            }

        return render(request, self.template_name, context=context)
