from datetime import datetime, timedelta
from django.db.models import Count, Sum

from database.models import ArticlePriceStock, ArticleStorageCost, Articles, SalesReportOnSales
from kinmac.constants_file import BRAND_LIST
from reklama.models import ArticleDailyCostToAdv
from unit_economic.models import MarketplaceCommission


class WbMarketplaceArticlesData:
    """Данные артикулов по ВБ"""

    def __init__(self, weeks_amount):
        self.weeks_amount = weeks_amount

    def only_sales_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=self.weeks_amount)
        response_dict = {}
        sales_dict = {}

        sale_data = SalesReportOnSales.objects.filter(
            doc_type_name='Продажа',
            date_from__gte=start_date,
            date_to__lte=end_date,
            brand_name__in=BRAND_LIST).order_by('sa_name').values('nm_id').annotate(sales_amount=Count('retail_amount'), sales_sum=Sum('retail_amount'))
        for data in sale_data:
            sales_dict[data['nm_id']] = {
                'sales_amount': data['sales_amount'], 'sales_sum': data['sales_sum']}
        for article_obj in Articles.objects.filter(brand__in=BRAND_LIST).order_by('common_article'):
            article_wb = int(article_obj.nomenclatura_wb)
            if article_wb in sales_dict:
                response_dict[article_wb] = {
                    'sales_amount': sales_dict[article_wb]['sales_amount'],
                    'sales_sum': sales_dict[article_wb]['sales_sum']
                }
            else:
                response_dict[article_wb] = {
                    'sales_amount': 0,
                    'sales_sum': 0
                }
        return response_dict

    def comission_data(self):
        comissions = MarketplaceCommission.objects.filter(
            marketplace_product__brand__in=BRAND_LIST).order_by('marketplace_product__common_article')
        response_dict = {}
        for data in comissions:
            response_dict[data.marketplace_product.common_article] = {
                'fbo_commission': data.fbo_commission,
                "width": data.marketplace_product.width,
                "height": data.marketplace_product.height,
                "length": data.marketplace_product.length
            }
        return response_dict

    def spp_stock_data(self):
        """Отдает данные по SPP, остаткам, цене"""
        stock_data = ArticlePriceStock.objects.filter(
            article__brand__in=BRAND_LIST).order_by('article__common_article')
        response_dict = {}
        for data in stock_data:
            response_dict[data.article.common_article] = {
                'date': data.date,
                'common_stock': data.common_stock,
                'price_after_seller_disc': data.price_after_seller_disc,
                'spp': data.spp
            }
        return response_dict

    def advert_data(self):
        """Получение данных а цене артикула в акции"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=self.weeks_amount)
        sales_dict = self.only_sales_data()
        adv_dict = {}
        adv_data = ArticleDailyCostToAdv.objects.filter(cost_date__gte=start_date, cost_date__lte=end_date,
                                                        article__brand__in=BRAND_LIST).order_by('article__common_article').values('article__nomenclatura_wb').annotate(sum_cost=Sum('cost'))
        for data in adv_data:
            adv_dict[data['article__nomenclatura_wb']] = data['sum_cost']

        response_dict = {}
        articles_data = Articles.objects.filter(
            brand__in=BRAND_LIST).order_by('common_article')
        for data in articles_data:
            response_dict[data.common_article] = {
                'sales_amount': sales_dict[int(data.nomenclatura_wb)]['sales_amount'],
                'adv_cost_sum': round(adv_dict[data.nomenclatura_wb], 2) if data.nomenclatura_wb in adv_dict else 0,
                'adv_cost_per_sale': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_amount'], 2) if data.nomenclatura_wb in adv_dict else 0,
                'drr': round(adv_dict[data.nomenclatura_wb]/sales_dict[int(data.nomenclatura_wb)]['sales_sum'] * 100, 2) if data.nomenclatura_wb in adv_dict else 0
            }
        return response_dict

    def logistic_storage_cost(self):
        """Входящие данные - количество недель за которые нужно отдать данные"""
        end_date = datetime.now()
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=self.weeks_amount)

        logistic_cost = {}
        sales_dict = self.only_sales_data()
        storage_cost = {}

        main_returned_dict = {}

        storage_data = ArticleStorageCost.objects.filter(
            date__gte=start_date,
            date__lte=end_date,
            article__brand__in=BRAND_LIST).order_by(
                'article__common_article').values(
                    'article__nomenclatura_wb').annotate(
                        storage_cost=Sum('warehouse_price'))

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

        for article_obj in Articles.objects.filter(brand__in=BRAND_LIST).order_by('common_article'):
            article_wb = int(article_obj.nomenclatura_wb)
            sales_amount = sales_dict[article_wb]['sales_amount']
            main_returned_dict[article_obj.common_article] = {
                'logistic_cost': logistic_cost[article_wb] if article_wb in logistic_cost else 0,
                'sales_amount': sales_amount,
                'storage_cost': storage_cost[article_wb] if article_wb in storage_cost else 0,
                'storage_per_sale': round(storage_cost[article_wb]/sales_amount, 2) if article_wb in storage_cost and sales_amount > 0 else 0,
                'logistic_per_sale': round(logistic_cost[article_wb]/sales_amount, 2) if article_wb in logistic_cost and sales_amount > 0 else 0, }
        return main_returned_dict