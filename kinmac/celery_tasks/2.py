import json
import os
import traceback
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
import telegram
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

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





def add_data_sales():
    try:
        control_date_sales = date.today() - timedelta(days=1)
        url_sales = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={control_date_sales}&flag=1"

        # Заголовок и сам ключ
        APIKEY = {"Authorization": os.getenv('STATISTIC_WB_TOKEN')}
        response_stock = requests.get(url_sales, headers=APIKEY)
        data_sales = json.loads(response_stock.text)

        common_data_sales = []

        for i in data_sales:
            check_data_sales = []
            check_data_sales.append(control_date_sales)
            check_data_sales.append(i['date'])
            check_data_sales.append(i['lastChangeDate'])
            check_data_sales.append(i['supplierArticle'])
            check_data_sales.append(i['techSize'])
            check_data_sales.append(i['barcode'])
            check_data_sales.append(i['totalPrice'])
            check_data_sales.append(i['discountPercent'])
            check_data_sales.append(i['isSupply'])
            check_data_sales.append(i['isRealization'])
            check_data_sales.append(0)
            check_data_sales.append(i['warehouseName'])
            check_data_sales.append(i['countryName'])
            check_data_sales.append(i['oblastOkrugName'])
            check_data_sales.append(i['regionName'])
            check_data_sales.append(i['incomeID'])
            check_data_sales.append(i['saleID'])
            check_data_sales.append(0)
            check_data_sales.append(i['spp'])
            check_data_sales.append(i['forPay'])
            check_data_sales.append(i['finishedPrice'])
            check_data_sales.append(i['priceWithDisc'])
            check_data_sales.append(i['nmId'])
            check_data_sales.append(i['subject'])
            check_data_sales.append(i['category'])
            check_data_sales.append(i['brand'])
            check_data_sales.append(0)
            check_data_sales.append(i['gNumber'])
            check_data_sales.append(i['sticker'])
            check_data_sales.append(i['srid'])
            common_data_sales.append(check_data_sales)

        try:
            # Подключение к существующей базе данных
            connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                                          dbname=os.getenv('DB_NAME'),
                                          password=os.getenv('POSTGRES_PASSWORD'),
                                          host=os.getenv('DB_HOST'),
                                          port=os.getenv('DB_PORT'))
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            # Курсор для выполнения операций с базой данных
            cursor = connection.cursor()

            cursor.executemany(
                '''INSERT INTO database_sales (pub_date,
                    sales_date,
                    last_change_date,
                    supplier_article,
                    tech_size,
                    barcode,
                    total_price,
                    discount_percent,
                    is_supply,
                    is_realization,
                    promo_code_discount,
                    warehouse_name,
                    country_name,
                    oblast_okrug_name,
                    region_name,
                    income_id,
                    sale_id,
                    odid,
                    spp,
                    for_pay,
                    finished_price,
                    price_with_disc,
                    nm_id,
                    subject,
                    category,
                    brand,
                    is_storno,
                    g_number,
                    sticker,
                    srid) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
                common_data_sales)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с PostgreSQL закрыто")
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('add_data_sales', add_data_sales, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')


add_data_sales()