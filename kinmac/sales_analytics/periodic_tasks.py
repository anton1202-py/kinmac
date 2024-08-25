from datetime import datetime

import pandas as pd
from celery_tasks.celery import app
from celery_tasks.tasks import sales_report_statistic
from database.models import (Articles, CodingMarketplaces, CostPrice,
                             SalesReportOnSales)
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side

from .models import (ArticleSaleAnalytic, CommonSaleAnalytic,
                     ReportForCommonSaleAnalytic)

FILTER_PLUS_DATA_LIST = ['Продажа', 'Корректная продажа', 'Сторно возвратов', 'Авансовая оплата за товар без движения']
FILTER_MINUS_DATA_LIST = ['Сторно продаж', 'Возврат', 'Корректный возврат', 'Компенсация ущерба']


@app.task
def articles_analytics_data():
    """Обновляет данные аналитики из еженедельных отчетов"""
    
    reports_numbers = SalesReportOnSales.objects.values_list('realizationreport_id').distinct()
    articles_list = Articles.objects.all()
    for report in reports_numbers:
        for article in articles_list:
            article = article
            report_number = report[0]
            analytic_date = SalesReportOnSales.objects.filter(realizationreport_id=report[0]).first().date_from
            sales_report_number = report_number
            marketplace = CodingMarketplaces.objects.get(marketpalce='Wildberries')


            main_queryset = SalesReportOnSales.objects.filter(
                realizationreport_id=report_number,
                nm_id=article.nomenclatura_wb
                    ).aggregate(
                        delivery_rub=Sum('delivery_rub'),
                    )
            sale_queryset = SalesReportOnSales.objects.filter(realizationreport_id=report_number,
                                                                          nm_id=article.nomenclatura_wb,
                                                                          supplier_oper_name__in=FILTER_PLUS_DATA_LIST).aggregate(
                    retail_price_withdisc_rub=Sum('retail_price_withdisc_rub'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_for_pay=Sum('ppvz_for_pay'),
                    amount_sales=Count('retail_amount'),
                    )
            sale_retail_price_withdisc_rub = sale_queryset['retail_price_withdisc_rub'] if sale_queryset['retail_price_withdisc_rub'] else 0
            sale_retail_amount = sale_queryset['retail_amount'] if sale_queryset['retail_amount'] else 0
            sale_for_pay = sale_queryset['ppvz_for_pay'] if sale_queryset['ppvz_for_pay'] else 0
            sales_amount = sale_queryset['amount_sales'] if sale_queryset['amount_sales'] else 0

            return_queryset = SalesReportOnSales.objects.filter(realizationreport_id=report_number,
                                                                          nm_id=article.nomenclatura_wb,
                                                                          supplier_oper_name__in=FILTER_MINUS_DATA_LIST).aggregate(
                    retail_price_withdisc_rub=Sum('retail_price_withdisc_rub'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_for_pay=Sum('ppvz_for_pay'),
                    amount_sales=Count('retail_amount')
                    )
            
            main_penalty = SalesReportOnSales.objects.filter(realizationreport_id=report_number,
                                                                          nm_id=article.nomenclatura_wb,
                                                                          supplier_oper_name='Штраф').aggregate(
                    penalty=Sum('penalty'),
                    )
            return_retail_price_withdisc_rub = return_queryset['retail_price_withdisc_rub'] if return_queryset['retail_price_withdisc_rub'] else 0
            return_retail_amount = return_queryset['retail_amount'] if return_queryset['retail_amount'] else 0
            return_returns = return_queryset['ppvz_for_pay'] if return_queryset['ppvz_for_pay'] else 0
            return_amount = return_queryset['amount_sales'] if return_queryset['amount_sales'] else 0

            sum_penalty = main_penalty['penalty'] if main_penalty['penalty'] else 0
            sum_logistic = main_queryset['delivery_rub'] if main_queryset['delivery_rub'] else 0

            common_sales_with_returns = sales_amount - return_amount
            realization_summ_sale = sale_retail_price_withdisc_rub - return_retail_price_withdisc_rub
            for_pay = sale_for_pay
            sale = sale_retail_amount - return_retail_amount
            returns = return_returns
            
            reimbursement_of_transportation_costs = 0
            payment_defective_and_lost = 0
            compensation_for_the_substituted = 0
            
            article_costprice = CostPrice.objects.filter(article=article).last().costprice if CostPrice.objects.filter(article=article).last().costprice else 0
            costprice_of_sales = common_sales_with_returns * article_costprice


            # costprice_of_sales = 

            penalty = sum_penalty

            logistic = sum_logistic
            average_logistic_cost = round((logistic / common_sales_with_returns), 2) if common_sales_with_returns != 0 else 0
            storage = 0
            ff_service = 0
            advertisment = 0

            refusals_and_returns_amount = return_amount

            average_percent_of_buyout = round((common_sales_with_returns / (common_sales_with_returns + refusals_and_returns_amount))*100, 2) if (common_sales_with_returns + refusals_and_returns_amount) != 0 else 0
            self_purchase = 0
            tax = sale * 0.06
            profit = for_pay - returns - penalty + reimbursement_of_transportation_costs +  payment_defective_and_lost - costprice_of_sales - logistic - tax
            average_profit_for_one_piece = profit / common_sales_with_returns if common_sales_with_returns != 0 else 0

            profit_with_self_purchase = average_profit_for_one_piece - self_purchase * average_profit_for_one_piece
            roi = average_profit_for_one_piece / (article_costprice + ff_service) if article_costprice != 0 or ff_service != 0 else 0
            profitability = (profit / realization_summ_sale) * 100 if realization_summ_sale != 0 else 0

            average_price_before_spp = realization_summ_sale/common_sales_with_returns if common_sales_with_returns else 0


            if ArticleSaleAnalytic.objects.filter(
                article=article,
                sales_report_number=sales_report_number).exists():

                ArticleSaleAnalytic.objects.filter(
                article=article,
                sales_report_number=sales_report_number).update(
                    analytic_date=analytic_date,
                    marketplace=marketplace,
                    average_price_before_spp=average_price_before_spp,
                    realization_summ_sale=realization_summ_sale,
                    sale=sale,
                    for_pay=for_pay,
                    returns=returns,
                    costprice_of_sales=costprice_of_sales,
                    penalty=penalty,
                    compensation_for_the_substituted=compensation_for_the_substituted,
                    reimbursement_of_transportation_costs=reimbursement_of_transportation_costs,
                    payment_defective_and_lost=payment_defective_and_lost,
                    logistic=logistic,
                    average_logistic_cost=average_logistic_cost,
                    storage=storage,
                    # box_multiplicity=box_multiplicity,
                    ff_service=ff_service,
                    advertisment=advertisment,
                    self_purchase=self_purchase,
                    refusals_and_returns_amount=refusals_and_returns_amount,
                    sales_amount=sales_amount,
                    common_sales_with_returns=common_sales_with_returns,
                    average_percent_of_buyout=average_percent_of_buyout,
                    average_profit_for_one_piece=average_profit_for_one_piece,
                    tax=tax,
                    profit=profit,
                    profit_with_self_purchase=profit_with_self_purchase,
                    roi=roi,
                    profitability=profitability
                )


            else:
                ArticleSaleAnalytic(
                    article=article,
                    analytic_date=analytic_date,
                    sales_report_number=sales_report_number,
                    marketplace=marketplace,
                    average_price_before_spp=average_price_before_spp,
                    realization_summ_sale=realization_summ_sale,
                    sale=sale,
                    for_pay=for_pay,
                    returns=returns,
                    costprice_of_sales=costprice_of_sales,
                    penalty=penalty,
                    compensation_for_the_substituted=compensation_for_the_substituted,
                    reimbursement_of_transportation_costs=reimbursement_of_transportation_costs,
                    payment_defective_and_lost=payment_defective_and_lost,
                    logistic=logistic,
                    average_logistic_cost=average_logistic_cost,
                    storage=storage,
                    # box_multiplicity=box_multiplicity,
                    ff_service=ff_service,
                    advertisment=advertisment,
                    self_purchase=self_purchase,
                    refusals_and_returns_amount=refusals_and_returns_amount,
                    sales_amount=sales_amount,
                    common_sales_with_returns=common_sales_with_returns,
                    average_percent_of_buyout=average_percent_of_buyout,
                    average_profit_for_one_piece=average_profit_for_one_piece,
                    tax=tax,
                    profit=profit,
                    profit_with_self_purchase=profit_with_self_purchase,
                    roi=roi,
                    profitability=profitability
                ).save()


@app.task
def commom_analytics_data():
    """Обновляет общие данные аналитики из аналитика каждого артикула"""
    articles_list = Articles.objects.all()
    for article in articles_list:
        analytic_queryset = ArticleSaleAnalytic.objects.filter(article=article)
        article_costprice = CostPrice.objects.filter(article=article).last().costprice if CostPrice.objects.filter(article=article).last().costprice else 0


        for data in analytic_queryset:

            if not ReportForCommonSaleAnalytic.objects.filter(article=article, sales_report_number=data.sales_report_number).exists():
                ReportForCommonSaleAnalytic(
                    article=article,
                    sales_report_number=data.sales_report_number,
                    analytic_date=data.analytic_date
                ).save()
                iteration_amount = len(ReportForCommonSaleAnalytic.objects.filter(article=article))
                if CommonSaleAnalytic.objects.filter(article=article).exists():
                    common_report_obj = CommonSaleAnalytic.objects.get(article=article)
                    
                    common_report_obj.realization_summ_sale += data.realization_summ_sale
                    common_report_obj.for_pay += data.for_pay
                    common_report_obj.sale += data.sale
                    common_report_obj.returns += data.returns
                    common_report_obj.costprice_of_sales += data.costprice_of_sales
                    common_report_obj.penalty += data.penalty

                    common_report_obj.compensation_for_the_substituted += data.compensation_for_the_substituted
                    common_report_obj.reimbursement_of_transportation_costs += data.reimbursement_of_transportation_costs
                    common_report_obj.payment_defective_and_lost += data.payment_defective_and_lost

                    common_report_obj.logistic += data.logistic
                    common_report_obj.average_logistic_cost = round(((common_report_obj.logistic + data.logistic) / (common_report_obj.common_sales_with_returns + data.common_sales_with_returns)), 2) if (common_report_obj.common_sales_with_returns + data.common_sales_with_returns) != 0 else 0

                    common_report_obj.storage += data.storage
                    common_report_obj.ff_service += data.ff_service
                    common_report_obj.self_purchase += data.self_purchase
                    common_report_obj.refusals_and_returns_amount += data.refusals_and_returns_amount

                    common_report_obj.sales_amount += data.sales_amount
                    common_report_obj.common_sales_with_returns += data.common_sales_with_returns

                    sum_sales_with_returns = common_report_obj.common_sales_with_returns + data.common_sales_with_returns
                    sum_common_sales_with_returns = (common_report_obj.common_sales_with_returns + 
                                                     data.common_sales_with_returns + 
                                                     common_report_obj.refusals_and_returns_amount + 
                                                     data.refusals_and_returns_amount)
                    common_report_obj.average_percent_of_buyout = round((sum_sales_with_returns / sum_common_sales_with_returns)*100, 2) if sum_common_sales_with_returns != 0 else 0

                    sum_profit = common_report_obj.profit + data.profit
                    sum_common_sales_with_returns = common_report_obj.common_sales_with_returns + data.common_sales_with_returns
                    common_report_obj.average_profit_for_one_piece = sum_profit / sum_common_sales_with_returns if sum_common_sales_with_returns != 0 else 0

                    common_report_obj.tax += data.tax
                    common_report_obj.profit += data.profit
                    common_report_obj.profit_with_self_purchase += data.profit_with_self_purchase

                    common_report_obj.roi = common_report_obj.average_profit_for_one_piece / (article_costprice + data.ff_service) if (article_costprice + data.ff_service) != 0  else 0

                    common_report_obj.profitability = (common_report_obj.profit / common_report_obj.realization_summ_sale) * 100 if common_report_obj.realization_summ_sale != 0 else 0

                    common_report_obj.save()
                else:
                    CommonSaleAnalytic(
                        article=article,
                        realization_summ_sale=data.realization_summ_sale,
                        for_pay=data.for_pay,
                        sale=data.sale,
                        returns=data.returns,
                        costprice_of_sales=data.costprice_of_sales,
                        penalty=data.penalty,

                        compensation_for_the_substituted=data.compensation_for_the_substituted,
                        reimbursement_of_transportation_costs=data.reimbursement_of_transportation_costs,
                        payment_defective_and_lost=data.payment_defective_and_lost,

                        logistic=data.logistic,
                        average_logistic_cost=data.average_logistic_cost,

                        storage=data.storage,
                        ff_service=data.ff_service,
                        self_purchase=data.self_purchase,
                        refusals_and_returns_amount=data.refusals_and_returns_amount,

                        sales_amount=data.sales_amount,
                        common_sales_with_returns=data.common_sales_with_returns,
                        average_percent_of_buyout=data.average_percent_of_buyout,
                        average_profit_for_one_piece=data.average_profit_for_one_piece,

                        tax=data.tax,
                        profit=data.profit,
                        profit_with_self_purchase=data.profit_with_self_purchase,

                        roi=data.roi,
                        profitability=data.profitability

                    ).save()


