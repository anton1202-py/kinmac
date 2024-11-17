from datetime import datetime, timedelta
import logging
from django.db.models import Count, Prefetch, Q, Case, When, Value, BooleanField, Sum, F, OuterRef, Subquery
from rest_framework import status, viewsets
from rest_framework.response import Response


from database.models import ArticlePriceStock, ArticleStorageCost, Articles, SalesReportOnSales
from google_table.serializers import ActionArticlesSerializer, MarketplaceCommissionSerializer, ProductInfoSerializer, SppPriceStockDataSerializer
from action.models import ArticleForAction
from kinmac.constants_file import BRAND_LIST
from database.periodic_tasks import update_info_about_articles
from reklama.models import ArticleDailyCostToAdv
from unit_economic.wb_tasks import wb_comission_add_to_db, wb_logistic_add_to_db
from unit_economic.models import MarketplaceCommission


logger = logging.getLogger(__name__)


class ProductInfoViewSet(viewsets.ViewSet):
    """ViewSet для работы с продуктами на платформе Wildberries"""
    # queryset = ProductPrice.objects.filter(platform=Platform.objects.get(platform_type=MarketplaceChoices.MOY_SKLAD))
    queryset = Articles.objects.all()
    serializer_class = ProductInfoSerializer

    def list(self, request):
        """Получение данных о продуктах из API и обновление базы данных"""
        updated_products = Articles.objects.all()
        serializer = ProductInfoSerializer(updated_products, many=True)
        return Response(
            {'articles amount': {len(updated_products)},
             'data': serializer.data},
            status=status.HTTP_200_OK)


class ActionArticleViewSet(viewsets.ViewSet):
    """ViewSet показывает в какой акции участвует артикул и какаяу него целевая цена"""
    queryset = ArticleForAction.objects.all()
    serializer_class = ActionArticlesSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        articles_for_actions = ArticleForAction.objects.select_related(
            'action').filter(article__brand__in=BRAND_LIST, action__date_finish__gte=datetime.now())
        # Структура для хранения результата
        result = {}
        for article_for_action in articles_for_actions:
            action_name = article_for_action.action.name

            if action_name not in result:
                result[action_name] = []
            serializer = ActionArticlesSerializer(article_for_action)
            result[action_name].append(serializer.data)
        return Response(result)


class MarketplaceCommissionViewSet(viewsets.ViewSet):
    """Отдает комиссии"""
    queryset = MarketplaceCommission.objects.all()
    serializer_class = MarketplaceCommissionSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        comissions = MarketplaceCommission.objects.filter(
            marketplace_product__brand__in=BRAND_LIST)
        print(len(comissions))
        serializer = MarketplaceCommissionSerializer(comissions, many=True)
        return Response(serializer.data)


class ArticleLogisticCostViewSet(viewsets.ViewSet):
    """Стоимость логистики каждого артикула за определенный период"""
    queryset = SalesReportOnSales.objects.all()
    # serializer_class = MarketplaceCommissionSerializer

    def post(self, request, *args, **kwargs):
        """Входящие данные - количество недель за которые нужно отдать данные"""

    def list(self, request):
        """Входящие данные - количество недель за которые нужно отдать данные"""

        weeks_amount = int(request.query_params.get('weeks'))
        end_date = datetime.now()
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=weeks_amount)

        logistic_cost = {}
        sales_dict = {}
        storage_cost = {}

        storage_data = ArticleStorageCost.objects.filter(date__gte=start_date,
                                                         date__lte=end_date,
                                                         article__brand__in=BRAND_LIST).values('article__common_article').annotate(storage_cost=Sum('warehouse_price'))
        for data in storage_data:
            storage_cost[data['article__common_article'].upper()
                         ] = round(data['storage_cost'], 2)

        logistic_data = SalesReportOnSales.objects.filter(
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).values('sa_name').annotate(
                logistic_cost=Sum('delivery_rub')
        )
        sale_data = SalesReportOnSales.objects.filter(
            doc_type_name='Продажа',
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).values('sa_name').annotate(sales_amount=Count('retail_amount'))
        for data in sale_data:
            sales_dict[data['sa_name']] = data['sales_amount']
        print(logistic_data)
        for data in logistic_data:
            if data['sa_name'] in sales_dict:
                logistic_cost[data['sa_name']] = {'logistic_cost': round(
                    data['logistic_cost'], 2), 'sales_amount': sales_dict[data['sa_name']],
                    'storage_cost': storage_cost[data['sa_name'].upper()] if data['sa_name'].upper() in storage_cost else 0,
                    'storage_per_sale': round(storage_cost[data['sa_name'].upper()]/sales_dict[data['sa_name']], 2) if data['sa_name'].upper() in storage_cost else 0,
                    'logistic_per_sale': round(data['logistic_cost']/sales_dict[data['sa_name']], 2)}
            else:
                logistic_cost[data['sa_name']] = {'logistic_cost': round(
                    data['logistic_cost'], 2), 'sales_amount': 0,
                    'storage_cost': storage_cost[data['sa_name']] if data['sa_name'] in storage_cost else 0,
                    'storage_per_sale': storage_cost[data['sa_name'].upper()] if data['sa_name'].upper() in storage_cost else 0,
                    'logistic_per_sale': round(data['logistic_cost'], 2)}

        return Response(logistic_cost)


class SppPriceStockDataViewSet(viewsets.ViewSet):
    """Отдает данные по SPP, остаткам, цене"""
    queryset = ArticlePriceStock.objects.all()
    serializer_class = SppPriceStockDataSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        data = ArticlePriceStock.objects.filter(
            article__brand__in=BRAND_LIST)
        print(len(data))
        serializer = SppPriceStockDataSerializer(data, many=True)
        return Response(serializer.data)


class AdvertCostViewSet(viewsets.ViewSet):
    """Отдает расходы рекламы на каждую продажу."""
    queryset = ArticleDailyCostToAdv.objects.all()
    serializer_class = SppPriceStockDataSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        weeks_amount = int(request.query_params.get('weeks'))
        end_date = datetime.now()
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=weeks_amount)
        sales_dict = {}
        adv_dict = {}
        adv_data = ArticleDailyCostToAdv.objects.filter(cost_date__gte=start_date, cost_date__lte=end_date,
                                                        article__brand__in=BRAND_LIST).values('article__nomenclatura_wb').annotate(sum_cost=Sum('cost'))
        for data in adv_data:
            adv_dict[data['article__nomenclatura_wb']] = data['sum_cost']
        sale_data = SalesReportOnSales.objects.filter(
            doc_type_name='Продажа',
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).values('nm_id').annotate(sales_amount=Count('retail_amount'), sales_sum=Sum('retail_amount'))
        for data in sale_data:
            sales_dict[data['nm_id']] = {
                'sales_amount': data['sales_amount'], 'sales_sum': data['sales_sum']}

        returned_dict = {}
        articles_data = Articles.objects.filter(brand__in=BRAND_LIST)
        for data in articles_data:
            returned_dict[data.common_article] = {
                'sales_amount': sales_dict[int(data.nomenclatura_wb)]['sales_amount'] if int(data.nomenclatura_wb) in sales_dict else 0,
                'adv_cost_sum': adv_dict[data.nomenclatura_wb] if data.nomenclatura_wb in adv_dict else 0,
                'adv_cost_per_sale': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_amount'], 2) if int(data.nomenclatura_wb) in sales_dict and data.nomenclatura_wb in adv_dict else 0,
                'drr': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_sum'], 4) * 100 if int(data.nomenclatura_wb) in sales_dict and data.nomenclatura_wb in adv_dict else 0
            }

        return Response(returned_dict)
