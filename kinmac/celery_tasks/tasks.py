import json
import os
import traceback
from datetime import date, datetime, timedelta
from time import sleep
import jwt
import pandas as pd
import psycopg2
import requests
import telegram
from api_requests.wb_requests import (get_report_detail_by_period,
                                      get_statistic_delivery_api,
                                      get_statistic_order_api,
                                      get_statistic_sales_api,
                                      get_statistic_stock_api,
                                      get_stock_from_webpage_api,
                                      wb_article_data_from_api)
from celery_tasks.celery import app
from check_report.supplyment import report_reconciliation, write_sales_report_data_to_database
from database.models import SalesReportOnSales, WeeklyReportInDatabase
from database.supplyment import (add_data_delivery_to_db,
                                 add_data_orders_from_site_to_db,
                                 add_data_sales_to_db, add_data_stock_from_api,
                                 add_data_stock_from_web_api)
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from kinmac.constants_file import (TELEGRAM_ADMIN_CHAT_ID,
                                   bot, wb_headers)

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
    message_error = (f'Ошибка в функции: {function_name}\n'
                     f'Функция выполняет: {function.__doc__}\n'
                     f'Ошибка\n: {error_text}\n\n'
                     f'Техническая информация:\n {tb_str}')
    return message_error

@app.task
def check_wb_toket_expire():
    """
    Проверяет срок годности токена.
    Если срок годности меньше 5 дней - отправляет сообщение в ТГ
    """
    
    api_key = wb_headers['Authorization']
    decoded = jwt.decode(api_key, options={"verify_signature": False})
    timestamp = decoded['exp']
    dt_object = datetime.fromtimestamp(timestamp)
    # Форматирование в строку
    delta_time = dt_object - datetime.now()
    delta_days = delta_time.days
    if delta_days < 5:
        message = f'Токен ВБ истекает через {delta_days} дней. Срочно обновите его'
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                         text=message)

@app.task
def add_data_stock_api():
    try:
        control_date_stock = date.today() - timedelta(days=1)
        data_stock = get_statistic_stock_api(wb_headers, control_date_stock)
        for data in data_stock:
            add_data_stock_from_api(data)        
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('add_data_stock_api', add_data_stock_api, e)
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message_text, parse_mode='HTML')


@app.task
def add_data_sales():
    try:
        control_date_sales = date.today() - timedelta(days=1)
        data_sales = get_statistic_sales_api(wb_headers, control_date_sales)
        for data in data_sales:
            add_data_sales_to_db(data)  
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('add_data_sales', add_data_sales, e)
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message_text, parse_mode='HTML')

@app.task
def add_stock_data_site():
    #try:
    wb_stock_id_name = {
        507: 'Коледино', 686: 'Новосибирск', 1193: 'Хабаровск', 1733: 'Екатеринбург',
        2737: 'Санкт-Петербург', 115651: 'FBS Тамбов', 117392: 'FBS Владимир',
        117414:	'FBS Уткина Заводь', 117419: 'FBS Новосибирск', 117442: 'Калуга',
        117501:	'Подольск', 117866:	'Тамбов', 117986: 'Казань', 118365:	'FBS Красноярск',
        119261:	'FBS Коледино', 120762: 'Электросталь', 121700: 'FBS Минск',
        121709:	'Электросталь', 122252:	'FBS Москва 72', 122259: 'FBS Москва',
        122495:	'FBS Астана', 130744: 'Краснодар ', 131643: 'FBS Иркутск',
        132043:	'FBS Санкт-Петербург', 133533: 'FBS Ростов-на-Дону', 144046: 'FBS Калуга',
        144154:	'FBS Симферополь', 146666: 'FBS Самара', 146725: 'FBS Тюмень',
        152588:	'FBS Волгоград', 152594: 'FBS Рязань', 152610: 'FBS Тверь', 152611: 'FBS Челябинск',
        152612:	'FBS Ярославль', 152700: 'FBS Уфа', 157848:	'FBS Пенза', 158448: 'FBS Ставрополь',
        158929:	'FBS Саратов', 159402: 'Шушары ', 161812: 'Санкт-Петербург', 168826: 'FBS Лобня',
        172073:	'FBS Ижевск', 172075: 'FBS Курск', 172430:	'Барнаул', 204212:	'FBS Солнцево',
        204492:	'FBS Астрахань', 204493: 'FBS Барнаул', 204494: 'FBS Брянск', 204495: 'FBS Владикавказ',
        204496:	'FBS Вологда', 204497: 'FBS Пятигорск', 204498: 'FBS Серов', 204499: 'FBS Чебоксары',
        204615:	'Томск',
        204939:	'Астана',
        205104:	'Ульяновск',
        205205:	'Киров',
        205228:	'Белая Дача',
        206236:	'Белые Столбы',
        206239:	'FBS Белая Дача',
        206348:	'Алексин',
        206708:	'Новокузнецк',
        206844:	'Калининград',
        206968:	'Чехов',
        207743:	'Пушкино',
        208277:	'Невинномысск',
        208761:	'FBS Калининград',
        208768:	'FBS Абакан',
        208771:	'FBS Гомель',
        208772:	'FBS Иваново',
        208773:	'FBS Киров',
        208774:	'FBS Крыловская',
        208776:	'FBS Липецк',
        208777:	'FBS Мурманск',
        208778:	'FBS Набережные Челны',
        208780:	'FBS Оренбург',
        208781:	'FBS Печатники',
        208782:	'FBS Пушкино',
        208783:	'FBS Смоленск',
        208784:	'FBS Сургут',
        208785:	'FBS Темрюк',
        208786:	'FBS Томск',
        208787:	'FBS Чита',
        208789:	'FBS Новокузнецк',
        208815:	'FBS Екатеринбург',
        208816:	'FBS Ереван',
        208817:	'FBS Казань',
        208818:	'FBS Краснодар',
        208819:	'FBS Шушары',
        208820:	'FBS Хабаровск',
        208941:	'Домодедово',
        209106:	'FBS Чертановский',
        209107:	'FBS Нахабино',
        209108:	'FBS Курьяновская',
        209109:	'FBS Комсомольский',
        209110:	'FBS Южные ворота',
        209111:	'FBS Гольяново',
        209112:	'FBS Белые Столбы',
        209113:	'FBS Черная грязь',
        209510:	'FBS Электросталь',
        209513:	'Домодедово',
        209591:	'FBS Омск',
        209592:	'FBS Пермь',
        209601:	'FBS Невинномысск',
        209649:	'FBS Алексин',
        209902:	'FBS Артём',
        209950:	'FBS Ульяновск',
        210001:	'Чехов 2',
        210515:	'Вёшки',
        210815:	'FBS Хоргос',
        210967:	'FBS Домодедово',
        211622:	'Минск',
        211672:	'FBS Минск 2',
        211730:	'FBS Внуково',
        211790:	'FBS Екатеринбург 2',
        211895:	'FBS Воронеж',
        212031:	'FBS Мытищи',
        212032:	'FBS Вешки',
        212038:	'FBS Алматы 2',
        212419:	'FBS Нижний Новгород',
        213651:	'FBS Нижний Тагил',
        213892:	'FBS Белгород',
        214110:	'FBS Архангельск',
        214111:	'FBS Псков',
        214112:	'FBS Белогорск',
        215049:	'FBS Махачкала',
        216462:	'FBS Кемерово',
        216745:	'FBS Бишкек',
        217390:	'FBS Байсерке',
        217650:	'FBS Санкт-Петербург WBGo',
        217678:	'Внуково',
        217906:	'FBS Москва WBGo 2',
        218110:	'FBS Москва WBGo',
        218119:	'FBS Астана',
        218210:	'Обухово',
        218268:	'FBS Москва WBGo 3',
        218402:	'Иваново',
        218579:	'FBS Москва WBGo 4',
        218623:	'Подольск 3',
        218637:	'FBS Ташкент',
        218654:	'FBS Чехов',
        218658:	'FBS Москва WBGo 5',
        218659:	'FBS Москва WBGo 6',
        218660:	'FBS Москва WBGo 7',
        218671:	'FBS Обухово',
        218672:	'FBS Москва WBGo 8',
        218675:	'FBS Иваново',
        218699:	'FBS Шымкент',
        218720:	'FBS Ростов-на-Дону',
        218733:	'FBS Ош',
        218804:	'FBS Белая Дача',
        218841:	'FBS Ижевск',
        218893:	'FBS Южно-Сахалинск',
        218894:	'FBS Якутск',
        218904:	'FBS Москва WBGo 9',
        218905:	'FBS Москва WBGo 10',
        218906:	'FBS Москва WBGo 11',
        218907:	'FBS Москва WBGo 12',
        218951:	'FBS Москва WBGo 13',
        218952:	'FBS Москва WBGo 14',
        218953:	'FBS Москва WBGo 15',
        218987: 'Алматы Атакент WB',
        218991:	'FBS Чехов 2',
        100001056: 'СЦ Тест',
        100001346: 'СЦ для вычитания Нур-Султан',
        100002577: 'СЦ для вычитания восточный КЗ',
        100002632: 'FBS для отключения тест',
        100002632: 'FBS для отключения тест',
    }
    now = datetime.now()
    control_date = now.strftime("%Y-%m-%d %H:%M:%S")
    URL = 'https://card.wb.ru/cards/detail?appType=0&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&dest=-2133464&nm='
    article_data = wb_article_data_from_api(wb_headers)
    # print(article_data)
    article_dict = {}
    for article in article_data:
        article_dict[article['nmID']] = article['vendorCode']
    iter_amount = len(article_dict.keys()) // 15
    for k in range(iter_amount+1):
        start_point = k*15
        finish_point = (k+1)*15
        nom_info_list = list(article_dict.keys())[start_point:finish_point]
        helper = ''
        for i in nom_info_list:
            helper += str(i)+';'

        data = get_stock_from_webpage_api(str(helper))
        main_data = data['data']['products']
        for j in main_data:
            if 'priceU' in j:
                data_for_db = {}
                amount = 0
                data_for_db['pub_date'] = control_date
                data_for_db['seller_article'] = article_dict[j['id']]
                data_for_db['nomenclatura_wb'] = j['id']
                data_for_db['name'] = j['name']
                data_for_db['price_u'] = int(j['priceU']) / 100
                data_for_db['sale_price_u'] = int(j['salePriceU']) / 100
                data_for_db['sale'] = j['sale']
                data_for_db['basic_sale'] = 0
                data_for_db['basic_price_u'] = 0
                data_for_db['review_rating'] = j['reviewRating']
                data_for_db['feedbacks'] = j['feedbacks']
                data_for_db['promotions'] = j['promotions']
                for i in j['sizes'][0]['stocks']:
                    if i['wh'] not in wb_stock_id_name.keys():
                        warehouse = i['wh']
                    else:
                        warehouse = wb_stock_id_name[i['wh']]
                    
                    quantity = i['qty']
                    amount += i["qty"]
                    data_for_db['warehouse'] = warehouse
                    data_for_db['quantity'] = quantity
                    add_data_stock_from_web_api(data_for_db)
                    
                
                sleep(1)
    
    # except Exception as e:
    #     # обработка ошибки и отправка сообщения через бота
    #     message_text = error_message('add_stock_data_site', add_stock_data_site, e)
    #     bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message_text, parse_mode='HTML')


@app.task
def delivery_statistic():
    """Добавляет данные по поставкам в базу данных"""
    try:
        control_date_delivery = date.today() - timedelta(days=2)
        data_deliveries = get_statistic_delivery_api(wb_headers, control_date_delivery)

        if data_deliveries:
            for data in data_deliveries:
                add_data_delivery_to_db(data)
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('delivery_statistic', delivery_statistic, e)
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message_text, parse_mode='HTML')

@app.task
def orders_statistic():
    """Добавляет данные по заказам в базу данных"""
    try:
        control_date = date.today() - timedelta(days=2)
        data_orders = get_statistic_order_api(wb_headers, control_date)
        for data in data_orders:
            add_data_orders_from_site_to_db(data)
    except Exception as e:
       # обработка ошибки и отправка сообщения через бота
       message_text = error_message('delivery_statistic', orders_statistic, e)
       bot.send_message(chat_id=CHAT_ID, text=message_text)

@app.task
def sales_report_statistic():
    """Добавляет данные по отчету продаж"""
    start_date = date.today() - timedelta(days=90)
    finish_date = date.today() - timedelta(days=1)
    common_data = get_report_detail_by_period(wb_headers, start_date, finish_date)
    if common_data:
        reports_data = {}
        for data in common_data:
            if not WeeklyReportInDatabase.objects.filter(realizationreport_id=data['realizationreport_id']).exists():
                if data['realizationreport_id'] not in reports_data:
                    reports_data[data['realizationreport_id']] = {
                        'date_from': data['date_from'],
                        'date_to': data['date_to'],
                        'create_dt': data['create_dt']
                    }
                write_sales_report_data_to_database(data)
        if reports_data:
            for report_number, info in reports_data.items():
                WeeklyReportInDatabase(
                    realizationreport_id=report_number,
                    date_from=info['date_from'],
                    date_to=info['date_to'],
                    create_dt=info['create_dt']
                ).save()
        report_reconciliation()
