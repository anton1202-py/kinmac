import json
import random
import time
from datetime import date, datetime, timedelta

import requests
from api_requests.common_func import api_retry_decorator

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


def time_sleep_for_wb_request():
    """Выдает рандомное число выдержки до запроса через фронт ЛК продавца ВБ"""
    random_number = random.randint(15, 20)
    return random_number


def wb_article_data_from_api(header, update_date=None, mn_id=0, common_data=None, counter=0):
    """Получаем данные всех артикулов в ВБ"""
    if not common_data:
        common_data = []
    if update_date:
        cursor = {
            "limit": 100,
            "updatedAt": update_date,
            "nmID": mn_id
        }
    else:
        cursor = {
            "limit": 100,
            "nmID": mn_id
        }
    url = 'https://content-api.wildberries.ru/content/v2/get/cards/list'
    payload = json.dumps(
        {
            "settings": {
                "cursor": cursor,
                "filter": {
                    "withPhoto": -1
                }
            }
        }
    )
    response = requests.request(
        "POST", url, headers=header, data=payload)
    print(f'{response.status_code}, {counter}, {len(common_data)}')
    counter += 1
    if response.status_code == 200:
        all_data = json.loads(response.text)["cards"]
        check_amount = json.loads(response.text)['cursor']
        for data in all_data:
            common_data.append(data)
        if len(json.loads(response.text)["cards"]) == 100:
            # time.sleep(1)
            print('Перезапрашиваю')
            return wb_article_data_from_api(header,
                                            check_amount['updatedAt'], check_amount['nmID'], common_data, counter)
        print(f'Должен вернуть данные {len(common_data)}')
        return common_data
    elif response.status_code != 200 and counter <= 50:
        return wb_article_data_from_api(header, update_date, mn_id, common_data, counter)
    else:
        message = f'статус код {response.status_code} у получения инфы всех артикулов api_request.wb_article_data'
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message)


# ========= ЗАПРОСЫ СТАТИТСТИКИ ========== #
@api_retry_decorator
def get_statistic_stock_api(header, control_date_stock):
    """
    Остатки товаров на складах WB. 
    Данные обновляются раз в 30 минут.
    Сервис статистики не хранит историю остатков товаров, 
    поэтому получить данные о них можно только в режиме "на текущий момент".
    Максимум 1 запрос в минуту
    """
    # time.sleep(61)
    url = f"https://statistics-api.wildberries.ru/api/v1/supplier/stocks?dateFrom={control_date_stock}"
    response = requests.request("GET", url, headers=header)
    return response


# @api_retry_decorator
def get_stock_from_webpage_api(nom_id):
    """
    Остатки товаров на складах WB. Из неофициального АПИ
    """
    # time.sleep(61)
    url = f"https://card.wb.ru/cards/detail?appType=0&dest=-2133464&nm={nom_id}"
    response = requests.request("GET", url)
    print(response.status_code)
    return json.loads(response.text)


@api_retry_decorator
def get_statistic_sales_api(header, control_date):
    """
    Продажи и возвраты.
    Гарантируется хранение данных не более 90 дней от даты продажи.
    Данные обновляются раз в 30 минут.
    Для идентификации заказа следует использовать поле srid.
    1 строка = 1 продажа/возврат = 1 единица товара.
    Максимум 1 запрос в минуту
    """
    # time.sleep(61)
    url = f"https://statistics-api.wildberries.ru/api/v1/supplier/sales?dateFrom={control_date}&flag=1"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_statistic_delivery_api(header, control_date):
    """
    Поставки. 
    Максимум 1 запрос в минуту
    """
    # time.sleep(61)
    url = f"https://statistics-api.wildberries.ru/api/v1/supplier/incomes?dateFrom={control_date}"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_statistic_order_api(header, control_date):
    """
    Заказы.
    Гарантируется хранение данных не более 90 дней от даты заказа.
    Данные обновляются раз в 30 минут.
    Для идентификации заказа следует использовать поле srid.
    1 строка = 1 заказ = 1 единица товара.
    Максимум 1 запрос в минуту
    """
    # time.sleep(61)
    url = f"https://statistics-api.wildberries.ru/api/v1/supplier/orders?dateFrom={control_date}&flag=1"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_report_detail_by_period(header, date_from, date_to):
    """
    Детализация к еженедельному отчёту реализации. 
    В отчёте доступны данные за последние 3 месяца. 
    Максимум 1 запрос в минуту.
    Чтобы получить данные до 29 января, используйте URL c v1: https://statistics-api.wildberries.ru/api/v1/supplier/reportDetailByPeriod
    Если нет данных за указанный период, метод вернет null.
    Технический перерыв в работе метода: каждый понедельник с 3:00 до 16:00.
    """
    # time.sleep(61)
    url = f'https://statistics-api.wildberries.ru/api/v5/supplier/reportDetailByPeriod?dateFrom={date_from}&dateTo={date_to}'
    response = requests.request("GET", url, headers=header)
    return response

# ========== КОНЕЦ ЗАПРОСЫ СТАТИСТИКИ ========== #

# ========= ЗАПРОСЫ АНАЛИТИКИ ========== #


# @api_retry_decorator
def get_create_storage_cost_report(header, date_from, date_to):
    """
    Создаёт задание на генерацию отчёта. 
    Можно получить отчёт максимум за 8 дней. 
    Максимум 1 запрос в минуту
    """
    print('зашел в get_create_storage_cost_report. Ждем 40 сек',
          datetime.now().time())
    time.sleep(40)
    print('Закончили ждать 40 сек')
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage?dateFrom={date_from}&dateTo={date_to}"
    response = requests.request("GET", url, headers=header)
    print(response.status_code)
    return json.loads(response.text)


# @api_retry_decorator
def get_check_storage_cost_report_status(header, report_id):
    """
    Возвращает статус задания на генерацию. 
    Максимум 1 запрос в 5 секунд
    """
    print('get_check_storage_cost_report_status',
          datetime.now().time())
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{report_id}/status"
    response = requests.request("GET", url, headers=header)
    print(response.status_code)
    return json.loads(response.text)


# @api_retry_decorator
def get_storage_cost_report_data(header, report_id):
    """
    Возвращает отчёт по ID задания. 
    Максимум 1 запрос в минуту
    """
    print('get_storage_cost_report_data')
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{report_id}/download"
    response = requests.request("GET", url, headers=header)
    print(response.status_code)
    return json.loads(response.text)


# ========= ЗАПРОСЫ РЕКЛАМЫ ========== #
@api_retry_decorator
def get_adv_campaign_lists_data(header):
    """
    Метод позволяет получать списки кампаний, 
    сгруппированных по типу и статусу, с информацией о дате последнего изменения кампании.

    Допускается 5 запросов в секунду.
    """
    url = f"https://advert-api.wildberries.ru/adv/v1/promotion/count"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_adv_info(header, campaign_list):
    """
    Метод позволяет получать информацию о кампаниях по query параметрам, 
    либо по списку ID кампаний.
    Допускается 5 запросов в секунду.
    """
    url = f"https://advert-api.wildberries.ru/adv/v1/promotion/adverts"
    payload = json.dumps(campaign_list)
    response = requests.request("POST", url, headers=header, data=payload)
    return response


@api_retry_decorator
def get_campaign_statistic(header, campaign_list):
    """
    Возвращает статистику кампаний.
    Максимум 1 запрос в минуту.
    Данные вернутся для кампаний в статусе 7, 9 и 11.
    Важно. В запросе можно передавать либо параметр dates либо параметр interval, но не оба.
    Можно отправить запрос только с ID кампании. При этом вернутся данные за последние сутки,
    но не за весь период существования кампании.
    """
    url = f"https://advert-api.wildberries.ru/adv/v2/fullstats"
    payload = json.dumps(campaign_list)
    response = requests.request("POST", url, headers=header, data=payload)
    return response

# ========= КОНЕЦ ЗАПРОСЫ РЕКЛАМЫ ========== #

# ========= ЗАПРОС ПОЗИЦИИ АРТИКУЛА В ПОИСКЕ ========== #


@api_retry_decorator
def get_article_position(query, page=1, pvz=123585487):
    """
    Возвращает артикулы в поисковой выдаче по слову
    """
    time.sleep(3)
    url = f"https://search.wb.ru/exactmatch/ru/common/v7/search?ab_testing=false&appType=1&curr=rub&dest={pvz}&page={page}&query={query}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
    response = requests.request("GET", url)
    return response

# ========= КОНЕЦ ЗАПРОС ПОЗИЦИИ АРТИКУЛА В ПОИСКЕ ========== #


# ========= КОМИССИИ ========== #
def wb_comissions(header):
    """
    Достает комиссии всех присутствующих категорий

    Входящие переменные:
        TOKEN_WB - токен учетной записи ВБ
    """
    api_url = f"https://common-api.wildberries.ru/api/v1/tariffs/commission"

    response = requests.get(api_url, headers=header)
    if response.status_code == 200:
        data = response.json().get('report', [])
        return data
    else:
        message = f'Ошибка при вызовае метода https://common-api.wildberries.ru/api/v1/tariffs/commission: {response.status_code}. {response.text}'
        print(message)


def wb_logistic(wb_headers):
    """
    Достает затраты на логистику в зависимости от габаритов

    Входящие переменные:
        TOKEN_WB - токен учетной записи ВБ
    """
    today_date = datetime.today().strftime('%Y-%m-%d')
    api_url = f"https://common-api.wildberries.ru/api/v1/tariffs/box?date={today_date}"

    response = requests.get(api_url, headers=wb_headers)
    if response.status_code == 200:

        main_data = response.json().get('response', [])
        if main_data:
            data = main_data['data']
            return data
    else:
        message = f'Ошибка при вызовае метода https://common-api.wildberries.ru/api/v1/tariffs/box?date: {response.status_code}. {response.text}'
        print(message)


# =========== АКЦИИ ========== #
@api_retry_decorator
def wb_actions_first_list(header):
    """
    Возвращает список акций с датами и временем проведения
    Максимум 10 запросов за 6 секунд
    """
    time.sleep(1)
    start_date = datetime.now().strftime('%Y-%m-%d')
    finish_date = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions?allPromo=false&startDateTime={start_date}T00:00:00Z&endDateTime={finish_date}T23:59:59Z'
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def wb_action_details_info(header, action_ids_list):
    """
    Возвращает список акций с датами и временем проведения
    """
    time.sleep(1)
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/details?{action_ids_list}'
    response = requests.request("GET", url, headers=header)
    return response


# @api_retry_decorator
def wb_articles_in_action(header, action_number, limit=1000, offset=0, counter=0, article_adv_data=None):
    """
    Возвращает список товаров, подходящих для участия в акции.
    Неприменимо для автоакций
    """
    time.sleep(1)
    if not article_adv_data:
        article_adv_data = []
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/nomenclatures?promotionID={action_number}&inAction=false&limit={limit}&offset={offset}'
    response = requests.request("GET", url, headers=header)
    counter += 1
    if response.status_code == 200:
        articles_list = json.loads(response.text)['data']['nomenclatures']
        for data in articles_list:
            article_adv_data.append(data)
        if len(articles_list) == limit:
            offset = limit * counter
            return wb_articles_in_action(header, action_number, limit, offset, counter, article_adv_data)
        else:
            return article_adv_data
    else:
        return None


def add_wb_articles_to_action(header, action_number, wb_nom_list):
    """
    Создаёт загрузку товара в акцию.
    Состояние загрузки можно проверить с помощью отдельных методов.

    Неприменимо для автоакций
    """
    time.sleep(1)
    url = f'https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/upload'
    payload = json.dumps({
        "data": {
            "promotionID": action_number,
            "uploadNow": True,
            "nomenclatures": wb_nom_list
        }
    })
    response = requests.request("POST", url, headers=header, data=payload)
    return response


def wb_action_info_from_front(cookie_auth, date_from, date_to):
    """
    Возвращает список акций с датами и временем проведения
    """
    time.sleep(1)
    url = f'https://discounts-prices.wildberries.ru/ns/calendar-api/dp-calendar/suppliers/api/v2/promo/actions/list?allPromoActions=false&endDateTime={date_to}T20%3A59%3A59.999Z&limit=100&offset=0&startDateTime={date_from}T21%3A00%3A00.000Z'
    response = requests.request("GET", url, headers=cookie_auth)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        message = f'Не смог получить информацию по списку акций с фронта. Ошибка: {response.text}'
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                         text=message[:4000])


def create_excel_file_with_article_in_auto_actions(cookie_auth, period):
    """
    Запускает формировани Excel файла с артикулами из авто акций
    """
    time.sleep(time_sleep_for_wb_request())
    url = f'https://discounts-prices.wildberries.ru/ns/calendar-api/dp-calendar/suppliers/api/v1/excel/create'
    payload = json.dumps(
        {"periodID": period}
    )
    response = requests.request("POST", url, headers=cookie_auth, data=payload)
    time.sleep(time_sleep_for_wb_request())
    return response


def take_excel_file_data_in_auto_actions(cookie_auth, action_number, period):
    """
    Запускает формировани Excel файла с артикулами из авто акций
    """
    time.sleep(time_sleep_for_wb_request())
    url = f'https://discounts-prices.wildberries.ru/ns/calendar-api/dp-calendar/suppliers/api/v1/excel?periodID={period}'
    response = requests.request("GET", url, headers=cookie_auth)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        message = f'Не смог скачать excel файл для акции {action_number} - {period}. Ошибка: {response.text}'
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                         text=message[:4000])


# =========== КОНЕЦ АКЦИИ ========== #
