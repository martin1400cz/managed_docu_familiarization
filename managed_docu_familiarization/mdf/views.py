from django.views.generic import View
from django.shortcuts import render

from managed_docu_familiarization.mdf.models import Document
"""
class MDFView(View):



    template_name = ""

    def get(self, request, *args, **kwargs):
        context = {}
        return render(request, self.template_name, context=context)
"""
class MDFDocumentsOverview(View):

    template_name = 'base_page.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            #mdf_documents = Document.objects.all()
            mdf_documents = Document.objects.filter(groups__users=request.user).distinct()
            #print(mdf_documents)
            context = {
                'mdf_documents' : mdf_documents,
            }

            return render(request, self.template_name, context=context)
        else:
            return render(request, 'templates/login.html')  # Redirect to login if not authenticated

