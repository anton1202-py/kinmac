from datetime import datetime, timedelta
import time
from api_requests.wb_requests import get_check_storage_cost_report_status, get_create_storage_cost_report, get_storage_cost_report_data, wb_article_data_from_api
from celery_tasks.celery import app

from kinmac.constants_file import BRAND_LIST, wb_headers

from .models import Articles, StorageCost


@app.task
def update_info_about_articles():
    common_data = wb_article_data_from_api(wb_headers)
    if common_data:
        for data in common_data:
            if Articles.objects.filter(
                nomenclatura_wb=data['nmID']
            ).exists():
                Articles.objects.filter(
                nomenclatura_wb=data['nmID']
            ).update(
                common_article=data['vendorCode'],
                brand=data['brand'],
                barcode=data['sizes'][0]['skus'][0],
                predmet=data['subjectName'],
                size=data['sizes'][0]['techSize'],
                name=data['title']
            )
            else:
                Articles(
                    nomenclatura_wb=data['nmID'],
                    common_article=data['vendorCode'],
                    brand=data['brand'],
                    barcode=data['sizes'][0]['skus'][0],
                    predmet=data['subjectName'],
                    size=data['sizes'][0]['techSize'],
                    name=data['title']
                ).save()


@app.task
def calculate_storage_cost() -> None:
    """
    Рассчитывает стоимость хранения товара за входящие даны на ВБ
    Входящие переменные
    date_start - дата начала периода хранения
    date_finish - дата завершения периода хранения

    Возвращает словарь типа {nm_id: summ}
    """
    date = datetime.now().date()
    print(date)
    article_storagecost = {}
    year = 2024

    # Начало года
    start_date = datetime(year, 1, 1)

    # Конец года
    end_date = datetime(year, 10, 7)

    # Список для хранения дат
    dates = []

    # Цикл для получения всех дат
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.date())  # Добавляем дату в список
        current_date += timedelta(days=1)   # Переходим к следующему дню

    # Выводим все даты
    for date in dates:
        date = str(date)
        print(date)
        report_number = get_create_storage_cost_report(wb_headers, date, date)['data']['taskId']
        time.sleep(5)
        status = get_check_storage_cost_report_status(wb_headers, report_number)['data']['status']
        while status != 'done':
            time.sleep(5)
            status = get_check_storage_cost_report_status(wb_headers, report_number)['data']['status']

        costs_data = get_storage_cost_report_data(wb_headers, report_number)
        for data in costs_data:
            if data['brand'] in BRAND_LIST: 
                if data['nmId'] in article_storagecost:
                    article_storagecost[data['nmId']] += data['warehousePrice']
                else:
                    article_storagecost[data['nmId']] = data['warehousePrice']

        for article, amount in article_storagecost.items():
            article_obj = Articles.objects.get(nomenclatura_wb=article)
            defaults={'storage_cost': amount}
            search_params = {'article': article_obj, 'start_date': date}
            
            StorageCost.objects.update_or_create(
                defaults=defaults, **search_params
            )

    