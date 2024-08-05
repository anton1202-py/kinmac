from datetime import date, timedelta

import pandas as pd
from celery_tasks.tasks import sales_report_statistic
from check_report.supplyment import (download_report_data_for_check,
                                     report_reconciliation)
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

from .models import CommonSalesReportData


def check_report(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Сверка еженедельных отчетов'
    data = CommonSalesReportData.objects.all().order_by('realizationreport_id')
    # for i in data:
    #     i.delete()
    if request.POST:
        print(request.POST)
        if 'reconciliation' in request.POST:
            report_reconciliation()
        elif 'import_file' in request.FILES:
            print('Нашел файл')
            errors_list = download_report_data_for_check(request.FILES['import_file'])
    paginator = Paginator(data, 100)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)  # Если номер страницы не целый, возвращаем первую страницу
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)  # Если страница выходит за пределы, возвращаем последнюю страницу
    # sales_report_statistic()
    context = {
        'page_name': page_name,
        'data': data,
        'page_obj': page_obj,
    }
    
    return render(request, 'check_report/common_report.html', context)

