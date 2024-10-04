from django.urls import path

from managed_docu_familiarization.emp.views import EMPView
from managed_docu_familiarization.emp.views import EMPPeopleOverview

app_name = "emp"
urlpatterns = [
    path("", EMPView.as_view(), name="emp_index"),
    path("emp-people-overview", EMPPeopleOverview.as_view(), name="emp_people_overview"),
]
