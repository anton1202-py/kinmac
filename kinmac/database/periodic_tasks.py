from datetime import datetime, timedelta
import time
from api_requests.wb_requests import (
    get_check_storage_cost_report_status,
    get_create_storage_cost_report,
    get_storage_cost_report_data,
    wb_article_data_from_api,
)
from django.db import transaction
from celery_tasks.celery import app

from api_requests.ozon_requests import (
    ArticleDataRequest,
    OzonFrontApiRequests,
    OzonReportsApiRequest,
    OzonSalesRequest,
)
from kinmac.constants_file import (
    wb_headers,
    BRAND_LIST,
    bot,
    TELEGRAM_ADMIN_CHAT_ID,
    event_bot,
    actions_info_users_list,
)
from database.supplyment import (
    OzonSalesDataSave,
    get_article_commot_stock_from_front,
    get_price_info_from_ofissial_api,
    last_seller_discount_wb,
)
from database.service.ozon_service import (
    OzonFrontDataHandler,
    OzonReportsHandler,
    OzonSalesOrdersHandler,
    OzonWarehouseInfo,
)


from .models import (
    ArticlePriceStock,
    ArticleStorageCost,
    Articles,
    Company,
    Marketplace,
    MarketplaceCategory,
    MarketplaceChoices,
    OzonArticleStorageCost,
    OzonProduct,
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
    report_number = get_create_storage_cost_report(wb_headers, date, date)[
        "data"
    ]["taskId"]
    time.sleep(15)
    status = get_check_storage_cost_report_status(wb_headers, report_number)[
        "data"
    ]["status"]
    while status != "done":
        time.sleep(10)
        status = get_check_storage_cost_report_status(
            wb_headers, report_number
        )["data"]["status"]
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
            StorageCost.objects.update_or_create(
                defaults=defaults, **search_params
            )


@app.task
def article_storage_cost():
    """
    Записывает стоимость хранения товара за входящую дату на ВБ
    """

    date_start = (datetime.now() - timedelta(days=1)).date()
    date_end = (datetime.now() - timedelta(days=1)).date()
    report_number = get_create_storage_cost_report(
        wb_headers, date_start, date_end
    )["data"]["taskId"]
    time.sleep(20)
    status = get_check_storage_cost_report_status(wb_headers, report_number)[
        "data"
    ]["status"]
    while status != "done":
        time.sleep(10)
        status = get_check_storage_cost_report_status(
            wb_headers, report_number
        )["data"]["status"]
    costs_data = get_storage_cost_report_data(wb_headers, report_number)
    print(len(costs_data))
    for data in costs_data:
        try:
            article_obj = Articles.objects.filter(
                nomenclatura_wb=data["nmId"]
            ).first()
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
        except Exception:
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
    # Список артикулов у которых изменилась скидка продавца и стала больше 20%
    sender_list = {"articles_list": [], "discount": 0}
    articles_discount = last_seller_discount_wb()
    for article_obj in articles_data:
        seller_discount = 0
        price_without_seller_discount = 0
        spp = None
        price_with_seller_discount = None
        price_on_page = None
        total_quantity = None
        if article_obj in spp_page_price_data:
            price_on_page = spp_page_price_data[article_obj]["sale_price_u"]
            total_quantity = spp_page_price_data[article_obj]["total_quantity"]

        if article_obj in price_discount_data:
            seller_discount = price_discount_data[article_obj]["discount"]
            if article_obj in articles_discount:
                if (
                    seller_discount > 20
                    and seller_discount > articles_discount[article_obj]
                ):
                    if article_obj.brand in BRAND_LIST:
                        sender_list["articles_list"].append(
                            article_obj.common_article
                        )
                        sender_list["discount"] = seller_discount
            price_without_seller_discount = price_discount_data[article_obj][
                "price_without_discount"
            ]
            price_with_seller_discount = price_discount_data[article_obj][
                "seller_price_with_discount"
            ]

        if total_quantity and price_on_page and price_with_seller_discount:
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
                "common_stock": total_quantity,
                "price_in_page": price_on_page,
                "price_after_seller_disc": price_with_seller_discount,
                "price_before_seller_disc": price_without_seller_discount,
                "seller_disc": seller_discount,
                "spp": spp,
            }
            ArticlePriceStock.objects.update_or_create(
                article=article_obj,
                marketplace=Marketplace.objects.get(name="Wildberries"),
                date=datetime.now().date(),
                defaults=defaults,
            )
    if sender_list["articles_list"]:
        message = (
            f"Скидка продавца стала {sender_list['discount']}% "
            f"у артикулов {sender_list['articles_list']} "
        )
        for chat_id in actions_info_users_list:
            event_bot.send_message(chat_id=chat_id, text=str(message)[:4000])


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
            if product["sources"]:
                try:
                    marketing_price = float(product["marketing_price"])
                except Exception:
                    marketing_price = 0
                try:
                    min_price = float(product["min_price"])
                except Exception:
                    min_price = 0
                try:
                    old_price = float(product["old_price"])
                except Exception:
                    old_price = 0
                try:
                    price = float(product["price"])
                except Exception:
                    price = 0

                fbo_comission = None
                fbs_comission = None
                for data in product["commissions"]:
                    if data["sale_schema"] == "FBO":
                        fbo_comission = data["percent"]
                    if data["sale_schema"] == "FBS":
                        fbs_comission = data["percent"]
                if OzonProduct.objects.filter(
                    company=company, product_id=product["id"]
                ):
                    OzonProduct.objects.filter(
                        company=company, product_id=product["id"]
                    ).update(
                        seller_article=product["offer_id"],
                        barcode=product["barcodes"],
                        sku=product["sources"][0]["sku"],
                        name=product["name"],
                        description_category_id=product[
                            "description_category_id"
                        ],
                        type_id=product["type_id"],
                        images=product["images"],
                        marketing_price=marketing_price,
                        min_price=min_price,
                        old_price=old_price,
                        price=price,
                        volume_weight=product["volume_weight"],
                        fbo_comission=fbo_comission,
                        fbs_comission=fbs_comission,
                    )
                else:
                    OzonProduct(
                        company=company,
                        product_id=product["id"],
                        seller_article=product["offer_id"],
                        barcode=product["barcodes"],
                        sku=product["sources"][0]["sku"],
                        name=product["name"],
                        description_category_id=product[
                            "description_category_id"
                        ],
                        type_id=product["type_id"],
                        images=product["images"],
                        marketing_price=marketing_price,
                        min_price=min_price,
                        old_price=old_price,
                        price=price,
                        volume_weight=product["volume_weight"],
                        fbo_comission=fbo_comission,
                        fbs_comission=fbs_comission,
                    ).save()
        attributes_info = ozon_req.ozon_product_attributes(header)
        ozon_products_to_update = []
        for attribute in attributes_info:
            product = OzonProduct.objects.filter(
                company=company, product_id=attribute["id"]
            ).first()
            if product:
                # Обновляем атрибуты
                product.height = attribute.get("height", 0) / 10
                product.depth = attribute.get("depth", 0) / 10
                product.width = attribute.get("width", 0) / 10
                product.weight = attribute.get("weight", 0) / 1000
                ozon_products_to_update.append(product)

        # Выполняем одно обращение к базе данных для обновления всех записей
        if ozon_products_to_update:
            with transaction.atomic():
                OzonProduct.objects.bulk_update(
                    ozon_products_to_update,
                    ["height", "depth", "width", "weight"],
                )


@app.task
def ozon_get_realization_report() -> None:
    """
    Загружает ежемесячный отчет по продажам в базу данных.
    """
    sales_data_req = OzonSalesRequest()
    sales_data_saver = OzonSalesDataSave()

    nessesary_date = datetime.now() - timedelta(days=20)
    month_report = int(nessesary_date.strftime("%m"))
    year_report = int(nessesary_date.strftime("%Y"))

    for company in Company.objects.all():
        header = company.ozon_header
        report_info = sales_data_req.realization_report(
            header, month_report, year_report
        ).get("result", None)
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
    clusters = OzonWarehouseInfo()
    clusters.save_ozon_fbo_warehouse_stock()


@app.task
def clusters_ozon_info_update():
    """Обновляет информацию о кластерах ОЗОН"""
    clusters = OzonWarehouseInfo()
    clusters.save_ozon_clusters_warehouses_info()


@app.task
def get_ozon_fbo_fbs_orders():
    """Загружает информацию о заказах Озон (ежедневно)"""

    orders_req = OzonSalesRequest()
    handler = OzonSalesOrdersHandler()
    for company in Company.objects.all():
        header = company.ozon_header

        date_from = (
            (datetime.now() - timedelta(days=7)).date().strftime("%Y-%m-%d")
        )
        date_to = (
            (datetime.now() - timedelta(days=1)).date().strftime("%Y-%m-%d")
        )

        fbo_orders_data = orders_req.fbo_orders_req(
            header=header, date_from=date_from, date_to=date_to
        )
        if fbo_orders_data:
            handler.order_data_handler(
                company=company,
                raw_order_data=fbo_orders_data,
                order_type="fbo",
            )

        fbs_orders_data = orders_req.fbs_orders_req(
            header=header, date_from=date_from, date_to=date_to
        )["result"].get("postings")
        if fbs_orders_data:
            handler.order_data_handler(
                company=company,
                raw_order_data=fbs_orders_data,
                order_type="fbs",
            )


def generate_date_segments():
    # Текущая дата
    end_date = datetime.now()
    # Дата 365 дней назад
    start_date = end_date - timedelta(days=365)

    # Список для хранения отрезков
    date_segments = []

    # Переменная для отслеживания текущей даты в цикле
    current_date = end_date

    while current_date > start_date:
        # Определяем дату начала отрезка
        date_from = current_date - timedelta(days=20)

        # Если date_from меньше start_date, устанавливаем его на start_date
        if date_from < start_date:
            date_from = start_date

        # Добавляем отрезок в список
        date_segments.append(
            {
                "date_from": date_from.strftime("%Y-%m-%d"),
                "date_to": current_date.strftime("%Y-%m-%d"),
            }
        )

        # Обновляем текущую дату для следующего отрезка
        current_date = date_from

    return date_segments


@app.task
def ozon_get_transactions_info():
    """Загружает информацию о транзакциях Озон"""

    req = OzonReportsApiRequest()
    handler = OzonReportsHandler()

    companies = Company.objects.filter(ozon_token__isnull=False)
    date_today = datetime.now()
    date_from = (date_today - timedelta(days=10)).date()
    date_to = date_today.date()

    for company in companies:
        transactions_info = req.finance_transaction_list(
            header=company.ozon_header,
            date_from=date_from,
            date_to=date_to,
        )
        handler.transaction_handler(
            company=company,
            transactions_info=transactions_info,
            date_from=date_from,
            date_to=date_to,
        )


@app.task
def ozon_storage_cost():
    """Сохраняет затраты на хранение товаров Озон (ежедневно)"""

    req = OzonFrontApiRequests()
    handler = OzonFrontDataHandler()
    companies = Company.objects.filter(ozon_cookie_token__isnull=False)
    last_date = OzonArticleStorageCost.objects.order_by("date").last().date

    if last_date != datetime.now().date():
        delta_time = (datetime.now().date() - last_date).days

        for i in range(delta_time):

            for company in companies:
                check_date = (datetime.now() - timedelta(days=i)).strftime(
                    "%Y-%m-%d"
                )

                common_cost_info: dict = req.daily_storage_cost(
                    front_header=company.ozon_cookie_header,
                    check_date=check_date,
                )

                if common_cost_info:
                    cost_info = common_cost_info.get("items")
                    handler.storage_cost_to_db(
                        company=company,
                        cost_info=cost_info,
                        cost_date=check_date,
                    )


@app.task
def ozon_price_with_ozon_card():
    """Сохраняет цены товара с озон картой"""
    req = OzonFrontApiRequests()
    handler = OzonFrontDataHandler()
    companies = Company.objects.filter(ozon_cookie_token__isnull=False)
    for company in companies:
        common_price_info = []
        article_objs = OzonProduct.objects.filter(company=company)
        product_ids_raw = article_objs.values_list("product_id", flat=True)
        product_ids = []
        for j in product_ids_raw:
            product_ids.append(str(j))
        request_list = [
            product_ids[i : i + 100] for i in range(0, len(product_ids), 100)
        ]
        for req_product_ids in request_list:
            raw_price_info: list = req.page_prices_info(
                front_header=company.ozon_cookie_header,
                front_company_id=company.ozon_front_company_id,
                prodict_ids=req_product_ids,
            )
            if raw_price_info:
                price_info = raw_price_info.get("items")
                common_price_info += price_info

                handler.article_price_info_to_db(
                    company=company, price_info=price_info
                )
