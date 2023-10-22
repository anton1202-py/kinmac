import json
import os
from datetime import date, datetime, timedelta
from time import sleep

import pandas as pd
import psycopg2
import requests
from celery_tasks.celery import app
from dotenv import load_dotenv
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()


@app.task
def add_data_stock_api():
    control_date_stock = date.today()
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


@app.task
def add_data_sales():
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
        check_data_sales.append(i['odid'])
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


@app.task
def add_stock_data_site():
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
    URL = 'https://card.wb.ru/cards/detail?regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&dest=-2133464&nm='

    excel_data = pd.read_excel(PATH)
    data = pd.DataFrame(excel_data, columns = ['Номенк WB', 'Арт'])
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
            basic_sale = j['extended']['basicSale']
            basic_price_u = j['extended']['basicPriceU']
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


#add_data_stock_api()
#add_data_sales()
#add_stock_data_site()

