import json
import time
from datetime import date, timedelta

import requests
from api_requests.common_func import api_retry_decorator

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


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


