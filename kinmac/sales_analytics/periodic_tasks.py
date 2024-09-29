from celery_tasks.celery import app

from database.models import Articles, CostPrice
                             

from kinmac.constants_file import BRAND_LIST
from .models import ArticleSaleAnalytic, CommonSaleAnalytic

@app.task
def commom_analytics_data():
    """Обновляет общие данные аналитики из аналитика каждого артикула"""
    articles_list = Articles.objects.filter(brand__in=BRAND_LIST)
    for article in articles_list:
        analytic_queryset = ArticleSaleAnalytic.objects.filter(article=article)
        article_costprice = CostPrice.objects.filter(article=article).last().costprice if CostPrice.objects.filter(article=article).last().costprice else 0
        for data in analytic_queryset:
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

