from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from managed_docu_familiarization.mdf import views
#from managed_docu_familiarization.mdf.views import MDFView
from managed_docu_familiarization.mdf.views import MDFDocumentsOverview, MDFDocumentsAdding, MDFAdminSearchDocument, \
    MDFDocumentDetailView, MDFDocumentStatsView

app_name = "mdf"
urlpatterns = [
    #path("", MDFView.as_view(), name="mdf_index"),
    path("mdfdocuments/document/", MDFDocumentDetailView.as_view(), name="document_page"),
    #path("mdfdocuments/document/<str:file_name>/", MDFDocumentDetailView.as_view(), name="document_page"),
    path("mdfdocuments/overview/", MDFDocumentsOverview.as_view(), name="base_page"),
    path('mdfdocuments/agreements/', MDFDocumentStatsView.as_view(), name='document_stats'),
    path('mdfdocuments/agreements/<str:doc_id>/', MDFDocumentStatsView.as_view(), name='document_stats'),
    path("mdfdocuments/overview/add/", MDFDocumentsAdding.as_view(), name="publishing_page"),
    path("mdfdocuments/overview/add/<str:file_name>/", MDFDocumentsAdding.as_view(), name="publishing_page"),
    path('mdfdocuments/admin-file-search/', MDFAdminSearchDocument.as_view(), name='admin_file_search_page'),
    path('mdfdocuments/admin-file-search/send-link/<str:file_name>/', views.send_link_to_owner, name='send_link_to_owner'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
