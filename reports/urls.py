# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_list, name='reports_list'),
    path('print/', views.print_report, name='print_report'),
]