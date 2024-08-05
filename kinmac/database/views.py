from datetime import date, timedelta

import pandas as pd
from celery_tasks.tasks import sales_report_statistic
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

from .forms import (ArticlesForm, LoginUserForm, SelectDateForm,
                    SelectDateStocksForm)
from .models import (Articles, Deliveries, Orders, Sales, SalesReportOnSales,
                     StocksApi, StocksSite)


def database_home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')

    data = Articles.objects.all()
    context = {
        'data': data,
    }
    # sales_report_statistic()
    if request.method == 'POST' and request.FILES['myarticles']:
        myfile = request.FILES['myarticles']
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata, columns=['Баркод', 'Номенк WB', 'Номенк OZON', 'Арт',
                                   'Бренд', 'Предмет', 'SIZE', 'MODEL', 'COLOR',
                                   'CC', 'Сред СС'])
        barcode_list = load_excel_data_wb_stock['Баркод'].to_list()
        nomenclatura_wb_list = load_excel_data_wb_stock['Номенк WB'].to_list()
        nomenclatura_ozon_list = load_excel_data_wb_stock['Номенк OZON'].to_list(
        )
        common_article_list = load_excel_data_wb_stock['Арт'].to_list()
        brend_list = load_excel_data_wb_stock['Бренд'].to_list()
        predmet_list = load_excel_data_wb_stock['Предмет'].to_list()
        size_list = load_excel_data_wb_stock['SIZE'].to_list()
        model_list = load_excel_data_wb_stock['MODEL'].to_list()
        color_list = load_excel_data_wb_stock['COLOR'].to_list()
        prime_cost_list = load_excel_data_wb_stock['CC'].to_list()
        average_cost_list = load_excel_data_wb_stock['Сред СС'].to_list()
        dbframe = empexceldata
        for i in range(len(common_article_list)):
            if Articles.objects.filter(Q(common_article=common_article_list[i])):
                Articles.objects.filter(common_article=common_article_list[i]).update(
                    barcode=barcode_list[i],
                    nomenclatura_wb=nomenclatura_wb_list[i],
                    nomenclatura_ozon=nomenclatura_ozon_list[i],
                    brend=brend_list[i],
                    predmet=predmet_list[i],
                    size=size_list[i],
                    model=model_list[i],
                    color=color_list[i],
                    prime_cost=prime_cost_list[i],
                    average_cost=average_cost_list[i],
                )
            else:
                obj = Articles(
                    common_article=common_article_list[i],
                    barcode=barcode_list[i],
                    nomenclatura_wb=nomenclatura_wb_list[i],
                    nomenclatura_ozon=nomenclatura_ozon_list[i],
                    brend=brend_list[i],
                    predmet=predmet_list[i],
                    size=size_list[i],
                    model=model_list[i],
                    color=color_list[i],
                    prime_cost=prime_cost_list[i],
                    average_cost=average_cost_list[i],
                )
                obj.save()
    return render(request, 'database/database_home.html', context)


def database_stock_api(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    articles = Articles.objects.all()
    data = StocksApi.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))
    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = StocksApi.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = StocksApi.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(article_marketplace=article_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
        'articles': articles.all().values(),
    }
    return render(request, 'database/stock_api.html', context)


def stock_site(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today()  # - timedelta(days=1)
    control_date_stock_tomorrow = date.today() + timedelta(days=1)
    data = StocksSite.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock_tomorrow]))
    form = SelectDateStocksForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        stock_filter = form.cleaned_data.get("stock_filter")
        if article_filter == '' and stock_filter == '':
            data = StocksSite.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        elif article_filter != '' and stock_filter == '':
            data = StocksSite.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(seller_article_wb=article_filter))
        elif article_filter == '' and stock_filter != '':
            data = StocksSite.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(stock_name=stock_filter))
        else:
            data = StocksSite.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(seller_article_wb=article_filter),
                Q(stock_name=stock_filter))
    context = {
        'form': form,
        'data': data,
        'datestart': str(datestart),
    }
    return render(request, 'database/stock_site.html', context)


def database_sales(request):
    """Отображение страницы База данных продаж"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_stock = date.today() - timedelta(days=1)
    seller_articles = Articles.objects.all()
    data = Sales.objects.filter(Q(pub_date__range=[
        control_date_stock,
        control_date_stock]))

    form = SelectDateForm(request.POST or None)
    datestart = control_date_stock
    datefinish = control_date_stock

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if article_filter == '':
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]))
        else:
            data = Sales.objects.filter(
                Q(pub_date__range=[datestart, datefinish]),
                Q(supplierArticle=article_filter))
    context = {
        'form': form,
        'data': data,
        'form_date': str(control_date_stock),
        'lenght': len(seller_articles.all().values()),
        'seller_articles': seller_articles.all().values(),
    }
    return render(request, 'database/database_sales.html', context)


def database_deliveries(request):
    """Отображение страницы База данных поставок"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_delivery = date.today() - timedelta(days=30)
    data = Deliveries.objects.filter(Q(delivery_date__range=[
        control_date_delivery,
        date.today()])).order_by('delivery_date')

    form = SelectDateForm(request.POST or None)
    datestart = control_date_delivery
    datefinish = date.today()

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if datestart:
            data = Deliveries.objects.filter(
                Q(delivery_date__gte=datestart)).order_by('delivery_date')
        if datefinish:
            data = Deliveries.objects.filter(
                Q(delivery_date__lte=datefinish)).order_by('delivery_date')
        if article_filter:
            data = Deliveries.objects.filter(
                Q(supplier_article=article_filter))
        return redirect('deliveries')
    context = {
        'form': form,
        'data': data,
    }
    return render(request, 'database/database_deliveries.html', context)


def database_orders(request):
    """Отображение страницы База данных заказов"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_orders = date.today() - timedelta(days=30)
    data = Orders.objects.filter(Q(order_date__range=[
        control_date_orders,
        date.today()])).order_by('order_date')

    form = SelectDateForm(request.POST or None)
    datestart = control_date_orders
    datefinish = date.today()

    if form.is_valid():
        datestart = form.cleaned_data.get("datestart")
        datefinish = form.cleaned_data.get("datefinish")
        article_filter = form.cleaned_data.get("article_filter")
        if datestart:
            data = Orders.objects.filter(
                Q(order_date__gte=datestart)).order_by('order_date')
        if datefinish:
            data = Orders.objects.filter(
                Q(order_date__lte=datefinish)).order_by('order_date')
        if article_filter:
            data = Orders.objects.filter(
                Q(supplier_article=article_filter))
        return redirect('deliveries')
    context = {
        'form': form,
        'data': data,
    }
    return render(request, 'database/database_orders.html', context)


def sales_report(request):
    """Отображение страницы База данных заказов"""
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    control_date_orders = date.today() - timedelta(days=10)
    
    data = SalesReportOnSales.objects.filter(Q(date_from__range=[
        control_date_orders,
        date.today()])).order_by('realizationreport_id')

    form = SelectDateForm(request.POST or None)
    datestart = control_date_orders
    datefinish = date.today()

    if request.POST:
        datestart = request.POST.get("datestart")
        datefinish = request.POST.get("datefinish")
        article_filter = request.POST.get("article_filter")
        report_number_filter=request.POST.get("report_number_filter")
        if datestart:
            data = SalesReportOnSales.objects.filter(
                Q(date_from__gt=datestart)).order_by('rrd_id')
        if datefinish:
            data = data.filter(
                Q(date_from__lt=datefinish)).order_by('rrd_id')
        if article_filter:
            data = data.filter(
                Q(sa_name=article_filter)).order_by('rrd_id')
        if report_number_filter:
            data = data.filter(
                Q(realizationreport_id=report_number_filter)).order_by('rrd_id')
    paginator = Paginator(data, 100)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)  # Если номер страницы не целый, возвращаем первую страницу
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)  # Если страница выходит за пределы, возвращаем последнюю страницу
    context = {
        'form': form,
        'data': data,
        'page_obj': page_obj,
    }
    return render(request, 'database/database_sales_report.html', context)



def weekly_sales_data(request):
    """Функция отвечает за отображение данных недельных продаж"""

    sales = Sales.objects.filter(finished_price__gte=0,
        brand='KINMAC').annotate(
        week=ExtractWeek('pub_date'),
        year=ExtractYear('pub_date')
    ).values('supplier_article', 'barcode', 'week', 'year').annotate(
        count=Count(Case(When(finished_price__gte=0, then=1),
                         
                    output_field=IntegerField()))
    ).order_by('supplier_article', 'barcode', 'year', 'week')

    articles_amount = Sales.objects.filter(finished_price__gte=0).annotate(
        week=TruncWeek('pub_date')
    ).values('week').annotate(
        count=Count('supplier_article')
    ).order_by('week')

    sales_data = Sales.objects.filter(finished_price__gte=0).annotate(
        week=ExtractWeek('pub_date'),
        year=ExtractYear('pub_date')
    ).values('week', 'year').order_by('year', 'week')

    # Создаем словарь с данными для передачи в шаблон
    data = {}
    week_data = []
    for tim in sales_data:
        week_year = f"{tim['week']}-{tim['year']}"
        week_data.append(week_year)
        #week_data.append('3-2024')
    unique_week = list(set(week_data))
    #sorted_list = sorted(unique_week, key=lambda x: (x['name'], x['age']))
    unique_week.sort()
    for sale in sales:
        supplier_article = sale['supplier_article']
        barcode = sale['barcode']
        week_year = f"{sale['week']}-{sale['year']}"
        count = sale['count']
        key = (supplier_article, barcode)
        if key not in data:
            data[key] = {}
        data[key][week_year] = count

    # Добавляем недостающие недели со значением 0
    for article_data in data.values():
        for week in unique_week:
            if week not in article_data:
                article_data[week] = 0

    context = {
        'data': data,
        'unique_week': unique_week,
        'articles_amount': articles_amount,
    }
    return render(request, 'database/sales_by_week.html', context)


class DatabaseDetailView(DetailView):
    model = Articles
    template_name = 'database/detail_view.html'
    context_object_name = 'article'


class DatabaseStockApiDetailView(ListView):
    model = StocksApi
    template_name = 'database/stock_api_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return StocksApi.objects.filter(
            nm_id=self.kwargs['nm_id'])


class DatabaseStockSiteDetailView(ListView):
    model = StocksSite
    template_name = 'database/stock_site_detail.html'
    context_object_name = 'articles'

    def get_queryset(self):
        return StocksSite.objects.filter(
            seller_article=self.kwargs['seller_article'])


class DatabaseSalesDetailView(ListView):
    model = Sales
    template_name = 'database/sales_detail.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(DatabaseSalesDetailView,
                        self).get_context_data(**kwargs)
        sales_amount = Sales.objects.filter(
            barcode=self.kwargs['barcode']).values('pub_date').annotate(
            count_true=Count('is_realization', filter=Q(is_realization='true'))
        )
        context.update({
            'sales_amount': sales_amount,
            'wbstocks': StocksApi.objects.filter(
                barcode=self.kwargs['barcode']).values()
        })
        return context

    def get_queryset(self):
        return Sales.objects.filter(
            barcode=self.kwargs['barcode'])


class DatabaseWeeklySalesDetailView(ListView):
    model = Sales
    template_name = 'database/sales_by_week_detail.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(DatabaseWeeklySalesDetailView,
                        self).get_context_data(**kwargs)

        sales = Sales.objects.filter(
            Q(barcode=self.kwargs['barcode']),
            Q(finished_price__gte=0)).annotate(
                week=ExtractWeek('pub_date'),
                year=ExtractYear('pub_date')
        ).values('supplier_article', 'barcode', 'week', 'year').annotate(
            count=Count(Case(When(finished_price__gte=0, then=1),
            output_field=IntegerField()))
        ).order_by('supplier_article', 'barcode', 'year', 'week')
        
        sales_data = Sales.objects.filter(
            Q(finished_price__gte=0)).annotate(
                week=ExtractWeek('pub_date'),
                year=ExtractYear('pub_date')
        ).values('week', 'year').order_by('year', 'week')

        # Получаем queryset вида [{'warehouse_name': 'Тула', 'week': 43, 'year': 2023, 'week_sales': 2}]
        warehouses = Sales.objects.filter(
            Q(barcode=self.kwargs['barcode']),
            Q(finished_price__gte=0)).annotate(
                week=ExtractWeek('pub_date'),
                year=ExtractYear('pub_date')
        ).values('warehouse_name', 'week', 'year'
                ).annotate(week_sales=Count('id', filter=Q(sales_date__gte=TruncWeek('sales_date')))
                ).order_by('warehouse_name')
        warehouses_list = []
        # Находим склады с которых были продажи и выводим в один список
        for warehouse in warehouses:
            if warehouse['warehouse_name'] not in warehouses_list:
                warehouses_list.append(warehouse['warehouse_name'])
        # Сортирую название складов по алфавиту
        warehouses_list.sort()

        data = {}
        week_data = []
        for tim in sales_data:
            week_year = f"{tim['week']}-{tim['year']}"
            week_data.append(week_year)
        unique_week = list(set(week_data))
        unique_week.sort()
        for sale in sales:
            supplier_article = sale['supplier_article']
            barcode = sale['barcode']
            week_year = f"{sale['week']}-{sale['year']}"
            count = sale['count']
            key = (supplier_article, barcode)
            if key not in data:
                data[key] = {}
            data[key][week_year] = count
        
        # Формирую новый словарь с данными по складам, что не
        # съезжали данные по неделям
        warehouses_data = {}
        for stock in warehouses:
            key = stock['warehouse_name']
            if key not in warehouses_data.keys():
                warehouses_data[key] = {}
            #if key in warehouses_data.keys():
            if  f"{stock['week']}-{stock['year']}" in warehouses_data[key].keys():
                warehouses_data[key][f"{stock['week']}-{stock['year']}"] += stock['week_sales']
            else:
                warehouses_data[key][f"{stock['week']}-{stock['year']}"] = stock['week_sales']
        
        # Добавляем недостающие недели со значением 0
        for warehouse_name, amount in warehouses_data.items():
            for week in unique_week:
                inner_dict = {}
                if week not in amount.keys():
                    amount[week] = ''
        for article_data in data.values():
            for week in unique_week:
                if week not in article_data:
                    article_data[week] = 0
        context.update({
            'data': data,
            'unique_week': unique_week,
            'sales': sales,
            'warehouses_data': warehouses_data,
            'warehouses_list': warehouses_list
        })
        return context

    def get_queryset(self):
        return Sales.objects.filter(
            barcode=self.kwargs['barcode'])


class DatabaseUpdateView(UpdateView):
    model = Articles
    template_name = 'database/create.html'
    form_class = ArticlesForm


class DatabaseDeleteView(DeleteView):
    model = Articles
    template_name = 'database/database_delete.html'
    success_url = '/stock/'


class DatabaseStockApiDeleteView(DeleteView):
    model = StocksApi
    template_name = 'database/stock_delete.html'
    success_url = '/stock/'


class DatabaseSalesDeleteView(DeleteView):
    model = Sales
    template_name = 'database/sales_delete.html'
    success_url = '/sales/'


@login_required
def create(request):
    error = ''
    if request.method == 'POST':
        form = ArticlesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('database_home')
        else:
            error = 'Форма была не верной'
    form = ArticlesForm()
    data = {
        'form': form,
        'error': error
    }
    return render(request, 'database/create.html', data)


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'database/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        return dict(list(context.items()))

    def get_success_url(self):
        return reverse_lazy('database_home')


def logout_user(request):
    logout(request)
    return redirect('login')
