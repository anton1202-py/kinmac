from datetime import datetime, timedelta
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.shortcuts import redirect, render
from position.periodic_tasks import article_position_task
from position.supplyment import add_article_for_find_position

from .models import ArticlePosition

def article_position(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Позиция артикулов по запросам'
    show_period = datetime.now() - timedelta(days=1)
    data = ArticlePosition.objects.filter(create_time__gte=show_period)

    if request.POST:
        wb_article = request.POST.get('wb_article', '')
        key_word = request.POST.get('key_word', '')
        datestart = request.POST.get('datestart', '')
        datefinish = request.POST.get('datefinish', '')
        article_filter = request.POST.get('article_filter', '')
        data = ArticlePosition.objects.all()
        if key_word and wb_article:
            add_article_for_find_position(int(wb_article), key_word)
        if datestart:
            data = data.filter(create_time__gte=datestart)
        if datefinish:
            data = data.filter(create_time__lte=datefinish)
        if article_filter:
            if ArticlePosition.objects.filter(seller_article=article_filter).exists():
                data = data.filter(seller_article=article_filter)
            else:
                data = data.filter(wb_article=int(article_filter))
    context = {
        'page_name': page_name,
        'data': data,
    }
    return render(request, 'position/article_position.html', context)


# class ArticlePositionDetailView(ListView):
#     model = ArticlePosition
#     template_name = 'database/sales_by_week_detail.html'
#     context_object_name = 'articles'

#     def get_context_data(self, **kwargs):
#         context = super(ArticlePositionDetailView,
#                         self).get_context_data(**kwargs)

#         sales = ArticlePosition.objects.filter(
#             Q(wb_article=self.kwargs['wb_article']),
#             Q(finished_price__gte=0)).annotate(
#                 week=ExtractWeek('pub_date'),
#                 year=ExtractYear('pub_date')
#         ).values('supplier_article', 'barcode', 'week', 'year').annotate(
#             count=Count(Case(When(finished_price__gte=0, then=1),
#             output_field=IntegerField()))
#         ).order_by('supplier_article', 'barcode', 'year', 'week')
        
#         sales_data = Sales.objects.filter(
#             Q(finished_price__gte=0)).annotate(
#                 week=ExtractWeek('pub_date'),
#                 year=ExtractYear('pub_date')
#         ).values('week', 'year').order_by('year', 'week')

#         # Получаем queryset вида [{'warehouse_name': 'Тула', 'week': 43, 'year': 2023, 'week_sales': 2}]
#         warehouses = Sales.objects.filter(
#             Q(barcode=self.kwargs['barcode']),
#             Q(finished_price__gte=0)).annotate(
#                 week=ExtractWeek('pub_date'),
#                 year=ExtractYear('pub_date')
#         ).values('warehouse_name', 'week', 'year'
#                 ).annotate(week_sales=Count('id', filter=Q(sales_date__gte=TruncWeek('sales_date')))
#                 ).order_by('warehouse_name')
#         warehouses_list = []
#         # Находим склады с которых были продажи и выводим в один список
#         for warehouse in warehouses:
#             if warehouse['warehouse_name'] not in warehouses_list:
#                 warehouses_list.append(warehouse['warehouse_name'])
#         # Сортирую название складов по алфавиту
#         warehouses_list.sort()

#         data = {}
#         week_data = []
#         for tim in sales_data:
#             week_year = f"{tim['week']}-{tim['year']}"
#             week_data.append(week_year)
#         unique_week = list(set(week_data))
#         unique_week.sort()
#         for sale in sales:
#             supplier_article = sale['supplier_article']
#             barcode = sale['barcode']
#             week_year = f"{sale['week']}-{sale['year']}"
#             count = sale['count']
#             key = (supplier_article, barcode)
#             if key not in data:
#                 data[key] = {}
#             data[key][week_year] = count
        
#         # Формирую новый словарь с данными по складам, что не
#         # съезжали данные по неделям
#         warehouses_data = {}
#         for stock in warehouses:
#             key = stock['warehouse_name']
#             if key not in warehouses_data.keys():
#                 warehouses_data[key] = {}
#             #if key in warehouses_data.keys():
#             if  f"{stock['week']}-{stock['year']}" in warehouses_data[key].keys():
#                 warehouses_data[key][f"{stock['week']}-{stock['year']}"] += stock['week_sales']
#             else:
#                 warehouses_data[key][f"{stock['week']}-{stock['year']}"] = stock['week_sales']
        
#         # Добавляем недостающие недели со значением 0
#         for warehouse_name, amount in warehouses_data.items():
#             for week in unique_week:
#                 inner_dict = {}
#                 if week not in amount.keys():
#                     amount[week] = ''
#         for article_data in data.values():
#             for week in unique_week:
#                 if week not in article_data:
#                     article_data[week] = 0
#         context.update({
#             'data': data,
#             'unique_week': unique_week,
#             'sales': sales,
#             'warehouses_data': warehouses_data,
#             'warehouses_list': warehouses_list
#         })
#         return context

#     def get_queryset(self):
#         return Sales.objects.filter(
#             barcode=self.kwargs['barcode'])