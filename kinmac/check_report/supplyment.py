from datetime import date, timedelta
from zipfile import ZipFile

import pandas as pd
from api_requests.wb_requests import get_report_detail_by_period
from database.models import SalesReportOnSales, StorageCost, WeeklyReportInDatabase
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

from kinmac.constants_file import wb_headers

from .models import CommonSalesReportData, ExcelReportData


def report_reconciliation():
    """Сверка отчетов"""
    report_numbers = SalesReportOnSales.objects.all().values('realizationreport_id', 'date_from', 'date_to', 'create_dt').distinct()
    for report in report_numbers:
        storage_sum = StorageCost.objects.filter(start_date__gte=report['date_from'], start_date__lte=report['date_to']).aggregate(
            result_data=Sum('storage_cost')
        )
        easy_data = SalesReportOnSales.objects.filter(
                realizationreport_id=report['realizationreport_id']).aggregate(
                    delivery_rub=Sum('delivery_rub'),
                    storage_fee=Sum('storage_fee'),
                    deduction=Sum('penalty'),
                    for_pay=Sum('ppvz_for_pay'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    acceptance=Sum('acceptance'),
                    penalty=Sum('deduction'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))
        
        sale_data = SalesReportOnSales.objects.filter(doc_type_name='Продажа',
                realizationreport_id=report['realizationreport_id']).aggregate(
                    for_pay=Sum('ppvz_for_pay'),
                    ppvz_reward=Sum('ppvz_reward'),
                    acquiring_fee=Sum('acquiring_fee'),
                    deduction=Sum('penalty'),
                    ppvz_vw=Sum('ppvz_vw'),
                    retail_amount=Sum('retail_amount'),
                    ppvz_vw_nds=Sum('ppvz_vw_nds'))

        return_data = SalesReportOnSales.objects.filter(doc_type_name='Возврат',
                realizationreport_id=report['realizationreport_id']).aggregate( 
                    for_pay=Sum('ppvz_for_pay'),
                    deduction=Sum('penalty'),
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

        retail_amount = round((sale_data['retail_amount'] if sale_data['retail_amount'] else 0), 2)
        return_amount = return_data['retail_amount'] if return_data['retail_amount'] else 0
        retail_without_return = retail_amount - return_amount

        ppvz_retail = round((sale_data['for_pay'] if sale_data['for_pay'] else 0), 2)
        ppvz_return = round((return_data['for_pay'] if return_data['for_pay'] else 0), 2)
        ppvz_for_pay = round((ppvz_retail - ppvz_return), 2)
        
        
        penalty = easy_data['penalty'] if easy_data['penalty'] else 0
        
        acceptance_goods = round((easy_data['acceptance'] if easy_data['acceptance'] else 0), 2)
        for_pay_sale = round((retail_amount - return_amount - (sale_ppvz_sum - return_ppvz_sum)), 2)

        delivery_rub = round(easy_data['delivery_rub'], 2)
        common_penalty = round((easy_data['penalty'] if easy_data['penalty'] else 0), 2)
        
        
        deduction = easy_data['deduction'] if easy_data['deduction'] else 0
        storage_fee = round((easy_data['storage_fee'] if easy_data['storage_fee'] else 0), 2)
        total_paid = ppvz_for_pay - delivery_rub - storage_fee - acceptance_goods - deduction - common_penalty
        total_paid = round(total_paid, 2)

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
                penalty=penalty,
                delivery_rub=delivery_rub,
                deduction=deduction,
                storage_fee=round(storage_sum['result_data']) if storage_sum['result_data'] else 0,
                acceptance_goods=acceptance_goods,
                common_penalty=common_penalty,
                check_ppvz_for_pay=for_pay_sale,
                total_paid=total_paid
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
                    penalty=penalty,
                    ppvz_for_pay=ppvz_for_pay,
                    ppvz_retail=ppvz_retail,
                    ppvz_return=ppvz_return,
                    delivery_rub=delivery_rub,
                    deduction=deduction,
                    acceptance_goods=acceptance_goods,
                    storage_fee=round(storage_sum['result_data']) if storage_sum['result_data'] else 0,
                    common_penalty=common_penalty,
                    check_ppvz_for_pay=for_pay_sale,
                    total_paid=total_paid
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


def add_data_to_db_from_excel(xlsx_file):
    """Записывает данные из Excel отчетов в базу данных"""
    excel_data_common = pd.read_excel(xlsx_file)
    column_list = excel_data_common.columns.tolist()
    if 'Юридическое лицо' in column_list and 'Дата начала' in column_list and 'Продажа' in column_list and 'Стоимость логистики' in column_list:
        excel_data = pd.DataFrame(excel_data_common, columns=[
                                  '№ отчета', 'Юридическое лицо', 'Дата начала', 'Дата конца', 'Дата формирования', 'Продажа', 'К перечислению за товар', 'Стоимость логистики', 'Стоимость хранения', 'Прочие удержания', 'Итого к оплате'])
        report_number_list = excel_data['№ отчета'].to_list()
        ur_lico_list = excel_data['Юридическое лицо'].to_list()
        start_date_list = excel_data['Дата начала'].to_list()
        finish_date_list = excel_data['Дата конца'].to_list()
        forming_date_list = excel_data['Дата формирования'].to_list()
        sale_list = excel_data['Продажа'].to_list()
        for_pay_list = excel_data['К перечислению за товар'].to_list()
        logistic_cost_list = excel_data['Стоимость логистики'].to_list()
        storage_cost_list = excel_data['Стоимость хранения'].to_list()
        other_deduction_list = excel_data['Прочие удержания'].to_list()
        total_to_paid_list = excel_data['Итого к оплате'].to_list()
        for i in range(len(report_number_list)):
            report_number = report_number_list[i]
            ur_lico = ur_lico_list[i]
            start_date = start_date_list[i]
            finish_date = finish_date_list[i]
            forming_date = forming_date_list[i]
            sale = sale_list[i]
            for_pay = for_pay_list[i]
            logistic_cost = logistic_cost_list[i]
            storage_cost = storage_cost_list[i]
            other_deduction = other_deduction_list[i]
            total_to_paid = total_to_paid_list[i]
            if ExcelReportData.objects.filter(realizationreport_id=report_number, date_from=start_date, date_to=finish_date).exists():
                ExcelReportData.objects.filter(realizationreport_id=report_number, date_from=start_date, date_to=finish_date).update(
                    ur_lico=ur_lico,
                    create_dt=forming_date,
                    retail_amount=sale,
                    ppvz_for_pay=for_pay,
                    delivery_rub=logistic_cost,
                    storage_fee=storage_cost,
                    deduction=other_deduction,
                    total_paid=total_to_paid
                )
            else:
                ExcelReportData(
                    realizationreport_id=report_number,
                    ur_lico=ur_lico,
                    date_from=start_date,
                    date_to=finish_date,
                    create_dt=forming_date,
                    retail_amount=sale,
                    ppvz_for_pay=for_pay,
                    delivery_rub=logistic_cost,
                    storage_fee=storage_cost,
                    deduction=other_deduction,
                    total_paid=total_to_paid
                ).save()



def data_comparison(report_number, sale, for_pay, logistic_cost, storage_cost, other_deduction, total_to_paid):
    """Сравнивает данных из Excel файла и из базы данных"""
    repors_data = CommonSalesReportData.objects.exclude(check_fact=True)
    if CommonSalesReportData.objects.filter(realizationreport_id=report_number).exclude(check_fact=True).exists():
        report_object = CommonSalesReportData.objects.get(realizationreport_id=report_number)

        if report_object.retail_without_return == sale and report_object.ppvz_for_pay == for_pay and report_object.delivery_rub == logistic_cost:
            report_object.check_fact = True
            report_object.save()


def write_sales_report_data_to_database(data):
    """
    Записывает полученные данные из еженедельного отчета реализации в базуданных
    """
    if SalesReportOnSales.objects.filter(
                realizationreport_id=data['realizationreport_id'],
                date_from=data['date_from'],
                date_to=data['date_to'],
                rrd_id=data['rrd_id']).exists():
        SalesReportOnSales.objects.filter(
            realizationreport_id=data['realizationreport_id'],
            date_from=data['date_from'],
            date_to=data['date_to'],
            rrd_id=data['rrd_id']).update(
                create_dt=data['create_dt'],
                currency_name=data['currency_name'],
                suppliercontract_code=data['suppliercontract_code'],
                gi_id=data['gi_id'],
                subject_name=data['subject_name'],
                nm_id=data['nm_id'],
                brand_name=data['brand_name'],
                sa_name=data['sa_name'],
                ts_name=data['ts_name'],
                barcode=data['barcode'],
                doc_type_name=data['doc_type_name'],
                quantity=data['quantity'],
                retail_price=data['retail_price'],
                retail_amount=data['retail_amount'],
                sale_percent=data['sale_percent'],
                commission_percent=data['commission_percent'],
                office_name=data['office_name'],
                supplier_oper_name=data['supplier_oper_name'],
                order_dt=data['order_dt'],
                sale_dt=data['sale_dt'],
                rr_dt=data['rr_dt'],
                shk_id=data['shk_id'],
                retail_price_withdisc_rub=data['retail_price_withdisc_rub'],
                delivery_amount=data['delivery_amount'],
                return_amount=data['return_amount'],
                delivery_rub=data['delivery_rub'],
                gi_box_type_name=data['gi_box_type_name'],
                product_discount_for_report=data['product_discount_for_report'],
                supplier_promo=data['supplier_promo'],
                rid=data['rid'],
                ppvz_spp_prc=data['ppvz_spp_prc'],
                ppvz_kvw_prc_base=data['ppvz_kvw_prc_base'],
                ppvz_kvw_prc=data['ppvz_kvw_prc'],
                sup_rating_prc_up=data['sup_rating_prc_up'],
                is_kgvp_v2=data['is_kgvp_v2'],
                ppvz_sales_commission=data['ppvz_sales_commission'],
                ppvz_for_pay=data['ppvz_for_pay'],
                ppvz_reward=data['ppvz_reward'],
                acquiring_fee=data['acquiring_fee'],
                acquiring_bank=data['acquiring_bank'],
                ppvz_vw=data['ppvz_vw'],
                ppvz_vw_nds=data['ppvz_vw_nds'],
                ppvz_office_id=data['ppvz_office_id'],
                ppvz_office_name=data['ppvz_office_name'],
                ppvz_supplier_id=data['ppvz_supplier_id'],
                ppvz_supplier_name=data['ppvz_supplier_name'],
                ppvz_inn=data['ppvz_inn'],
                declaration_number=data['declaration_number'],
                bonus_type_name=data.get('bonus_type_name', ''),
                sticker_id=data['sticker_id'],
                site_country=data['site_country'],
                penalty=data['penalty'],
                additional_payment=data['additional_payment'],
                rebill_logistic_cost=data.get('rebill_logistic_cost', 0),
                rebill_logistic_org=data.get('rebill_logistic_org', ''),
                kiz=data.get('kiz', ''),
                storage_fee=data['storage_fee'],
                deduction=data['deduction'],
                acceptance=data['acceptance'],
                srid=data['srid'],
                report_type=data['report_type']
            )
    else:
        SalesReportOnSales(
            realizationreport_id=data['realizationreport_id'],
            date_from=data['date_from'],
            date_to=data['date_to'],
            create_dt=data['create_dt'],
            currency_name=data['currency_name'],
            suppliercontract_code=data['suppliercontract_code'],
            rrd_id=data['rrd_id'],
            gi_id=data['gi_id'],
            subject_name=data['subject_name'],
            nm_id=data['nm_id'],
            brand_name=data['brand_name'],
            sa_name=data['sa_name'],
            ts_name=data['ts_name'],
            barcode=data['barcode'],
            doc_type_name=data['doc_type_name'],
            quantity=data['quantity'],
            retail_price=data['retail_price'],
            retail_amount=data['retail_amount'],
            sale_percent=data['sale_percent'],
            commission_percent=data['commission_percent'],
            office_name=data['office_name'],
            supplier_oper_name=data['supplier_oper_name'],
            order_dt=data['order_dt'],
            sale_dt=data['sale_dt'],
            rr_dt=data['rr_dt'],
            shk_id=data['shk_id'],
            retail_price_withdisc_rub=data['retail_price_withdisc_rub'],
            delivery_amount=data['delivery_amount'],
            return_amount=data['return_amount'],
            delivery_rub=data['delivery_rub'],
            gi_box_type_name=data['gi_box_type_name'],
            product_discount_for_report=data['product_discount_for_report'],
            supplier_promo=data['supplier_promo'],
            rid=data['rid'],
            ppvz_spp_prc=data['ppvz_spp_prc'],
            ppvz_kvw_prc_base=data['ppvz_kvw_prc_base'],
            ppvz_kvw_prc=data['ppvz_kvw_prc'],
            sup_rating_prc_up=data['sup_rating_prc_up'],
            is_kgvp_v2=data['is_kgvp_v2'],
            ppvz_sales_commission=data['ppvz_sales_commission'],
            ppvz_for_pay=data['ppvz_for_pay'],
            ppvz_reward=data['ppvz_reward'],
            acquiring_fee=data['acquiring_fee'],
            acquiring_bank=data['acquiring_bank'],
            ppvz_vw=data['ppvz_vw'],
            ppvz_vw_nds=data['ppvz_vw_nds'],
            ppvz_office_id=data['ppvz_office_id'],
            ppvz_office_name=data['ppvz_office_name'],
            ppvz_supplier_id=data['ppvz_supplier_id'],
            ppvz_supplier_name=data['ppvz_supplier_name'],
            ppvz_inn=data['ppvz_inn'],
            declaration_number=data['declaration_number'],
            bonus_type_name=data.get('bonus_type_name', ''),
            sticker_id=data['sticker_id'],
            site_country=data['site_country'],
            penalty=data['penalty'],
            additional_payment=data['additional_payment'],
            rebill_logistic_cost=data.get('rebill_logistic_cost', 0),
            rebill_logistic_org=data.get('rebill_logistic_org', ''),
            kiz=data.get('kiz', ''),
            storage_fee=data['storage_fee'],
            deduction=data['deduction'],
            acceptance=data['acceptance'],
            srid=data['srid'],
            report_type=data['report_type']
        ).save()
    

def rewrite_sales_order(date_from, date_to, realizationreport_id):
    """Перезаписывает необходимый отчет в базу данных"""
    main_data = get_report_detail_by_period(wb_headers, date_from, date_to) 
    SalesReportOnSales.objects.filter(
        realizationreport_id=realizationreport_id,
                        date_from=date_from,
                        date_to=date_to
                        ).delete()
    CommonSalesReportData.objects.filter(
        realizationreport_id=realizationreport_id,
                        date_from=date_from,
                        date_to=date_to
                        ).delete()
    if main_data:
        reports_data = {}
        for data in main_data:
            if data['realizationreport_id'] not in reports_data:
                reports_data[data['realizationreport_id']] = {
                    'date_from': data['date_from'],
                    'date_to': data['date_to'],
                    'create_dt': data['create_dt']
                }
            write_sales_report_data_to_database(data)
        report_reconciliation()
        if reports_data:
            for report_number, info in reports_data.items():
                update_weekly_data = WeeklyReportInDatabase.objects.filter(
                    realizationreport_id=report_number)
                if update_weekly_data:
                    for data in update_weekly_data:
                        data.date_from=info['date_from']
                        data.date_to=info['date_to']
                        data.create_dt=info['create_dt']
                        data.save()
                else:
                    WeeklyReportInDatabase(
                        realizationreport_id=report_number,
                        date_from=info['date_from'],
                        date_to=info['date_to'],
                        create_dt=info['create_dt']
                    ).save()
                

def rewrite_sales_order_from_zip(date_from, date_to, realizationreport_id, zip_address):
    """Перезаписывает необходимый отчет в базу данных"""
    SalesReportOnSales.objects.filter(
        realizationreport_id=realizationreport_id,
                        date_from=date_from,
                        date_to=date_to
                        ).delete()
    CommonSalesReportData.objects.filter(
        realizationreport_id=realizationreport_id,
                        date_from=date_from,
                        date_to=date_to
                        ).delete()
    with ZipFile(zip_address, "r") as myzip:
        for item in myzip.namelist():
            content = myzip.read(item)
            add_data_to_db_from_analytic_report_zip(date_from, date_to, realizationreport_id, content)
    report_reconciliation()
    update_weekly_data = WeeklyReportInDatabase.objects.filter(
        realizationreport_id=realizationreport_id)
    if update_weekly_data:
        for data in update_weekly_data:
            data.date_from=date_from
            data.date_to=date_to
            data.save()
    else:
        WeeklyReportInDatabase(
            realizationreport_id=realizationreport_id,
            date_from=date_from,
            date_to=date_to
        ).save()
    

def add_data_to_db_from_analytic_report_zip(date_from, date_to, realizationreport_id, xlsx_file):
    """Записывает данные в базу данных из файла ZIP"""
    excel_data_common = pd.read_excel(xlsx_file)    
    excel_data = pd.DataFrame(excel_data_common, columns=[
        '№', 
        'Номер поставки', 
        'Предмет', 
        'Код номенклатуры', 
        'Бренд', 
        'Артикул поставщика', 
        'Название', 
        'Размер', 
        'Баркод', 
        'Тип документа', 
        'Обоснование для оплаты', 
        'Дата заказа покупателем', 
        'Дата продажи', 
        'Кол-во', 
        'Цена розничная', 
        'Вайлдберриз реализовал Товар (Пр)', 
        'Согласованный продуктовый дисконт, %', 
        'Промокод %', 
        'Итоговая согласованная скидка, %', 
        'Цена розничная с учетом согласованной скидки', 
        'Размер снижения кВВ из-за рейтинга, %', 
        'Размер снижения кВВ из-за акции, %', 
        'Скидка постоянного Покупателя (СПП), %', 
        'Размер кВВ, %', 
        'Размер  кВВ без НДС, % Базовый', 
        'Итоговый кВВ без НДС, %', 
        'Вознаграждение с продаж до вычета услуг поверенного, без НДС', 
        'Возмещение за выдачу и возврат товаров на ПВЗ', 
        'Возмещение издержек по эквайрингу', 
        'Размер комиссии за эквайринг, %', 
        'Вознаграждение Вайлдберриз (ВВ), без НДС', 
        'НДС с Вознаграждения Вайлдберриз', 
        'К перечислению Продавцу за реализованный Товар', 
        'Количество доставок', 
        'Количество возврата', 
        'Услуги по доставке товара покупателю', 
        'Общая сумма штрафов', 
        'Доплаты', 
        'Виды логистики, штрафов и доплат', 
        'Стикер МП', 
        'Наименование банка-эквайера', 
        'Номер офиса', 
        'Наименование офиса доставки', 
        'ИНН партнера', 
        'Партнер', 
        'Склад', 
        'Страна', 
        'Тип коробов', 
        'Номер таможенной декларации', 
        'Код маркировки', 
        'ШК', 
        'Rid', 
        'Srid', 
        'Возмещение издержек по перевозке/по складским операциям с товаром', 
        'Организатор перевозки', 
        'Хранение', 
        'Удержания', 
        'Платная приемка', 
        'Фиксированный коэффициент склада по поставке', 
        'Дата начала действия фиксации', 
        'Дата конца действия фиксации'])
 
    
    gi_id = excel_data['Номер поставки'].to_list()
    subject_name = excel_data['Предмет'].to_list()
    nm_id = excel_data['Код номенклатуры'].to_list()
    brand_name = excel_data['Бренд'].to_list()
    sa_name = excel_data['Артикул поставщика'].to_list()
    ts_name = excel_data['Размер'].to_list()
    barcode = excel_data['Баркод'].to_list()
    doc_type_name = excel_data['Тип документа'].to_list()
    supplier_oper_name = excel_data['Обоснование для оплаты'].to_list()
    order_dt = excel_data['Дата заказа покупателем'].to_list()
    sale_dt = excel_data['Дата продажи'].to_list()
    quantity = excel_data['Кол-во'].to_list()
    retail_price = excel_data['Цена розничная'].to_list()
    retail_amount = excel_data['Вайлдберриз реализовал Товар (Пр)'].to_list()
    product_discount_for_report = excel_data['Согласованный продуктовый дисконт, %'].to_list()
    supplier_promo = excel_data['Промокод %'].to_list()
    sale_percent = excel_data['Итоговая согласованная скидка, %'].to_list()
    retail_price_withdisc_rub = excel_data['Цена розничная с учетом согласованной скидки'].to_list()
    sup_rating_prc_up = excel_data['Размер снижения кВВ из-за рейтинга, %'].to_list()
    is_kgvp_v2 = excel_data['Размер снижения кВВ из-за акции, %'].to_list()
    ppvz_spp_prc = excel_data['Скидка постоянного Покупателя (СПП), %'].to_list()
    commission_percent = excel_data['Размер кВВ, %'].to_list()
    ppvz_kvw_prc_base = excel_data['Размер  кВВ без НДС, % Базовый'].to_list()
    ppvz_kvw_prc = excel_data['Итоговый кВВ без НДС, %'].to_list()
    ppvz_sales_commission = excel_data['Вознаграждение с продаж до вычета услуг поверенного, без НДС'].to_list()
    ppvz_reward = excel_data['Возмещение за выдачу и возврат товаров на ПВЗ'].to_list()
    acquiring_fee = excel_data['Возмещение издержек по эквайрингу'].to_list()
    # = excel_data['Размер комиссии за эквайринг, %'].to_list()
    ppvz_vw = excel_data['Вознаграждение Вайлдберриз (ВВ), без НДС'].to_list()
    ppvz_vw_nds = excel_data['НДС с Вознаграждения Вайлдберриз'].to_list()
    ppvz_for_pay = excel_data['К перечислению Продавцу за реализованный Товар'].to_list()
    delivery_amount = excel_data['Количество доставок'].to_list()
    return_amount = excel_data['Количество возврата'].to_list()
    delivery_rub = excel_data['Услуги по доставке товара покупателю'].to_list()
    penalty = excel_data['Общая сумма штрафов'].to_list()
    additional_payment = excel_data['Доплаты'].to_list()
    bonus_type_name = excel_data['Виды логистики, штрафов и доплат'].to_list()
    sticker_id = excel_data['Стикер МП'].to_list()
    acquiring_bank = excel_data['Наименование банка-эквайера'].to_list()
    ppvz_office_id = excel_data['Номер офиса'].to_list()
    ppvz_office_name = excel_data['Наименование офиса доставки'].to_list()
    ppvz_inn = excel_data['ИНН партнера'].to_list()
    ppvz_supplier_name = excel_data['Партнер'].to_list()
    office_name = excel_data['Склад'].to_list()
    site_country = excel_data['Страна'].to_list()
    gi_box_type_name = excel_data['Тип коробов'].to_list()
    declaration_number = excel_data['Номер таможенной декларации'].to_list()
    kiz = excel_data['Код маркировки'].to_list()
    shk_id = excel_data['ШК'].to_list()
    rid = excel_data['Rid'].to_list()
    srid = excel_data['Srid'].to_list()
    rebill_logistic_cost = excel_data['Возмещение издержек по перевозке/по складским операциям с товаром'].to_list()
    rebill_logistic_org = excel_data['Организатор перевозки'].to_list()
    storage_fee = excel_data['Хранение'].to_list()
    deduction = excel_data['Удержания'].to_list()
    acceptance = excel_data['Платная приемка'].to_list()
    # = excel_data['Фиксированный коэффициент склада по поставке'].to_list()
    # = excel_data['Дата начала действия фиксации'].to_list()
    # = excel_data['Дата конца действия фиксации'].to_list()
    for i in range(len(sa_name)):
        
        SalesReportOnSales(
            realizationreport_id=realizationreport_id,
            date_from=date_from,
            date_to=date_to,
            # create_dt=create_dt[i],
            # currency_name=currency_name[i],
            # suppliercontract_code=suppliercontract_code[i],
            # rrd_id=rrd_id[i],
            gi_id=gi_id[i],
            subject_name=subject_name[i],
            nm_id=nm_id[i],
            brand_name=brand_name[i],
            sa_name=sa_name[i],
            ts_name=ts_name[i],
            barcode=barcode[i],
            doc_type_name=doc_type_name[i],
            quantity=quantity[i],
            retail_price=retail_price[i],
            retail_amount=retail_amount[i],
            sale_percent=sale_percent[i],
            commission_percent=commission_percent[i],
            office_name=office_name[i],
            supplier_oper_name=supplier_oper_name[i],
            order_dt=order_dt[i],
            sale_dt=sale_dt[i],
            # rr_dt=rr_dt[i],
            shk_id=shk_id[i],
            retail_price_withdisc_rub=retail_price_withdisc_rub[i],
            delivery_amount=delivery_amount[i],
            return_amount=return_amount[i],
            delivery_rub=delivery_rub[i],
            gi_box_type_name=gi_box_type_name[i],
            product_discount_for_report=product_discount_for_report[i],
            supplier_promo=supplier_promo[i],
            rid=rid[i] if str(rid[i]) != 'nan' else 0,
            ppvz_spp_prc=ppvz_spp_prc[i],
            ppvz_kvw_prc_base=ppvz_kvw_prc_base[i],
            ppvz_kvw_prc=ppvz_kvw_prc[i],
            sup_rating_prc_up=sup_rating_prc_up[i],
            is_kgvp_v2=is_kgvp_v2[i],
            ppvz_sales_commission=ppvz_sales_commission[i],
            ppvz_for_pay=ppvz_for_pay[i],
            ppvz_reward=ppvz_reward[i],
            acquiring_fee=acquiring_fee[i] if str(acquiring_fee[i]) != 'nan' else 0,
            acquiring_bank=acquiring_bank[i],
            ppvz_vw=ppvz_vw[i],
            ppvz_vw_nds=ppvz_vw_nds[i],
            ppvz_office_id=ppvz_office_id[i] if str(ppvz_office_id[i]) != 'nan' else None,
            ppvz_office_name=ppvz_office_name[i],
            # ppvz_supplier_id=ppvz_supplier_id[i],
            ppvz_supplier_name=ppvz_supplier_name[i],
            ppvz_inn=ppvz_inn[i],
            declaration_number=declaration_number[i],
            bonus_type_name=bonus_type_name[i],
            sticker_id=sticker_id[i],
            site_country=site_country[i],
            penalty=penalty[i],
            additional_payment=additional_payment[i],
            rebill_logistic_cost=rebill_logistic_cost[i],
            rebill_logistic_org=rebill_logistic_org[i],
            kiz=kiz[i],
            storage_fee=storage_fee[i],
            deduction=deduction[i],
            acceptance=acceptance[i],
            srid=srid[i]
            # report_type=report_type[i]
        ).save()