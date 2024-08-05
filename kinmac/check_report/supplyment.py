from datetime import date, timedelta

import pandas as pd
from celery_tasks.tasks import sales_report_statistic
from database.models import SalesReportOnSales
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

from .models import CommonSalesReportData


def report_reconciliation():
    """Сверка отчетов"""
    report_numbers = SalesReportOnSales.objects.all().values('realizationreport_id', 'date_from', 'date_to', 'create_dt').distinct()
    for report in report_numbers:
        easy_data = SalesReportOnSales.objects.filter(
                realizationreport_id=report['realizationreport_id']).aggregate(
                    delivery_rub=Sum('delivery_rub'),
                    storage_fee=Sum('storage_fee'),
                    deduction=Sum('deduction'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))
        sale_data = SalesReportOnSales.objects.filter(supplier_oper_name='Продажа',
                realizationreport_id=report['realizationreport_id']).aggregate(
                    sale_sum=Sum('retail_amount'), 
                    for_pay=Sum('ppvz_for_pay'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))
        sale_data_minus = SalesReportOnSales.objects.filter(
                realizationreport_id=report['realizationreport_id']).exclude(supplier_oper_name='Возврат').aggregate(
                    sale_sum=Sum('retail_amount'), 
                    for_pay=Sum('ppvz_for_pay'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))
        return_data = SalesReportOnSales.objects.filter(supplier_oper_name='Возврат',
                realizationreport_id=report['realizationreport_id']).aggregate(
                    sale_sum=Sum('retail_amount'), 
                    for_pay=Sum('ppvz_for_pay'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))

        return_data_ppvz_reward = return_data['ppvz_reward'] if return_data['ppvz_reward'] else 0
        return_data_acquiring_fee = return_data['acquiring_fee'] if return_data['acquiring_fee'] else 0
        return_data_ppvz_vw = return_data['ppvz_vw'] if return_data['ppvz_vw'] else 0
        return_data_ppvz_vw_nds = return_data['ppvz_vw_nds'] if return_data['ppvz_vw_nds'] else 0

        return_ppvz_sum = return_data_ppvz_reward + return_data_acquiring_fee + return_data_ppvz_vw + return_data_ppvz_vw_nds
        

        sale_data_ppvz_reward = sale_data['ppvz_reward'] if sale_data['ppvz_reward'] else 0
        sale_data_acquiring_fee = sale_data['acquiring_fee'] if sale_data['acquiring_fee'] else 0
        sale_data_ppvz_vw = sale_data['ppvz_vw'] if sale_data['ppvz_vw'] else 0
        sale_data_ppvz_vw_nds = sale_data['ppvz_vw_nds'] if sale_data['ppvz_vw_nds'] else 0

        sale_ppvz_sum = sale_data_ppvz_reward + sale_data_acquiring_fee + sale_data_ppvz_vw + sale_data_ppvz_vw_nds


        
        ppvz_reward = sale_data['ppvz_reward']
        acquiring_fee = sale_data['acquiring_fee']
        ppvz_vw = sale_data['ppvz_vw']
        ppvz_vw_nds=sale_data['ppvz_vw_nds']

        retail_amount = round(sale_data['retail_amount'], 2)
        return_amount = return_data['retail_amount'] if return_data['retail_amount'] else 0
        retail_without_return = retail_amount - return_amount

        ppvz_retail = round(sale_data['for_pay'], 2)
        ppvz_return = round((return_data['for_pay'] if return_data['for_pay'] else 0), 2)
        ppvz_for_pay = round((ppvz_retail - ppvz_return), 2)
        
        for_minus =  ppvz_reward + acquiring_fee + ppvz_vw + ppvz_vw_nds
        

        for_pay_sale = round((retail_amount - return_amount - (sale_ppvz_sum - return_ppvz_sum)), 2)
        if report['realizationreport_id'] == 268846777:
            print(report['realizationreport_id'], 'ppvz_retail', ppvz_retail, 'ppvz_for_pay', ppvz_for_pay, 'ppvz_return', ppvz_return)

       
        if not CommonSalesReportData.objects.filter(
            realizationreport_id=report['realizationreport_id'],
            date_from=report['date_from'],
            date_to=report['date_to'],
            create_dt=report['create_dt']).exists():
            CommonSalesReportData(
                realizationreport_id=report['realizationreport_id'],
                date_from=report['date_from'],
                date_to=report['date_to'],
                create_dt=report['create_dt'],

                retail_without_return=retail_without_return,
                retail_amount=retail_amount,
                return_amount=return_amount,

                ppvz_for_pay=ppvz_for_pay,
                ppvz_retail=ppvz_retail,
                ppvz_return=ppvz_return,

                delivery_rub=round(easy_data['delivery_rub'], 2),
                penalty=easy_data['deduction'],
                storage_fee=easy_data['storage_fee'],
                check_ppvz_for_pay=for_pay_sale
                    ).save()
        else:
            CommonSalesReportData.objects.filter(
                realizationreport_id=report['realizationreport_id'],
                date_from=report['date_from'],
                date_to=report['date_to'],
                create_dt=report['create_dt']).update(
                    retail_without_return=retail_without_return,
                    retail_amount=retail_amount,
                    return_amount=return_amount,

                    ppvz_for_pay=ppvz_for_pay,
                    ppvz_retail=ppvz_retail,
                    ppvz_return=ppvz_return,

                    delivery_rub=round(easy_data['delivery_rub'], 2),
                    penalty=easy_data['deduction'],
                    storage_fee=easy_data['storage_fee'],
                    check_ppvz_for_pay=for_pay_sale
                    )


#@sender_error_to_tg
def download_report_data_for_check(xlsx_file):
    """Импортирует данные о отчетах из Excel"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'Юридическое лицо' in column_list and 'Дата начала' in column_list and 'Продажа' in column_list and 'Стоимость логистики' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  '№ отчета', 'Продажа', 'К перечислению за товар', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания', 'Итого к оплате'])
        report_number_list = excel_data['№ отчета'].to_list()
        
        sale_list = excel_data['Продажа'].to_list()
        for_pay_list = excel_data['К перечислению за товар'].to_list()
        logistic_cost_list = excel_data['Стоимость логистики'].to_list()
        storage_cost_list = excel_data['Стоимость хранения'].to_list()
        other_deduction_list = excel_data['Прочие удержания'].to_list()
        total_to_paid_list = excel_data['Итого к оплате'].to_list()
        for i in range(len(report_number_list)):
            report_number = report_number_list[i]
            sale = sale_list[i]
            for_pay = for_pay_list[i]
            logistic_cost = logistic_cost_list[i]
            storage_cost = storage_cost_list[i]
            other_deduction = other_deduction_list[i]
            total_to_paid = total_to_paid_list[i]
            data_comparison(report_number, sale, for_pay, logistic_cost, storage_cost, other_deduction, total_to_paid)

    else:
        return f'Вы пытались загрузить ошибочный файл {xlsx_file}.'
    

def data_comparison(report_number, sale, for_pay, logistic_cost, storage_cost, other_deduction, total_to_paid):
    """Сравнивает данных из Excel файла и из базы данных"""
    repors_data = CommonSalesReportData.objects.exclude(check_fact=True)
    if CommonSalesReportData.objects.filter(realizationreport_id=report_number).exclude(check_fact=True).exists():
        report_object = CommonSalesReportData.objects.get(realizationreport_id=report_number)

        if report_object.retail_without_return == sale and report_object.ppvz_for_pay == for_pay and report_object.delivery_rub == logistic_cost:
            report_object.check_fact = True
            report_object.save()

