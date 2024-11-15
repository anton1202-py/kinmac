from datetime import date, datetime, timedelta

import pandas as pd
from celery_tasks.tasks import sales_report_statistic
from check_report.supplyment import (add_data_to_db_from_excel,
                                     download_report_data_for_check,
                                     report_reconciliation,
                                     rewrite_sales_order,
                                     rewrite_sales_order_from_zip)
from database.models import SalesReportOnSales
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import (ExtractMonth, ExtractWeek, ExtractYear,
                                        TruncWeek)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from .models import CommonSalesReportData, ExcelReportData


def check_report(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Сверка еженедельных отчетов'
    data = CommonSalesReportData.objects.all().order_by('realizationreport_id')
    if request.POST:
        if 'reconciliation' in request.POST:
            report_reconciliation()
        elif 'import_file' in request.FILES:
            errors_list = download_report_data_for_check(
                request.FILES['import_file'])
        elif 'reload_zip' in request.FILES:
            report_date_from = request.POST.get('report_date_from')
            report_date_to = request.POST.get('report_date_to')
            report_number = request.POST.get('report_number')
            rewrite_sales_order_from_zip(
                report_date_from, report_date_to, report_number, request.FILES['reload_zip'])

            data = CommonSalesReportData.objects.all().order_by('realizationreport_id')

    context = {
        'page_name': page_name,
        'data': data,
    }

    return render(request, 'check_report/common_report.html', context)


def compair_report(request):
    """Сведение отчетов из excel и из базы по АПИ"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Сведение еженедельных отчетов'
    excel_data = ExcelReportData.objects.all().order_by('realizationreport_id')
    db_report_data = CommonSalesReportData.objects.all()
    if request.POST:
        if 'reconciliation' in request.POST:
            report_reconciliation()
        elif 'reload_report' in request.POST:
            report_date_from = request.POST.get('report_date_from')
            report_date_to = request.POST.get('report_date_to')
            report_number = request.POST.get('report_number')
            rewrite_sales_order(
                report_date_from, report_date_to, report_number)
            db_report_data = CommonSalesReportData.objects.all()
        elif 'reload_zip' in request.FILES:
            report_date_from = request.POST.get('report_date_from')
            report_date_to = request.POST.get('report_date_to')
            report_number = request.POST.get('report_number')
            rewrite_sales_order_from_zip(
                report_date_from, report_date_to, report_number, request.FILES['reload_zip'])
            db_report_data = CommonSalesReportData.objects.all()
        elif 'import_file' in request.FILES:
            errors_list = add_data_to_db_from_excel(
                request.FILES['import_file'])
    db_data_dict = {}
    for db_data in db_report_data:
        db_data_dict[db_data.realizationreport_id] = [float(db_data.retail_without_return), float(
            db_data.ppvz_for_pay), db_data.check_ppvz_for_pay, db_data.delivery_rub, db_data.storage_fee, db_data.penalty, db_data.total_paid]
    context = {
        'page_name': page_name,
        'excel_data': excel_data,
        'db_data_dict': db_data_dict
    }

    return render(request, 'check_report/compair_report.html', context)


class SalesOneReportDetailView(ListView):
    model = SalesReportOnSales
    template_name = 'check_report/check_report_sales_report.html'
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super(SalesOneReportDetailView,
                        self).get_context_data(**kwargs)
        sales_report = SalesReportOnSales.objects.filter(
            realizationreport_id=self.kwargs['realizationreport_id']).order_by('rrd_id')
        page_name = f"Еженедельный отчет {self.kwargs['realizationreport_id']}"
        context.update({
            'page_name': page_name,
            'sales_report': sales_report,
        })
        return context
