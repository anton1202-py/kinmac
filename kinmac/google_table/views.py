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
        try:
            articles_for_actions = ArticleForAction.objects.select_related(
                'action').filter(article__brand__in=BRAND_LIST, action__date_finish__gte=datetime.now()).order_by('article__common_article')
            # Структура для хранения результата
            result = {}
            for article_for_action in articles_for_actions:
                action_name = article_for_action.action.name
                date_start = article_for_action.action.date_start
                date_finish = article_for_action.action.date_finish

                if action_name not in result:
                    result[action_name] = {
                        'date_start': date_start, 'date_finish': date_finish, 'articles': []}
                serializer = ActionArticlesSerializer(article_for_action)
                result[action_name]['articles'].append(serializer.data)

            # Сортируем артикулы в акции по алфавиту
            return Response(result)
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            return Response({'error': f'Произошла ошибка при получении данных.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarketplaceCommissionViewSet(viewsets.ViewSet):
    """Отдает комиссии"""
    queryset = MarketplaceCommission.objects.all()
    serializer_class = MarketplaceCommissionSerializer

    def list(self, request):
        """Получеине данных а цене артикула в акции"""
        comissions = MarketplaceCommission.objects.filter(
            marketplace_product__brand__in=BRAND_LIST).order_by('marketplace_product__common_article')
        serializer = MarketplaceCommissionSerializer(comissions, many=True)
        return Response(serializer.data)


class ArticleLogisticCostViewSet(viewsets.ViewSet):
    """Стоимость логистики каждого артикула за определенный период"""
    queryset = SalesReportOnSales.objects.all()
    # serializer_class = MarketplaceCommissionSerializer

    def list(self, request):
        """Входящие данные - количество недель за которые нужно отдать данные"""

        weeks_amount = int(request.query_params.get('weeks'))
        end_date = datetime.now()
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=weeks_amount)

        logistic_cost = {}
        sales_dict = {}
        storage_cost = {}

        main_returned_dict = {}

        storage_data = ArticleStorageCost.objects.filter(date__gte=start_date,
                                                         date__lte=end_date,
                                                         article__brand__in=BRAND_LIST).order_by('article__common_article').values('article__nomenclatura_wb').annotate(storage_cost=Sum('warehouse_price'))

        for data in storage_data:
            storage_cost[int(data['article__nomenclatura_wb'])
                         ] = round(data['storage_cost'], 2)
        logistic_data = SalesReportOnSales.objects.filter(
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).order_by('sa_name').values('nm_id').annotate(
                logistic_cost=Sum('delivery_rub')
        )
        for data in logistic_data:
            logistic_cost[data['nm_id']] = round(data['logistic_cost'], 2)

        sale_data = SalesReportOnSales.objects.filter(
            doc_type_name='Продажа',
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).order_by('sa_name').values('nm_id').annotate(sales_amount=Count('retail_amount'))
        for data in sale_data:
            sales_dict[data['nm_id']] = data['sales_amount']

        for article_obj in Articles.objects.filter(brand__in=BRAND_LIST).order_by('common_article'):
            article_wb = int(article_obj.nomenclatura_wb)
            if article_wb in sales_dict:

                main_returned_dict[article_obj.common_article] = {
                    'logistic_cost': logistic_cost[article_wb] if article_wb in logistic_cost else 0,
                    'sales_amount': sales_dict[article_wb],
                    'storage_cost': storage_cost[article_wb] if article_wb in storage_cost else 0,
                    'storage_per_sale': round(storage_cost[article_wb]/sales_dict[article_wb], 2) if article_wb in storage_cost else 0,
                    'logistic_per_sale': round(logistic_cost[article_wb]/sales_dict[article_wb], 2) if article_wb in logistic_cost else 0, }
            else:
                main_returned_dict[article_obj.common_article] = {
                    'logistic_cost': logistic_cost[article_wb] if article_wb in logistic_cost else 0,
                    'sales_amount': 0,
                    'storage_cost': storage_cost[article_wb] if article_wb in storage_cost else 0,
                    'storage_per_sale': storage_cost[article_wb] if article_wb in storage_cost else 0,
                    'logistic_per_sale': logistic_cost[article_wb] if article_wb in logistic_cost else 0, }

        return Response(main_returned_dict)


class SppPriceStockDataViewSet(viewsets.ViewSet):
    """Отдает данные по SPP, остаткам, цене"""
    queryset = ArticlePriceStock.objects.all()
    serializer_class = SppPriceStockDataSerializer

    def list(self, request):
        """Отдает данные по SPP, остаткам, цене"""
        data = ArticlePriceStock.objects.filter(
            article__brand__in=BRAND_LIST).order_by('article__common_article')
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
                                                        article__brand__in=BRAND_LIST).order_by('article__common_article').values('article__nomenclatura_wb').annotate(sum_cost=Sum('cost'))
        for data in adv_data:
            adv_dict[data['article__nomenclatura_wb']] = data['sum_cost']
        sale_data = SalesReportOnSales.objects.filter(
            doc_type_name='Продажа',
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).order_by('sa_name').values('nm_id').annotate(sales_amount=Count('retail_amount'), sales_sum=Sum('retail_amount'))
        for data in sale_data:
            sales_dict[data['nm_id']] = {
                'sales_amount': data['sales_amount'], 'sales_sum': data['sales_sum']}

        returned_dict = {}
        articles_data = Articles.objects.filter(
            brand__in=BRAND_LIST).order_by('common_article')
        for data in articles_data:
            returned_dict[data.common_article] = {
                'sales_amount': sales_dict[int(data.nomenclatura_wb)]['sales_amount'] if int(data.nomenclatura_wb) in sales_dict else 0,
                'adv_cost_sum': round(adv_dict[data.nomenclatura_wb], 2) if data.nomenclatura_wb in adv_dict else 0,
                'adv_cost_per_sale': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_amount'], 2) if int(data.nomenclatura_wb) in sales_dict and data.nomenclatura_wb in adv_dict else 0,
                'drr': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_sum'] * 100, 2) if int(data.nomenclatura_wb) in sales_dict and data.nomenclatura_wb in adv_dict else 0
            }

        return Response(returned_dict)
