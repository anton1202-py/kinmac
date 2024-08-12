import json
import time

import requests
from api_requests.common_func import api_retry_decorator

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot


# ========= ЗАПРОСЫ СТАТИТСТИКИ ========== #
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


