from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from managed_docu_familiarization.mdf import views
#from managed_docu_familiarization.mdf.views import MDFView
from managed_docu_familiarization.mdf.views import MDFDocumentsOverview, MDFDocumentsAdding, MDFAdminDocumentAdd, \
    MDFDocumentView, MDFDocumentStatsView, MDFDocumentsUserDetailView, open_document_base_page, open_document_stats, \
    open_document_user_detail, open_admin_add_document_page, MDFAdminDocumentList, MDFDocumentApprovalView, \
    open_document_approval

app_name = "mdf"
urlpatterns = [
    #path("", MDFView.as_view(), name="mdf_index"),
    # document_page - view to display the document
    path("mdfdocuments/document/", MDFDocumentView.as_view(), name="document_page"),
    path("mdfdocuments/document/<str:enc_doc_id>", MDFDocumentView.as_view(), name="document_page"),
    path("mdfdocuments/overview/open/<str:enc_doc_id>/", open_document_base_page, name="open_document_view"),

    # base_page - documents overview
    path("mdfdocuments/overview/", MDFDocumentsOverview.as_view(), name="base_page"),

    # documents_stats - view to display statistics about a document
    path('mdfdocuments/agreements/', MDFDocumentStatsView.as_view(), name='document_stats'),
    path('mdfdocuments/agreements/open/<str:enc_doc_id>/', open_document_stats, name='open_document_stats'),

    # document_approval - view for approvers to check a document
    path('mdfdocuments/approvals/', MDFDocumentApprovalView.as_view(), name='document_approval'),
    path('mdfdocuments/approvals/<str:enc_doc_id>', MDFDocumentApprovalView.as_view(), name='document_approval'),
    path('mdfdocuments/approvals/open/<str:enc_doc_id>/', open_document_approval, name='open_document_approval'),
    # user_stats
    path('mdfdocuments/user_stats/', MDFDocumentsUserDetailView.as_view(), name='user_stats'),
    path('mdfdocuments/user_stats/open/<str:user_id>/', open_document_user_detail, name='open_user_stats'),
    # publishing_page
    path("mdfdocuments/overview/add/", MDFDocumentsAdding.as_view(), name="publishing_page"),
    path("mdfdocuments/overview/add/<str:file_name>/", MDFDocumentsAdding.as_view(), name="publishing_page"),
    # admin pages
    path('mdfdocuments/admin-file-search/', MDFAdminDocumentList.as_view(), name='admin_file_search_page'),
    path('mdfdocuments/admin-file-search/open/<str:doc_id>', open_admin_add_document_page,name='open_admin_add_document_page'),
    path('mdfdocuments/admin-file-search/open/<str:doc_id><str:action>', open_admin_add_document_page, name='open_admin_add_document_page'),
    path('mdfdocuments/admin-file-search/open/<str:action>', open_admin_add_document_page, name='open_admin_add_document_page'),
    path('mdfdocuments/admin-add-document/', MDFAdminDocumentAdd.as_view(), name='admin_add_document_page'),
    path('mdfdocuments/admin-add-document/<str:action>', MDFAdminDocumentAdd.as_view(), name='admin_add_document_page'),
    path('mdfdocuments/admin-file-search/send-link/<str:file_name>/', MDFAdminDocumentAdd.as_view(), name='send_link_to_owner'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
