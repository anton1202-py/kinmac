from django.urls import path

from . import views

urlpatterns = [
    path('check_report', views.check_report, name='check_report'),
    path('compair_report', views.compair_report, name='compair_report'),

    path('sales_one_report/<int:realizationreport_id>',
          views.SalesOneReportDetailView.as_view(),
          name='sales_one_report'
          ),
]