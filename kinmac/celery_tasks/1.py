import json
import os
import traceback
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
import telegram
#from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def error_message(function_name: str, function, error_text: str) -> str:
    """
    Формирует текст ошибки и выводит информацию в модальном окне
    function_name - название функции.
    function - сама функция, как объект, а не результат работы. Без скобок.
    error_text - текст ошибки.
    """
    tb_str = traceback.format_exc()
    message_error = (f'Ошибка в функции: <b>{function_name}</b>\n'
                     f'<b>Функция выполняет</b>: {function.__doc__}\n'
                     f'<b>Ошибка</b>\n: {error_text}\n\n'
                     f'<b>Техническая информация</b>:\n {tb_str}')
    return message_error

#@app.task
def sales_report_statistic():
    """Добавляет данные по отчету продаж"""
    try:
        start_date = date.today() - timedelta(days=90)
        url_delivery = f"https://statistics-api.wildberries.ru/api/v1/supplier/reportDetailByPeriod?dateFrom={start_date}&dateTo={start_date}"
        # Заголовок и сам ключ
        APIKEY = {"Authorization": os.getenv('STATISTIC_WB_TOKEN')}
        response_report = requests.get(url_delivery, headers=APIKEY)
        data_report = json.loads(response_report.text)
        data_key_dict = {
                'realizationreport_id': 'integer',
                'date_from': 'text',
                'date_to': 'text',
                'create_dt': 'text',
                'currency_name': 'text',
                'suppliercontract_code': 'text',
                'rrd_id': 'integer',
                'gi_id': 'integer',
                'subject_name': 'text',
                'nm_id': 'integer',
                'brand_name': 'text',
                'sa_name': 'text',
                'ts_name': 'text',
                'barcode': 'text',
                'doc_type_name': 'text',
                'quantity': 'integer',
                'retail_price': 'float',
                'retail_amount': 'float',
                'sale_percent': 'integer',
                'commission_percent': 'float',
                'office_name': 'text',
                'supplier_oper_name': 'text',
                'order_dt': 'text',
                'sale_dt': 'text',
                'rr_dt': 'text',
                'shk_id': 'integer',
                'retail_price_withdisc_rub': 'float',
                'delivery_amount': 'integer',
                'return_amount': 'integer',
                'delivery_rub': 'float',
                'gi_box_type_name': 'text',
                'product_discount_for_report': 'float',
                'supplier_promo': 'float',
                'rid': 'integer',
                'ppvz_spp_prc': 'float',
                'ppvz_kvw_prc_base': 'float',
                'ppvz_kvw_prc': 'float',
                'sup_rating_prc_up': 'float',
                'is_kgvp_v2': 'float',
                'ppvz_sales_commission': 'float',
                'ppvz_for_pay': 'float',
                'ppvz_reward': 'float',
                'acquiring_fee': 'float',
                'acquiring_bank': 'text',
                'ppvz_vw': 'float',
                'ppvz_vw_nds': 'float',
                'ppvz_office_id': 'integer',
                'ppvz_office_name': 'text',
                'ppvz_supplier_id': 'integer',
                'ppvz_supplier_name': 'text',
                'ppvz_inn': 'text',
                'declaration_number': 'text',
                'bonus_type_name': 'text',
                'sticker_id': 'text',
                'site_country': 'text',
                'penalty': 'float',
                'additional_payment': 'float',
                'rebill_logistic_cost': 'float',
                'rebill_logistic_org': 'text',
                'kiz': 'text',
                'srid': 'text'
        }
        common_data_reports = []
        for i in data_report:
            check_data_reports = []
            for key, value in data_key_dict.items():
                if key in i.keys():
                    check_data_reports.append(i[key])
                else:
                    if value == 'text':
                        check_data_reports.append('')
                    else:
                        check_data_reports.append(0)
            #common_data_reports.append(check_data_reports)
            # Подключение к существующей базе данных
            connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                                          dbname=os.getenv('DB_NAME'),
                                          password=os.getenv('POSTGRES_PASSWORD'),
                                          host=os.getenv('DB_HOST'),
                                          port=os.getenv('DB_PORT'))
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            # Курсор для выполнения операций с базой данных
            cursor = connection.cursor()

            cursor.execute(
                '''
                INSERT INTO database_salesreportonSales (
                    realizationreport_id,
                    date_from,
                    date_to,
                    create_dt,
                    currency_name,
                    suppliercontract_code,
                    rrd_id,
                    gi_id,
                    subject_name,
                    nm_id,
                    brand_name,
                    sa_name,
                    ts_name,
                    barcode,
                    doc_type_name,
                    quantity,
                    retail_price,
                    retail_amount,
                    sale_percent,
                    commission_percent,
                    office_name,
                    supplier_oper_name,
                    order_dt,
                    sale_dt,
                    rr_dt,
                    shk_id,
                    retail_price_withdisc_rub,
                    delivery_amount,
                    return_amount,
                    delivery_rub,
                    gi_box_type_name,
                    product_discount_for_report,
                    supplier_promo,
                    rid,
                    ppvz_spp_prc,
                    ppvz_kvw_prc_base,
                    ppvz_kvw_prc,
                    sup_rating_prc_up,
                    is_kgvp_v2,
                    ppvz_sales_commission,
                    ppvz_for_pay,
                    ppvz_reward,
                    acquiring_fee,
                    acquiring_bank,
                    ppvz_vw,
                    ppvz_vw_nds,
                    ppvz_office_id,
                    ppvz_office_name,
                    ppvz_supplier_id,
                    ppvz_supplier_name,
                    ppvz_inn,
                    declaration_number,
                    bonus_type_name,
                    sticker_id,
                    site_country,
                    penalty,
                    additional_payment,
                    rebill_logistic_cost,
                    rebill_logistic_org,
                    kiz,
                    srid
                    ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (rrd_id) DO NOTHING;''',
                check_data_reports)
            connection.commit()
            # except:
            #     #connection.rollback()
            #     print("User with this rrd_id already exists")
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


    except Exception as e:
        #обработка ошибки и отправка сообщения через бота
        message_text = error_message('sales_report_statistic', sales_report_statistic, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')

sales_report_statistic()

#sales_report_statistic_test()
