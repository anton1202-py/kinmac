from datetime import date, timedelta

import pandas as pd
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import ExtractMonth, ExtractWeek, ExtractYear, TruncWeek
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from ..database.forms import (
    ArticlesForm,
    LoginUserForm,
    SelectDateForm,
    SelectDateStocksForm,
)
from ..database.models import (
    Articles,
    Deliveries,
    Orders,
    Sales,
    SalesReportOnSales,
    StocksApi,
    StocksSite,
)


def database_home(request):
    if str(request.user) == "AnonymousUser":
        return redirect("login")

    data = Articles.objects.all()
    context = {
        "data": data,
    }
    if request.method == "POST" and request.FILES["myarticles"]:
        myfile = request.FILES["myarticles"]
        empexceldata = pd.read_excel(myfile)
        load_excel_data_wb_stock = pd.DataFrame(
            empexceldata,
            columns=[
                "Баркод",
                "Номенк WB",
                "Номенк OZON",
                "Арт",
                "Бренд",
                "Предмет",
                "SIZE",
                "MODEL",
                "COLOR",
                "CC",
                "Сред СС",
            ],
        )
        barcode_list = load_excel_data_wb_stock["Баркод"].to_list()
        nomenclatura_wb_list = load_excel_data_wb_stock["Номенк WB"].to_list()
        common_article_list = load_excel_data_wb_stock["Арт"].to_list()
        brand_list = load_excel_data_wb_stock["Бренд"].to_list()
        predmet_list = load_excel_data_wb_stock["Предмет"].to_list()
        size_list = load_excel_data_wb_stock["SIZE"].to_list()
        model_list = load_excel_data_wb_stock["MODEL"].to_list()
        color_list = load_excel_data_wb_stock["COLOR"].to_list()
        prime_cost_list = load_excel_data_wb_stock["CC"].to_list()
        average_cost_list = load_excel_data_wb_stock["Сред СС"].to_list()
        dbframe = empexceldata
        for i in range(len(common_article_list)):
            if Articles.objects.filter(Q(common_article=common_article_list[i])):
                Articles.objects.filter(common_article=common_article_list[i]).update(
                    barcode=barcode_list[i],
                    nomenclatura_wb=nomenclatura_wb_list[i],
                    brand=brand_list[i],
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
                    brand=brand_list[i],
                    predmet=predmet_list[i],
                    size=size_list[i],
                    model=model_list[i],
                    color=color_list[i],
                    prime_cost=prime_cost_list[i],
                    average_cost=average_cost_list[i],
                )
                obj.save()
    return render(request, "database/database_home.html", context)


def planning_sales_data(request):
    """Функция отвечает за отображение данных недельных продаж"""

    sales = (
        Sales.objects.filter(finished_price__gte=0)
        .annotate(week=ExtractWeek("pub_date"), year=ExtractYear("pub_date"))
        .values("supplier_article", "barcode", "week", "year")
        .annotate(
            count=Count(
                Case(When(finished_price__gte=0, then=1), output_field=IntegerField())
            )
        )
        .order_by("supplier_article", "barcode", "year", "week")
    )

    articles_amount = (
        Sales.objects.filter(finished_price__gte=0)
        .annotate(week=TruncWeek("pub_date"))
        .values("week")
        .annotate(count=Count("supplier_article"))
        .order_by("week")
    )

    sales_data = (
        Sales.objects.filter(finished_price__gte=0)
        .annotate(week=ExtractWeek("pub_date"), year=ExtractYear("pub_date"))
        .values("week", "year")
        .order_by("year", "week")
    )

    # Создаем словарь с данными для передачи в шаблон
    data = {}
    week_data = []
    for tim in sales_data:

        week_year = f"{tim['week']}-{tim['year']}"
        week_data.append(week_year)

    unique_week = list(set(week_data))
    unique_week.sort()

    for sale in sales:
        supplier_article = sale["supplier_article"]
        barcode = sale["barcode"]
        week_year = f"{sale['week']}-{sale['year']}"
        count = sale["count"]
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
        "data": data,
        "unique_week": unique_week,
        "articles_amount": articles_amount,
    }
    return render(request, "database/sales_by_week.html", context)


class DatabaseDetailView(DetailView):
    model = Articles
    template_name = "database/detail_view.html"
    context_object_name = "article"


class DatabaseStockApiDetailView(ListView):
    model = StocksApi
    template_name = "database/stock_api_detail.html"
    context_object_name = "articles"

    def get_queryset(self):
        return StocksApi.objects.filter(nm_id=self.kwargs["nm_id"])


class DatabaseStockSiteDetailView(ListView):
    model = StocksSite
    template_name = "database/stock_site_detail.html"
    context_object_name = "articles"

    def get_queryset(self):
        return StocksSite.objects.filter(seller_article=self.kwargs["seller_article"])


class DatabaseSalesDetailView(ListView):
    model = Sales
    template_name = "database/sales_detail.html"
    context_object_name = "articles"

    def get_context_data(self, **kwargs):
        context = super(DatabaseSalesDetailView, self).get_context_data(**kwargs)
        sales_amount = (
            Sales.objects.filter(barcode=self.kwargs["barcode"])
            .values("pub_date")
            .annotate(
                count_true=Count("is_realization", filter=Q(is_realization="true"))
            )
        )
        context.update(
            {
                "sales_amount": sales_amount,
                "wbstocks": StocksApi.objects.filter(
                    barcode=self.kwargs["barcode"]
                ).values(),
            }
        )
        return context

    def get_queryset(self):
        return Sales.objects.filter(barcode=self.kwargs["barcode"])


class DatabaseWeeklySalesDetailView(ListView):
    model = Sales
    template_name = "database/sales_by_week_detail.html"
    context_object_name = "articles"

    def get_context_data(self, **kwargs):
        context = super(DatabaseWeeklySalesDetailView, self).get_context_data(**kwargs)

        sales = (
            Sales.objects.filter(
                Q(barcode=self.kwargs["barcode"]), Q(finished_price__gte=0)
            )
            .annotate(week=ExtractWeek("pub_date"), year=ExtractYear("pub_date"))
            .values("supplier_article", "barcode", "week", "year")
            .annotate(
                count=Count(
                    Case(
                        When(finished_price__gte=0, then=1), output_field=IntegerField()
                    )
                )
            )
            .order_by("supplier_article", "barcode", "year", "week")
        )

        sales_data = (
            Sales.objects.filter(Q(finished_price__gte=0))
            .annotate(week=ExtractWeek("pub_date"), year=ExtractYear("pub_date"))
            .values("week", "year")
            .order_by("year", "week")
        )
        data = {}
        week_data = []
        for tim in sales_data:

            week_year = f"{tim['week']}-{tim['year']}"
            week_data.append(week_year)

        unique_week = list(set(week_data))
        unique_week.sort()

        for sale in sales:
            supplier_article = sale["supplier_article"]
            barcode = sale["barcode"]
            week_year = f"{sale['week']}-{sale['year']}"
            count = sale["count"]
            key = (supplier_article, barcode)
            if key not in data:
                data[key] = {}
            data[key][week_year] = count

        # Добавляем недостающие недели со значением 0
        for article_data in data.values():
            for week in unique_week:
                if week not in article_data:
                    article_data[week] = 0
        context.update(
            {
                "data": data,
                "unique_week": unique_week,
            }
        )
        return context

    def get_queryset(self):
        return Sales.objects.filter(barcode=self.kwargs["barcode"])


class DatabaseUpdateView(UpdateView):
    model = Articles
    template_name = "database/create.html"
    form_class = ArticlesForm


class DatabaseDeleteView(DeleteView):
    model = Articles
    template_name = "database/database_delete.html"
    success_url = "/stock/"


class DatabaseStockApiDeleteView(DeleteView):
    model = StocksApi
    template_name = "database/stock_delete.html"
    success_url = "/stock/"


class DatabaseSalesDeleteView(DeleteView):
    model = Sales
    template_name = "database/sales_delete.html"
    success_url = "/sales/"
