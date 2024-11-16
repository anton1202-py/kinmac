from datetime import datetime, timedelta
import time
from api_requests.wb_requests import get_check_storage_cost_report_status, get_create_storage_cost_report, get_storage_cost_report_data, wb_article_data_from_api
from celery_tasks.celery import app

from kinmac.constants_file import wb_headers


from .models import ArticleStorageCost, Articles, MarketplaceCategory, MarketplaceChoices, Platform, StorageCost


@app.task
def update_info_about_articles():
    common_data = wb_article_data_from_api(wb_headers)
    if common_data:
        for data in common_data:
            category_number = data['subjectID']
            category_name = data['subjectName']
            platform_obj, created = Platform.objects.get_or_create(
                platform_type=MarketplaceChoices.WILDBERRIES)
            category_obj, created = MarketplaceCategory.objects.get_or_create(
                platform=platform_obj,
                category_number=category_number,
                category_name=category_name
            )
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
                    name=data['title'],
                    category=category_obj,
                    width=data['dimensions']['width'],
                    height=data['dimensions']['height'],
                    length=data['dimensions']['length'],
                    weight=0
                )
            else:
                Articles(
                    nomenclatura_wb=data['nmID'],
                    common_article=data['vendorCode'],
                    brand=data['brand'],
                    barcode=data['sizes'][0]['skus'][0],
                    predmet=data['subjectName'],
                    size=data['sizes'][0]['techSize'],
                    name=data['title'],
                    category=category_obj,
                    width=data['dimensions']['width'],
                    height=data['dimensions']['height'],
                    length=data['dimensions']['length'],
                    weight=0
                ).save()


@app.task
def calculate_storage_cost() -> None:
    """
    Рассчитывает стоимость хранения товара за входящие даны на ВБ
    """
    date = datetime.now().date()
    article_storagecost = {}

    date = str(date)
    report_number = get_create_storage_cost_report(
        wb_headers, date, date)['data']['taskId']
    time.sleep(15)
    status = get_check_storage_cost_report_status(
        wb_headers, report_number)['data']['status']
    while status != 'done':
        time.sleep(10)
        status = get_check_storage_cost_report_status(
            wb_headers, report_number)['data']['status']
    costs_data = get_storage_cost_report_data(wb_headers, report_number)
    for data in costs_data:
        if data['nmId'] in article_storagecost:
            article_storagecost[data['nmId']] += data['warehousePrice']
        else:
            article_storagecost[data['nmId']] = data['warehousePrice']
    for article, amount in article_storagecost.items():
        if Articles.objects.filter(nomenclatura_wb=article).exists():
            article_obj = Articles.objects.get(nomenclatura_wb=article)
            defaults = {'storage_cost': amount}
            search_params = {'article': article_obj, 'start_date': date}
            StorageCost.objects.update_or_create(
                defaults=defaults, **search_params
            )


@app.task
def article_storage_cost():
    """
    Записывает стоимость хранения товара за входящую дату на ВБ
    """
    for i in range(1, 44):
        date_stat = (datetime.now() - timedelta(days=i)).date()
        date_stat = str(date_stat)
        n = i*8
        m = (i + 1)*8
        date_start = (datetime.now() - timedelta(days=m)).date()
        date_end = (datetime.now() - timedelta(days=n)).date()
        report_number = get_create_storage_cost_report(
            wb_headers, date_start, date_end)['data']['taskId']
        time.sleep(20)
        status = get_check_storage_cost_report_status(
            wb_headers, report_number)['data']['status']
        while status != 'done':
            time.sleep(10)
            status = get_check_storage_cost_report_status(
                wb_headers, report_number)['data']['status']
        costs_data = get_storage_cost_report_data(wb_headers, report_number)
        print(len(costs_data))
        for data in costs_data:
            if Articles.objects.filter(nomenclatura_wb=data['nmId']).exists():
                article_obj = Articles.objects.filter(
                    nomenclatura_wb=data['nmId']).first()
                ArticleStorageCost.objects.get_or_create(
                    article=article_obj,
                    date=data["date"],
                    warehouse=data["warehouse"],
                    office_id=data["officeId"],
                    gi_id=data["giId"],
                    log_warehouse_coef=data["logWarehouseCoef"],
                    warehouse_coef=data["warehouseCoef"],
                    chrt_id=data["chrtId"],
                    size=data["size"],
                    barcode=data["barcode"],
                    subject=data["subject"],
                    brand=data["brand"],
                    vendor_code=data["vendorCode"],
                    nm_id=data["nmId"],
                    volume=data["volume"],
                    calc_type=data["calcType"],
                    warehouse_price=data["warehousePrice"],
                    barcodes_count=data["barcodesCount"],
                    pallet_place_code=data["palletPlaceCode"],
                    pallet_count=data["palletCount"],
                    original_date=data["originalDate"],
                    loyalty_discount=data["loyaltyDiscount"],
                    tariffFix_date=data["tariffFixDate"],
                    tariff_lower_date=data["tariffLowerDate"]
                )
        print('загрузил', date_stat)
