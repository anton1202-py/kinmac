from datetime import date, datetime, timedelta
import urllib.parse
import pandas as pd
from celery_tasks.tasks import (add_data_sales, add_data_stock_api,
                                add_stock_data_site, delivery_statistic,
                                orders_statistic, sales_report_statistic)
from database.periodic_tasks import calculate_storage_cost, update_info_about_articles
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, IntegerField, Q, When
from django.db.models.functions import (ExtractWeek, ExtractYear,
                                        TruncWeek)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from check_report.signals import articles_analytics_data
from api_requests.wb_requests import get_campaign_statistic, get_stock_from_webpage_api
from kinmac.constants_file import BRAND_LIST
from position.periodic_tasks import article_position_task
from position.supplyment import article_position_in_search
from reklama.periodic_tasks import campaign_list_to_db, update_daily_article_adv_cost, write_daily_adv_statistic


from .models import ArticlePosition

def article_position(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    article_position_task()
    page_name = 'Позиция артикулов по запросам'
    data = ArticlePosition.objects.all()
    if request.POST:
        wb_article = int(request.POST.get('wb_article', ''))
        key_word = request.POST.get('key_word', '')
        position = None
        if key_word and wb_article:
            about_article = get_stock_from_webpage_api(wb_article)
            if about_article:
                article_data = about_article['data']['products'][0]
                name = article_data['name']
                brand = article_data['brand']
            position_data = article_position_in_search(wb_article, key_word)  
            if position_data:
                position = position_data

            if not ArticlePosition.objects.filter(
                wb_article=wb_article,
                key_word=key_word,
                create_time=datetime.now()).exists():
                ArticlePosition(
                    wb_article=wb_article,
                    key_word=key_word,
                    name=name,
                    brand=brand,
                    position=position
                ).save()
            else:
                ArticlePosition.objects.filter(
                    wb_article=wb_article,
                    key_word=key_word,
                    create_time=datetime.now()).update(
                    name=name,
                    brand=brand,
                    position=position
                )
    context = {
        'page_name': page_name,
        'data': data,
    }
    
    
    return render(request, 'position/article_position.html', context)

