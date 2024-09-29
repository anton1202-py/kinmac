from datetime import date, datetime, timedelta

import pandas as pd
from celery_tasks.tasks import sales_report_statistic
from check_report.supplyment import (add_data_to_db_from_excel,
                                     download_report_data_for_check,
                                     report_reconciliation,
                                     rewrite_sales_order,
                                     rewrite_sales_order_from_zip)
from database.models import Articles, CostPrice, SalesReportOnSales
from database.periodic_tasks import update_info_about_articles
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import (Case, Count, IntegerField, Max, OuterRef, Q,
                              Subquery, Sum, When)
from django.db.models.functions import (ExtractMonth, ExtractWeek, ExtractYear,
                                        TruncWeek)
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from sales_analytics.supplyment import (costprice_article_timport_from_excel,
                                        template_for_article_costprice)

from .models import ArticleSaleAnalytic, CommonSaleAnalytic
from kinmac.constants_file import BRAND_LIST


def common_sales_analytic(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Общий анализ продаж'
    analytic_data = CommonSaleAnalytic.objects.filter(article__brand__in=BRAND_LIST)
   
    context = {
        'page_name': page_name,
        'analytic_data': analytic_data,
    }
    
    return render(request, 'sales_analytics/common_analytics.html', context)

def add_costprice_article(request):
    """Страница с добавлением себестоимости артикула"""
    page_name = 'Себестоимость товаров'
    costprice_data = CostPrice.objects.filter(article__brand='KINMAC')

    articles_data = Articles.objects.all()

    for article in articles_data:
        if not CostPrice.objects.filter(article=article).exists():
            CostPrice(
                article=article
            ).save()
    error_text= []
    if request.POST:
        if 'export' in request.POST or 'import_file' in request.FILES:
            if request.POST.get('export') == 'create_file':
                return template_for_article_costprice(costprice_data)

            elif 'import_file' in request.FILES:
                error_text = costprice_article_timport_from_excel(
                    request.FILES['import_file'])
                if not error_text:
                    return redirect('sales_analytic_costprice')

    context = {
        'page_name': page_name,
        'costprice_data': costprice_data,
        'error_text': error_text
    }
    return render(request, 'sales_analytics/costprice.html', context)


def update_costprice(request):
    """Обновление себестоимости и затрат на ФФ через jQuery"""
    if request.POST:
        article = request.POST.get('article')   
        costprice = request.POST.get('main_costprice', '')
        ff_cost = request.POST.get('main_ff_cost', '')
       
        if article:
            # Сохраняем себестоимоть
            if costprice:
                costprice = int(costprice)
                if CostPrice.objects.filter(article__nomenclatura_wb=article).exists():
                    CostPrice.objects.filter(article__nomenclatura_wb=article).update(
                        costprice=costprice, costprice_date=datetime.now()
                    )
                else:
                    CostPrice(article__nomenclatura_wb=article,
                        costprice=costprice, costprice_date=datetime.now()
                    ).save()
            # Сохраняем затраты на Фулфилмент
            if ff_cost:
                costprice = int(ff_cost)
                if CostPrice.objects.filter(article__nomenclatura_wb=article).exists():
                    CostPrice.objects.filter(article__nomenclatura_wb=article).update(
                        ff_cost=ff_cost, ff_cost_date=datetime.now()
                    )
                else:
                    CostPrice(article__nomenclatura_wb=article,
                        ff_cost=ff_cost, ff_cost_date=datetime.now()
                    ).save()
        return JsonResponse({'message': 'Value saved successfully.'})
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


class ArticleAnalyticsDetailView(ListView):
    model = ArticleSaleAnalytic
    template_name = 'sales_analytics/article_analytics.html'
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super(ArticleAnalyticsDetailView,
                        self).get_context_data(**kwargs)
        analytic_data = ArticleSaleAnalytic.objects.filter(
            article__nomenclatura_wb=self.kwargs['article']).order_by('-analytic_date')
        article_obj = Articles.objects.get(nomenclatura_wb=self.kwargs['article'])
        page_name = f"Аналитика артикула {article_obj.common_article} ({article_obj.name})"
        context.update({
            'page_name': page_name,
            'analytic_data': analytic_data,
        })
        return context
