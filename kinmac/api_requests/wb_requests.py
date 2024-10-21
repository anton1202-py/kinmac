import json
import time
from datetime import date, timedelta

import requests
from api_requests.common_func import api_retry_decorator

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


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
    url = 'https://suppliers-api.wildberries.ru/content/v2/get/cards/list'
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

    counter += 1
    if response.status_code == 200:
        all_data = json.loads(response.text)["cards"]
        check_amount = json.loads(response.text)['cursor']
        for data in all_data:
            common_data.append(data)
        if len(json.loads(response.text)["cards"]) == 100:
            # time.sleep(1)
            return wb_article_data_from_api(header,
                                            check_amount['updatedAt'], check_amount['nmID'], common_data, counter)
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


@api_retry_decorator
def get_stock_from_webpage_api(nom_id):
    """
    Остатки товаров на складах WB. Из неофициального АПИ
    """
    # time.sleep(61)
    url = f"https://card.wb.ru/cards/detail?appType=0&regions=80,38,4,64,83,33,68,70,69,30,86,75,40,1,66,110,22,31,48,71,114&dest=-2133464&nm={nom_id}"
    response = requests.request("GET", url)
    return response


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
@api_retry_decorator
def get_create_storage_cost_report(header, date_from, date_to):
    """
    Создаёт задание на генерацию отчёта. 
    Можно получить отчёт максимум за 8 дней. 
    Максимум 1 запрос в минуту
    """
    # time.sleep(61)
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage?dateFrom={date_from}&dateTo={date_to}"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_check_storage_cost_report_status(header, report_id):
    """
    Возвращает статус задания на генерацию. 
    Максимум 1 запрос в 5 секунд
    """
    # time.sleep(61)
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{report_id}/status"
    response = requests.request("GET", url, headers=header)
    return response


@api_retry_decorator
def get_storage_cost_report_data(header, report_id):
    """
    Возвращает отчёт по ID задания. 
    Максимум 1 запрос в минуту
    """
    url = f"https://seller-analytics-api.wildberries.ru/api/v1/paid_storage/tasks/{report_id}/download"
    response = requests.request("GET", url, headers=header)
    return response




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

# =========ЗАПРОС ПОЗИЦИИ АРТИКУЛА В ПОИСКЕ ========== #
@api_retry_decorator
def get_article_position(query, page=1, pvz=123585487):
    """
    Возвращает артикулы в поисковой выдаче по слову
    """
    time.sleep(5)
    url = f"https://search.wb.ru/exactmatch/ru/common/v7/search?ab_testing=false&appType=1&curr=rub&dest={pvz}&page={page}&query={query}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
    response = requests.request("GET", url)
    return response

# =========КОНЕЦ ЗАПРОС ПОЗИЦИИ АРТИКУЛА В ПОИСКЕ ========== #