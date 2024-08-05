from django.urls import path

from . import views

urlpatterns = [
    path('check_report', views.check_report, name='check_report'),
    
]