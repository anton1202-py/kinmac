from collections import defaultdict
from datetime import datetime, timedelta
import time
from api_requests.wb_requests import (
    get_check_storage_cost_report_status,
    get_create_storage_cost_report,
    get_storage_cost_report_data,
    wb_article_data_from_api,
)
from celery_tasks.celery import app

from api_requests.ozon_requests import ArticleDataRequest, OzonSalesRequest
from kinmac.constants_file import wb_headers
from database.supplyment import (
    OzonSalesDataSave,
    get_article_commot_stock_from_front,
    get_price_info_from_ofissial_api,
)
from database.service.ozon_service import OzonWarehouseInfo


from .models import (
    ArticlePriceStock,
    ArticleStorageCost,
    Articles,
    Company,
    MarketplaceCategory,
    MarketplaceChoices,
    Platform,
    StorageCost,
)


@app.task
def update_info_about_articles():
    common_data = wb_article_data_from_api(wb_headers)
    if common_data:
        for data in common_data:
            category_number = data["subjectID"]
            category_name = data["subjectName"]
            platform_obj, created = Platform.objects.get_or_create(
                platform_type=MarketplaceChoices.WILDBERRIES
            )
            category_obj, created = MarketplaceCategory.objects.get_or_create(
                platform=platform_obj,
                category_number=category_number,
                category_name=category_name,
            )
            if Articles.objects.filter(nomenclatura_wb=data["nmID"]).exists():

                Articles.objects.filter(nomenclatura_wb=data["nmID"]).update(
                    common_article=data["vendorCode"],
                    brand=data["brand"],
                    barcode=data["sizes"][0]["skus"][0],
                    predmet=data["subjectName"],
                    size=data["sizes"][0]["techSize"],
                    name=data["title"],
                    category=category_obj,
                    width=data["dimensions"]["width"],
                    height=data["dimensions"]["height"],
                    length=data["dimensions"]["length"],
                    weight=0,
                )
            else:
                Articles(
                    nomenclatura_wb=data["nmID"],
                    common_article=data["vendorCode"],
                    brand=data["brand"],
                    barcode=data["sizes"][0]["skus"][0],
                    predmet=data["subjectName"],
                    size=data["sizes"][0]["techSize"],
                    name=data["title"],
                    category=category_obj,
                    width=data["dimensions"]["width"],
                    height=data["dimensions"]["height"],
                    length=data["dimensions"]["length"],
                    weight=0,
                ).save()


@app.task
def calculate_storage_cost() -> None:
    """
    Рассчитывает стоимость хранения товара за входящие даны на ВБ
    """
    date = datetime.now().date()
    article_storagecost = {}

    date = str(date)
    report_number = get_create_storage_cost_report(wb_headers, date, date)["data"][
        "taskId"
    ]
    time.sleep(15)
    status = get_check_storage_cost_report_status(wb_headers, report_number)["data"][
        "status"
    ]
    while status != "done":
        time.sleep(10)
        status = get_check_storage_cost_report_status(wb_headers, report_number)[
            "data"
        ]["status"]
    costs_data = get_storage_cost_report_data(wb_headers, report_number)
    for data in costs_data:
        if data["nmId"] in article_storagecost:
            article_storagecost[data["nmId"]] += data["warehousePrice"]
        else:
            article_storagecost[data["nmId"]] = data["warehousePrice"]
    for article, amount in article_storagecost.items():
        if Articles.objects.filter(nomenclatura_wb=article).exists():
            article_obj = Articles.objects.get(nomenclatura_wb=article)
            defaults = {"storage_cost": amount}
            search_params = {"article": article_obj, "start_date": date}
            StorageCost.objects.update_or_create(defaults=defaults, **search_params)


@app.task
def article_storage_cost():
    """
    Записывает стоимость хранения товара за входящую дату на ВБ
    """

    date_start = (datetime.now() - timedelta(days=1)).date()
    date_end = (datetime.now() - timedelta(days=1)).date()
    report_number = get_create_storage_cost_report(wb_headers, date_start, date_end)[
        "data"
    ]["taskId"]
    time.sleep(20)
    status = get_check_storage_cost_report_status(wb_headers, report_number)["data"][
        "status"
    ]
    while status != "done":
        time.sleep(10)
        status = get_check_storage_cost_report_status(wb_headers, report_number)[
            "data"
        ]["status"]
    costs_data = get_storage_cost_report_data(wb_headers, report_number)
    print(len(costs_data))
    for data in costs_data:
        try:
            # if Articles.objects.filter(nomenclatura_wb=data['nmId']).exists():
            article_obj = Articles.objects.filter(nomenclatura_wb=data["nmId"]).first()
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
                tariff_lower_date=data["tariffLowerDate"],
            )
        except:
            print(f"{data} в бд")
    print("загрузил", date_end)


@app.task
def wb_article_price_stock_app_data() -> None:
    """
    Записывает данные в базу о СПП, остатке цене артикула.
    Для последующей выдачи в АПИ для гугл таблицы (для расчета Юнит экономики)
    """
    spp_page_price_data = get_article_commot_stock_from_front()
    price_discount_data = get_price_info_from_ofissial_api()

    articles_data = Articles.objects.all()

    for article_obj in articles_data:
        if article_obj in spp_page_price_data:
            price_on_page = spp_page_price_data[article_obj]["sale_price_u"]
            total_quantity = spp_page_price_data[article_obj]["total_quantity"]
        else:
            price_on_page = 0
            total_quantity = 0

        if article_obj in price_discount_data:
            seller_discount = price_discount_data[article_obj]["discount"]
            price_without_seller_discount = price_discount_data[article_obj][
                "price_without_discount"
            ]
            price_with_seller_discount = price_discount_data[article_obj][
                "seller_price_with_discount"
            ]
        else:
            seller_discount = 0
            price_without_seller_discount = 0
            price_with_seller_discount = 0
        spp = 0
        if price_with_seller_discount != 0:
            spp = int(
                (
                    1
                    - (
                        price_on_page
                        / price_without_seller_discount
                        / (1 - seller_discount / 100)
                    )
                )
                * 100
            )
        defaults = {
            "date": datetime.now().date(),
            "common_stock": total_quantity,
            "price_in_page": price_on_page,
            "price_after_seller_disc": price_with_seller_discount,
            "price_before_seller_disc": price_without_seller_discount,
            "seller_disc": seller_discount,
            "spp": spp,
        }
        ArticlePriceStock.objects.update_or_create(
            article=article_obj, defaults=defaults
        )


def split_list(input_list, chunk_size):
    """Разделяет список на подсписки заданного размера."""
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i : i + chunk_size]


@app.task
def ozon_update_article_date() -> None:
    """
    Обновляет данные по артикулам ОЗОН
    """
    ozon_req = ArticleDataRequest()
    for company in Company.objects.filter(ozon_token__isnull=False):
        header = company.ozon_header
        product_id_list = []
        product_ids = ozon_req.ozon_products_list(header)
        for product_id in product_ids:
            product_id_list.append(product_id.get("product_id"))
        chunk_size = 1000
        products_info = []
        # Разделяем список и отправляем запросы
        for chunk in split_list(product_id_list, chunk_size):
            products = ozon_req.ozon_product_info(header, chunk)["items"]
            products_info.extend(products)
        for product in products_info:
            if product["barcodes"]:
                if Articles.objects.filter(barcode=product["barcodes"][0]):
                    if product["sources"][0]["sku"]:
                        article_obj = Articles.objects.filter(
                            barcode=product["barcodes"][0]
                        ).first()
                elif Articles.objects.filter(common_article=product["offer_id"]):
                    article_obj = Articles.objects.filter(
                        common_article=product["offer_id"]
                    ).first()
                else:
                    if len(product["barcodes"]) > 1:
                        article_obj = Articles.objects.filter(
                            barcode=product["barcodes"][1]
                        ).first()

                if article_obj:
                    article_obj.ozon_product_id = product["id"]
                    article_obj.ozon_seller_article = product["offer_id"]
                    article_obj.ozon_sku = product["sources"][0]["sku"]
                    article_obj.ozon_barcode = product["barcodes"][0]
                    article_obj.save()


@app.task
def ozon_get_realization_report() -> None:
    """
    Загружает ежемесячный отчет по продажам в базу данных.
    """
    sales_data_req = OzonSalesRequest()
    sales_data_saver = OzonSalesDataSave()

    nessesary_date = datetime.now() - timedelta(days=20)
    month_report = int(nessesary_date.strftime("%m"))
    year_report = nessesary_date.strftime("%Y")
    for company in Company.objects.all():
        header = company.ozon_header
        report_info = sales_data_req.realization_report(
            header, month_report, year_report
        ).get("result")
        if report_info:
            report_data = report_info.get("header")
            report_obj = sales_data_saver.save_realization_report(
                company=company, report_data=report_data
            )

            articles_report_data = report_info.get("rows")
            for article_data in articles_report_data:
                if article_data:
                    sales_data_saver.save_article_in_realization_report(
                        report=report_obj, article_report_data=article_data
                    )


@app.task
def save_ozon_fbo_warehouses_balance():
    """Сохраняет остаток на ФБО складах ОЗОН"""
    print("Сохранение кластеров")
    clusters = OzonWarehouseInfo()
    clusters.save_ozon_clusters_warehouses_info()
    clusters.save_ozon_fbo_warehouse_stock()
