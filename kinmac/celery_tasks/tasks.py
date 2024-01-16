import json
import os
import traceback
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
import telegram
from celery_tasks.celery import app
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

@app.task
def add_data_stock_api():
    try:
        control_date_stock = date.today() - timedelta(days=1)
        url_stock = f"https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={control_date_stock}"

        # Заголовок и сам ключ
        APIKEY = {"Authorization": os.getenv('STATISTIC_WB_TOKEN')}
        response_stock = requests.get(url_stock, headers=APIKEY)
        data_stock = json.loads(response_stock.text)
        common_data_stock = []

        for i in range(len(data_stock)):
            check_data_stock = []
            check_data_stock.append(control_date_stock)

            for key, value in data_stock[i].items():

                check_data_stock.append(value)
            common_data_stock.append(check_data_stock)
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
                '''INSERT INTO database_stocksapi (pub_date, last_change_date,
                       warehouse_name,
                       supplier_article,
                       nm_id,
                       barcode,
                       quantity,
                       in_way_to_client,
                       in_way_from_client,
                       quantity_full,
                       category,
                       subject,
                       brand,
                       tech_size,
                       price,
                       discount,
                       is_supply,
                       is_realization,
                       sccode) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
                common_data_stock)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с PostgreSQL закрыто")
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('add_data_stock_api', add_data_stock_api, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')


@app.task
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

@app.task
def add_stock_data_site():
    try:
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
        PATH = 'celery_tasks/Аналитика МП.xlsx'
        URL = 'https://card.wb.ru/cards/detail?appType=0&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&dest=-2133464&nm='

        excel_data = pd.read_excel(PATH)
        data = pd.DataFrame(excel_data, columns=['Номенк WB', 'Арт'])
        nomenclatura_list = data['Номенк WB'].to_list()
        article_list = data['Арт'].to_list()

        article_dict = {}

        for i in range(len(nomenclatura_list)):
            article_dict[nomenclatura_list[i]] = article_list[i]

        iter_amount = len(article_dict.keys()) // 15

        data_for_database = []
        for k in range(iter_amount+1):
            start_point = k*15
            finish_point = (k+1)*15
            nom_info_list = list(article_dict.keys())[start_point:finish_point]

            helper = ''
            for i in nom_info_list:
                helper += str(i)+';'
            url = URL + str(helper)
            payload = {}
            headers = {}
            response = requests.request("GET", url, headers=headers, data=payload)

            data = json.loads(response.text)

            main_data = data['data']['products']

            for j in main_data:
                amount = 0
                pub_date = control_date
                seller_article = article_dict[j['id']]
                nomenclatura_wb = j['id']
                name = j['name']
                price_u = j['priceU']
                sale_price_u = j['salePriceU']
                sale = j['sale']
                basic_sale = 0
                basic_price_u = 0
                review_rating = j['reviewRating']
                feedbacks = j['feedbacks']
                promotions = j['promotions']

                for i in j['sizes'][0]['stocks']:
                    if i['wh'] not in wb_stock_id_name.keys():
                        warehouse = i['wh']
                    else:
                        warehouse = wb_stock_id_name[i['wh']]
                    quantity = i['qty']
                    amount += i["qty"]
                    inner_data_set = (pub_date,
                                      seller_article,
                                      nomenclatura_wb,
                                      warehouse,
                                      quantity,
                                      price_u,
                                      basic_sale,
                                      basic_price_u,
                                      sale,
                                      sale_price_u,
                                      name,
                                      promotions,
                                      review_rating,
                                      feedbacks
                                      )
                    data_for_database.append(inner_data_set)
                raw_data_for_database = (pub_date,
                                         seller_article,
                                         nomenclatura_wb,
                                         'Итого по складам',
                                         amount,
                                         price_u,
                                         basic_sale,
                                         basic_price_u,
                                         sale,
                                         sale_price_u,
                                         name,
                                         promotions,
                                         review_rating,
                                         feedbacks)
                data_for_database.append(raw_data_for_database)
                sleep(1)
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
                '''INSERT INTO database_stockssite (
                    pub_date,
                    seller_article,
                    nomenclatura_wb,
                    warehouse,
                    quantity,
                    price_u,
                    basic_sale,
                    basic_price_u,
                    sale,
                    sale_price_u,
                    name,
                    promotions,
                    review_rating,
                    feedbacks
                    ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
                data_for_database)
        except (Exception, Error) as error:
            print("Ошибка при работе с PostgreSQL", error)
        finally:
            if connection:
                cursor.close()
                connection.close()
                print("Соединение с PostgreSQL закрыто")
    except Exception as e:
        # обработка ошибки и отправка сообщения через бота
        message_text = error_message('add_stock_data_site', add_stock_data_site, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')


@app.task
def delivery_statistic():
    """Добавляет данные по поставкам в базу данных"""
    try:
        control_date_delivery = date.today() - timedelta(days=2)
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

@app.task
def orders_statistic():
    """Добавляет данные по заказам в базу данных"""
    try:
        control_date_order = date.today() - timedelta(days=2)
        url_order = f"https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={control_date_order}&flag=1"
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

@app.task
def sales_report_statistic():
    """Добавляет данные по отчету продаж"""
    try:
        start_date = date.today() - timedelta(days=61)
        finish_date = date.today() - timedelta(days=30)
        url_delivery = f"https://statistics-api.wildberries.ru/api/v1/supplier/reportDetailByPeriod?dateFrom={start_date}&dateTo={finish_date}"
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
        
                try:

                    connection = psycopg2.connect(user=os.getenv('POSTGRES_USER'),
                                      dbname=os.getenv('DB_NAME'),
                                      password=os.getenv('POSTGRES_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'))
                    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    # Курсор для выполнения операций с базой данных
                    cursor = connection.cursor()
                    #try:
                    cursor.execute("CREATE UNIQUE INDEX unique_rrd_id ON database_salesreportonSales (rrd_id)")
                    cursor.executemany(
                        '''INSERT INTO database_salesreportonSales (
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
                            ) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);''',
                        check_data_reports)
                    if connection:
                        cursor.close()
                        connection.close()
                        print("Соединение с PostgreSQL закрыто")
                except Exception as k:
                    #connection.rollback()
                    print("User with this email already exists")
        


    except Exception as e:
        #обработка ошибки и отправка сообщения через бота
        message_text = error_message('sales_report_statistic', sales_report_statistic, e)
        bot.send_message(chat_id=CHAT_ID, text=message_text, parse_mode='HTML')

# add_data_stock_api()
#add_data_sales()
# add_stock_data_site()
