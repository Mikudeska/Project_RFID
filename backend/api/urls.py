from django.urls import path
from .views import PersonList, PersonDetail, StatsView, ExportData, ImportData, ExportPDF, ExportPDFResult, ResetDatabase, RFIDSimulator, LogList, ResetLog, LogCreateView
from . import views

urlpatterns = [
    path('person/', PersonList.as_view(), name='person-list'),
    path('person/<int:pk>/', PersonDetail.as_view(), name='person-detail'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('person/delete/', PersonList.as_view(), name='person-delete'),
    path('export/<str:format_type>/', ExportData.as_view()),
    path('import/', ImportData.as_view()),
    path('export-pdf/', ExportPDF.as_view()),
    path('export-pdf-result/', ExportPDFResult.as_view()),
    path('reset/', ResetDatabase.as_view(), name='reset-database'),
    path('resetlog/', ResetLog.as_view(), name='reset-log'),
    path('rfidAPI/', RFIDSimulator.as_view(), name='rfid_api'),
    path('logs/', LogList.as_view(), name='log-list'),
    path('logs/new/', LogCreateView.as_view(), name='log-create'),
    path("get-csrf-token/", views.get_csrf_token, name="get_csrf_token"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
]