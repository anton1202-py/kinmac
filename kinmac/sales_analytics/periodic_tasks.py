from celery_tasks.celery import app
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from database.models import Articles, CostPrice
                             

from kinmac.constants_file import BRAND_LIST
from .models import ArticleSaleAnalytic, CommonSaleAnalytic

@app.task
def commom_analytics_data():
    """Обновляет общие данные аналитики из аналитика каждого артикула"""
    articles_list = Articles.objects.filter(brand__in=BRAND_LIST)
    for article in articles_list:
        if ArticleSaleAnalytic.objects.filter(article=article).exists():
            article_costprice = CostPrice.objects.filter(article=article).last().costprice if CostPrice.objects.filter(article=article).last().costprice else 0
            analytic_queryset = ArticleSaleAnalytic.objects.filter(article=article).aggregate(
                realization_summ_sale=Sum('realization_summ_sale'),
                for_pay=Sum('for_pay'),
                sale=Sum('sale'),
                returns=Sum('returns'),
                costprice_of_sales=Sum('costprice_of_sales'),
                penalty=Sum('penalty'),
                advertisment=Sum('advertisment'),
                compensation_for_the_substituted=Sum('compensation_for_the_substituted'),
                reimbursement_of_transportation_costs=Sum('reimbursement_of_transportation_costs'),
                payment_defective_and_lost=Sum('payment_defective_and_lost'),
                logistic=Sum('logistic'),
                storage=Sum('storage'),
                ff_service=Sum('ff_service'),
                self_purchase=Sum('self_purchase'),
                refusals_and_returns_amount=Sum('refusals_and_returns_amount'),
                sales_amount=Sum('sales_amount'),
                common_sales_with_returns=Sum('common_sales_with_returns'),
                tax=Sum('tax'),
                profit=Sum('profit'),
                profit_with_self_purchase=Sum('profit_with_self_purchase'),
            )

            realization_summ_sale = analytic_queryset['realization_summ_sale']
            for_pay = analytic_queryset['for_pay']
            sale = analytic_queryset['sale']
            returns = analytic_queryset['returns']
            costprice_of_sales = analytic_queryset['costprice_of_sales']
            penalty =  analytic_queryset['penalty']
            advertisment =  analytic_queryset['advertisment']
            compensation_for_the_substituted =  analytic_queryset['compensation_for_the_substituted']
            reimbursement_of_transportation_costs =  analytic_queryset['reimbursement_of_transportation_costs']
            payment_defective_and_lost =  analytic_queryset['payment_defective_and_lost']
            logistic =  analytic_queryset['logistic']
            storage =  analytic_queryset['storage']
            ff_service =  analytic_queryset['ff_service']
            self_purchase =  analytic_queryset['self_purchase']
            refusals_and_returns_amount = analytic_queryset['refusals_and_returns_amount']
            sales_amount =  analytic_queryset['sales_amount']
            common_sales_with_returns =  analytic_queryset['common_sales_with_returns']
            tax = analytic_queryset['tax']
            profit = analytic_queryset['profit']
            profit_with_self_purchase = analytic_queryset['profit_with_self_purchase']
            average_logistic_cost = round((logistic / common_sales_with_returns), 2) if common_sales_with_returns != 0 else 0
            # TODO Проверить это значение. Есть вероятность ошибки. Дублируется значение 'common_sales_with_returns'
            sum_sales_with_returns = common_sales_with_returns
            sum_common_sales_with_returns = common_sales_with_returns + refusals_and_returns_amount
            average_percent_of_buyout = round((sum_sales_with_returns / sum_common_sales_with_returns)*100, 2) if sum_common_sales_with_returns != 0 else 0
            average_profit_for_one_piece = profit / sum_common_sales_with_returns if sum_common_sales_with_returns != 0 else 0
            average_price_before_spp = realization_summ_sale/common_sales_with_returns if common_sales_with_returns != 0 else 0
            roi = (average_profit_for_one_piece / (article_costprice + ff_service))*100 if (article_costprice + ff_service) != 0  else 0
            profitability = (profit / realization_summ_sale) * 100 if realization_summ_sale != 0 else 0


            search_params = {'article': article}

            defaults = {
                'realization_summ_sale': realization_summ_sale,
                'for_pay': for_pay,
                'sale': sale,
                'returns': returns,
                'costprice_of_sales': costprice_of_sales,
                'penalty': penalty,
                'advertisment': advertisment,
                'compensation_for_the_substituted': compensation_for_the_substituted,
                'reimbursement_of_transportation_costs': reimbursement_of_transportation_costs,
                'payment_defective_and_lost': payment_defective_and_lost,
                'logistic': logistic,
                'average_logistic_cost': average_logistic_cost,
                'storage': storage,
                'ff_service': ff_service,
                'self_purchase': self_purchase,
                'refusals_and_returns_amount': refusals_and_returns_amount,
                'sales_amount': sales_amount,
                'common_sales_with_returns': common_sales_with_returns,
                'average_percent_of_buyout': average_percent_of_buyout,
                'profit': profit,
                'average_profit_for_one_piece': average_profit_for_one_piece,
                'tax': tax,
                'average_price_before_spp': average_price_before_spp,
                'profit_with_self_purchase': profit_with_self_purchase,
                'roi': roi,
                'profitability': profitability
            }

            CommonSaleAnalytic.objects.update_or_create(defaults=defaults, **search_params)