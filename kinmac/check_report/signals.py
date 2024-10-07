from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from database.models import Articles, CodingMarketplaces, CostPrice, SalesReportOnSales, StorageCost, WeeklyReportInDatabase
from kinmac.constants_file import BRAND_LIST, bot, TELEGRAM_ADMIN_CHAT_ID
from reklama.models import ArticleDailyCostToAdv
from sales_analytics.models import ArticleSaleAnalytic


@receiver(post_save, sender=WeeklyReportInDatabase)
def update_weekly_report_analytical_data(sender, instance, created, **kwargs):
    """
    Обновлеине аналитики еженедельного отчета, если обновляется сам отчет
    """
    try:
        articles_analytics_data(instance.realizationreport_id)
    except Exception as e:
        message = f'Не удалось обновить аналитику еженедельного отчета {instance.realizationreport_id}. Ошибка: {e}'
        bot.send_message(
                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message)


FILTER_PLUS_DATA_LIST = ['Продажа', 'Корректная продажа', 'Сторно возвратов', 'Авансовая оплата за товар без движения']
FILTER_MINUS_DATA_LIST = ['Сторно продаж', 'Возврат', 'Корректный возврат', 'Компенсация ущерба']


def articles_analytics_data(report_number):
    """Обновляет данные аналитики из еженедельных отчетов"""
    # Словарь вида: {номер_отчета: [{'nm_id': nom номер ВБ}}
    nm_ids_list = SalesReportOnSales.objects.filter(realizationreport_id=report_number, brand_name__in=BRAND_LIST).values('nm_id').distinct()
    analytic_date = SalesReportOnSales.objects.filter(realizationreport_id=report_number).first().date_from
    analytic_date_to = SalesReportOnSales.objects.filter(realizationreport_id=report_number).first().date_to
    date_start = analytic_date.strftime('%Y-%m-%d')
    date_finish = analytic_date_to.strftime('%Y-%m-%d')
    
    for nm_id_dict in nm_ids_list:
        if Articles.objects.filter(nomenclatura_wb=nm_id_dict['nm_id']).exists():
            article = Articles.objects.get(nomenclatura_wb=nm_id_dict['nm_id'])
            costs_data = StorageCost.objects.filter(article=article, start_date__range=[date_start, date_finish]).aggregate(storage_cost=Sum('storage_cost'))
            marketplace = CodingMarketplaces.objects.get(marketpalce='Wildberries')
            main_queryset = SalesReportOnSales.objects.filter(
                realizationreport_id=report_number,
                nm_id=nm_id_dict['nm_id']
                    ).aggregate(
                        delivery_rub=Sum('delivery_rub'),
                        rebill_logistic_cost=Sum('rebill_logistic_cost'),
                    )

            sale_queryset = SalesReportOnSales.objects.filter(realizationreport_id=report_number,
                                                                          nm_id=nm_id_dict['nm_id'],
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
                                                                          nm_id=nm_id_dict['nm_id'],
                                                                          supplier_oper_name__in=FILTER_MINUS_DATA_LIST).aggregate(
                    retail_price_withdisc_rub=Sum('retail_price_withdisc_rub'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_for_pay=Sum('ppvz_for_pay'),
                    amount_sales=Count('retail_amount')
                    )

            main_penalty = SalesReportOnSales.objects.filter(realizationreport_id=report_number,
                                                                          nm_id=nm_id_dict['nm_id'],
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
            reimbursement_of_transportation_costs = main_queryset['rebill_logistic_cost'] if main_queryset['rebill_logistic_cost'] else 0
            payment_defective_and_lost = 0
            compensation_for_the_substituted = 0
            article_costprice = CostPrice.objects.filter(article=article).last().costprice if CostPrice.objects.filter(article=article).last().costprice else 0
            costprice_of_sales = common_sales_with_returns * article_costprice
            penalty = sum_penalty
            logistic = sum_logistic
            average_logistic_cost = round((logistic / common_sales_with_returns), 2) if common_sales_with_returns != 0 else 0

            # Расходы на хранение
            storage = costs_data.get('storage_cost') if costs_data.get('storage_cost') else 0

            # Расходы на Фулфилмент
            ff_cost = CostPrice.objects.filter(article=article).last().ff_cost if CostPrice.objects.filter(article=article).last().ff_cost else 0
            ff_service = ff_cost * common_sales_with_returns

            # Рекламные расходы
            advertisment_cost_data = ArticleDailyCostToAdv.objects.filter(article=article, cost_date__range=(date_start, date_finish))
            advertisment = advertisment_cost_data.aggregate(cost_sum=Sum('cost'))['cost_sum'] if advertisment_cost_data else 0

            refusals_and_returns_amount = return_amount
            average_percent_of_buyout = round((common_sales_with_returns / (common_sales_with_returns + refusals_and_returns_amount))*100, 2) if (common_sales_with_returns + refusals_and_returns_amount) != 0 else 0
            
            # Самовыкупы
            self_purchase = 0

            # Налог
            tax = sale * 0.02

            profit = for_pay - returns - penalty + reimbursement_of_transportation_costs +  payment_defective_and_lost - costprice_of_sales - logistic - tax
            average_profit_for_one_piece = profit / common_sales_with_returns if common_sales_with_returns != 0 else 0
            profit_with_self_purchase = average_profit_for_one_piece - self_purchase * average_profit_for_one_piece
            roi = average_profit_for_one_piece / (article_costprice + ff_service) if article_costprice != 0 or ff_service != 0 else 0
            profitability = (profit / realization_summ_sale) * 100 if realization_summ_sale != 0 else 0

            # Средняя цена до СПП
            average_price_before_spp = realization_summ_sale/common_sales_with_returns if common_sales_with_returns else 0
            if ArticleSaleAnalytic.objects.filter(
                article=article,
                sales_report_number=report_number).exists():
                ArticleSaleAnalytic.objects.filter(
                article=article,
                sales_report_number=report_number).update(
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
                    sales_report_number=report_number,
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
        else:
            print(f'В базе нет артикула: {nm_id_dict["nm_id"]} в отчете {report_number}')