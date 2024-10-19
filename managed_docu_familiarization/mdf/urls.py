from django.urls import path

from managed_docu_familiarization.mdf.views import MDFView
from managed_docu_familiarization.mdf.views import MDFDocumentsOverview

app_name = "mdf"
urlpatterns = [
    path("", MDFView.as_view(), name="mdf_index"),
    path("emp-people-overview", MDFDocumentsOverview.as_view(), name="managed_docu_familiarization"),
]
