from datetime import datetime
from database.models import Articles, CostPrice

from django.http import JsonResponse
from django.shortcuts import redirect, render

from django.views.generic import ListView
from sales_analytics.periodic_tasks import commom_analytics_data
from sales_analytics.supplyment import (costprice_article_timport_from_excel,
                                        template_for_article_costprice)

from .models import ArticleSaleAnalytic, CommonSaleAnalytic
from kinmac.constants_file import BRAND_LIST


def common_sales_analytic(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Общий анализ продаж'
    analytic_data = CommonSaleAnalytic.objects.all()
    if request.POST:
        datestart = request.POST.get('datestart', '')
        datefinish = request.POST.get('datefinish', '')
        article_filter = request.POST.get('article_filter', '')
        commom_analytics_data(datestart=datestart, datefinish=datefinish, article_filter=article_filter)
        if 'update_data' in request.POST:
            commom_analytics_data()
        analytic_data = CommonSaleAnalytic.objects.all()
    context = {
        'page_name': page_name,
        'analytic_data': analytic_data,
    }
    
    return render(request, 'sales_analytics/common_analytics.html', context)


def add_costprice_article(request):
    """Страница с добавлением себестоимости артикула"""
    page_name = 'Себестоимость товаров'
    

    articles_data = Articles.objects.filter(brand__in=BRAND_LIST)

    for article in articles_data:
        if not CostPrice.objects.filter(article=article).exists():
            CostPrice(
                article=article
            ).save()
    costprice_data = CostPrice.objects.filter(article__brand__in=BRAND_LIST)
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
