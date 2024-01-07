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

#@app.task
def delivery_statistic():
    """Добавляет данные по поставкам в базу данных"""
    try:
        control_date_delivery = date.today() - timedelta(days=30)
        url_delivery = f"https://statistics-api.wildberries.ru/api/v1/supplier/incomes?dateFrom={control_date_delivery}"
        # Заголовок и сам ключ
        APIKEY = {"Authorization": os.getenv('STATISTIC_WB_TOKEN')}
        response_delivery = requests.get(url_delivery, headers=APIKEY)
        data_deliveries = json.loads(response_delivery.text)
        common_data_deliveries = []
        for i in data_deliveries:
            check_data_deliveries = []
            check_data_deliveries.append(i['incomeId'])
            check_data_deliveries.append(i['number'])
            check_data_deliveries.append(i['date'])
            check_data_deliveries.append(i['lastChangeDate'])
            check_data_deliveries.append(i['supplierArticle'])
            check_data_deliveries.append(i['techSize'])
            check_data_deliveries.append(i['barcode'])
            check_data_deliveries.append(i['quantity'])
            check_data_deliveries.append(i['totalPrice'])
            check_data_deliveries.append(i['dateClose'])
            check_data_deliveries.append(i['warehouseName'])
            check_data_deliveries.append(i['nmId'])
            check_data_deliveries.append(i['status'])
            common_data_deliveries.append(check_data_deliveries)

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
            '''INSERT INTO database_deliveries (income_id,
                number,
                delivery_date,
                last_change_date,
                supplier_article,
                tech_size,
                barcode,
                quantity,
                total_price,
                date_close,
                warehouse_name,
                nmid,
                status) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
            common_data_deliveries)
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('delivery_statistic', delivery_statistic, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')


def orders_statistic():
    """Добавляет данные по заказам в базу данных"""
    try:
        control_date_order = date.today() - timedelta(days=3)
        url_order = f"https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={control_date_order}&flag=0"
        # Заголовок и сам ключ
        APIKEY = {"Authorization": os.getenv('STATISTIC_WB_TOKEN')}
        response_order = requests.get(url_order, headers=APIKEY)
        data_orders = json.loads(response_order.text)
        common_data_orders = []
        for i in data_orders:
            check_data_orders = []
            check_data_orders.append(i['date'])
            check_data_orders.append(i['lastChangeDate'])
            check_data_orders.append(i['warehouseName'])
            check_data_orders.append(i['countryName'])
            check_data_orders.append(i['oblastOkrugName'])
            check_data_orders.append(i['regionName'])
            check_data_orders.append(i['supplierArticle'])
            check_data_orders.append(i['nmId'])
            check_data_orders.append(i['barcode'])
            check_data_orders.append(i['category'])
            check_data_orders.append(i['subject'])
            check_data_orders.append(i['brand'])
            check_data_orders.append(i['techSize'])
            check_data_orders.append(i['incomeID'])
            check_data_orders.append(i['isSupply'])
            check_data_orders.append(i['isRealization'])
            check_data_orders.append(i['totalPrice'])
            check_data_orders.append(i['discountPercent'])
            check_data_orders.append(i['spp'])
            check_data_orders.append(i['finishedPrice'])
            check_data_orders.append(i['priceWithDisc'])
            check_data_orders.append(i['isCancel'])
            check_data_orders.append(i['cancelDate'])
            check_data_orders.append(i['orderType'])
            check_data_orders.append(i['sticker'])
            check_data_orders.append(i['gNumber'])
            check_data_orders.append(i['srid'])

            common_data_orders.append(check_data_orders)

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
            '''INSERT INTO database_orders (order_date,
                last_change_date,
                warehouse_name,
                country_name,
                oblast_okrug_name,
                region_name,
                supplier_article,
                nmid,
                barcode,
                category,
                subject,
                brand,
                tech_size,
                income_id,
                is_supply,
                is_realization,
                total_price,
                discount_percent,
                spp,
                finish_price,
                price_with_disc,
                is_cancel,
                cancel_date,
                order_type,
                sticker,
                g_number,
                srid) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
            common_data_orders)
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('delivery_statistic', orders_statistic, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text)

orders_statistic()
