from django.urls import path
from .views import PersonList, PersonDetail, StatsView, ExportData, ImportData, ExportPDF, ExportPDFResult, ResetDatabase, RFIDSimulator, LogList, ResetLog, LogCreateView

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
    path('simulate-rfid/', RFIDSimulator.as_view(), name='simulate-rfid'),
    path('logs/', LogList.as_view(), name='log-list'),
    path('logs/new/', LogCreateView.as_view(), name='log-create'),
]
