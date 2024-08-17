from datetime import date, datetime, timedelta
from zipfile import ZipFile

import pandas as pd
from api_requests.wb_requests import get_report_detail_by_period
from database.models import SalesReportOnSales
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import (ExtractMonth, ExtractWeek, ExtractYear,
                                        TruncWeek)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, bot, wb_headers

from .models import Deliveries, Orders, Sales, StocksApi, StocksSite


#@sender_error_to_tg
def add_data_stock_from_api(data):
    """
    Записывает данные по остаткам взятые из АПИ в базу данных 
    """
    control_date_stock = date.today() - timedelta(days=1)
    if StocksApi.objects.filter(warehouse_name=data['warehouseName'],
                                supplier_article=data['supplierArticle'],
                                last_change_date=data['lastChangeDate'],
                                nm_id=data['nmId']).exists():
        StocksApi.objects.filter(warehouse_name=data['warehouseName'],
            supplier_article=data['supplierArticle'],
            last_change_date=data['lastChangeDate'],
            nm_id=data['nmId']).update(
                                    pub_date=control_date_stock,
                                    barcode=data['barcode'],
                                    quantity=data['quantity'],
                                    in_way_to_client=data['inWayToClient'],
                                    in_way_from_client=data['inWayFromClient'],
                                    quantity_full=data['quantityFull'],
                                    category=data['category'],
                                    subject=data['subject'],
                                    brand=data['brand'],
                                    tech_size=data['techSize'],
                                    price=data['Price'],
                                    discount=data['Discount'],
                                    is_supply=data['isSupply'],
                                    is_realization=data['isRealization'],
                                    sccode=data['SCCode']
                                )
    else:
        StocksApi(
            pub_date=control_date_stock,
            warehouse_name=data['warehouseName'],
            supplier_article=data['supplierArticle'],
            last_change_date=data['lastChangeDate'],
            nm_id=data['nmId'],
            barcode=data['barcode'],
            quantity=data['quantity'],
            in_way_to_client=data['inWayToClient'],
            in_way_from_client=data['inWayFromClient'],
            quantity_full=data['quantityFull'],
            category=data['category'],
            subject=data['subject'],
            brand=data['brand'],
            tech_size=data['techSize'],
            price=data['Price'],
            discount=data['Discount'],
            is_supply=data['isSupply'],
            is_realization=data['isRealization'],
            sccode=data['SCCode']
        ).save()


def add_data_stock_from_web_api(data):
    """
    Записывает данные по остаткам взятые из неофициального АПИ в базу данных 
    """
    control_date_stock = date.today() - timedelta(days=1)
    if StocksSite.objects.filter(pub_date=data['pub_date'],
                                nomenclatura_wb=data['nomenclatura_wb'],
                                warehouse=data['warehouse']
                                ).exists():
        StocksSite.objects.filter(pub_date=data['pub_date'],
            nomenclatura_wb=data['nomenclatura_wb'],
            warehouse=data['warehouse']).update(
                quantity=data['quantity'],
                price_u=data['price_u'],
                basic_sale=data['basic_sale'],
                basic_price_u=data['basic_price_u'],
                sale=data['sale'],
                sale_price_u=data['sale_price_u'],
                name=data['name'],
                promotions=data['promotions'],
                review_rating=data['review_rating'],
                feedbacks=data['feedbacks']
                                )
    else:
        StocksSite(
            pub_date=data['pub_date'],
            seller_article=data['seller_article'],
            nomenclatura_wb=data['nomenclatura_wb'],
            warehouse=data['warehouse'],
            quantity=data['quantity'],
            price_u=data['price_u'],
            basic_sale=data['basic_sale'],
            basic_price_u=data['basic_price_u'],
            sale=data['sale'],
            sale_price_u=data['sale_price_u'],
            name=data['name'],
            promotions=data['promotions'],
            review_rating=data['review_rating'],
            feedbacks=data['feedbacks']
        ).save()


def add_data_sales_to_db(data):
    """
    Записывает данные по продажам взятые из АПИ в базу данных 
    """
    control_date_sales = date.today() - timedelta(days=1)
    if Sales.objects.filter(sale_id=data['saleID'],
                            supplier_article=data['supplierArticle'],
                            nm_id=data['nmId']).exists():
       Sales.objects.filter(
            sale_id=data['saleID'],
            supplier_article=data['supplierArticle'],
            nm_id=data['nmId']).update(
                    pub_date=control_date_sales,
                    sales_date=data['date'],
                    last_change_date=data['lastChangeDate'],
                    tech_size=data['techSize'],
                    barcode=data['barcode'],
                    total_price=data['totalPrice'],
                    discount_percent=data['discountPercent'],
                    is_supply=data['isSupply'],
                    is_realization=data['isRealization'],
                    warehouse_name=data['warehouseName'],
                    country_name=data['countryName'],
                    oblast_okrug_name=data['oblastOkrugName'],
                    region_name=data['regionName'],
                    income_id=data['incomeID'],
                    paymen_sale_amount=data['paymentSaleAmount'],
                    spp=data['spp'],
                    for_pay=data['forPay'],
                    finished_price=data['finishedPrice'],
                    price_with_disc=data['priceWithDisc'],
                    subject=data['subject'],
                    category=data['category'],
                    brand=data['brand'],
                    order_type=data['orderType'],
                    g_number=data['gNumber'],
                    sticker=data['sticker'],
                    srid=data['srid']
                )
    else:
        Sales(
            pub_date=control_date_sales,
            sales_date=data['date'],
            last_change_date=data['lastChangeDate'],
            supplier_article=data['supplierArticle'],
            tech_size=data['techSize'],
            barcode=data['barcode'],
            total_price=data['totalPrice'],
            discount_percent=data['discountPercent'],
            is_supply=data['isSupply'],
            is_realization=data['isRealization'],
            warehouse_name=data['warehouseName'],
            country_name=data['countryName'],
            oblast_okrug_name=data['oblastOkrugName'],
            region_name=data['regionName'],
            income_id=data['incomeID'],
            paymen_sale_amount=data['paymentSaleAmount'],
            sale_id=data['saleID'],
            spp=data['spp'],
            for_pay=data['forPay'],
            finished_price=data['finishedPrice'],
            price_with_disc=data['priceWithDisc'],
            nm_id=data['nmId'],
            subject=data['subject'],
            category=data['category'],
            brand=data['brand'],
            order_type=data['orderType'],
            g_number=data['gNumber'],
            sticker=data['sticker'],
            srid=data['srid']
        ).save()


def add_data_stock_from_site_to_db(data):
    """
    Записывает данные по остаткам из неофициального АПИ в базу данных
    """
    control_date_sales = date.today() - timedelta(days=1)
    if Sales.objects.filter(sale_id=data['saleID'],
                            supplier_article=data['supplierArticle'],
                            nm_id=data['nmId']).exists():
       Sales.objects.filter(
            sale_id=data['saleID'],
            supplier_article=data['supplierArticle'],
            nm_id=data['nmId']).update(
                    pub_date=control_date_sales,
                    sales_date=data['date'],
                    last_change_date=data['lastChangeDate'],
                    tech_size=data['techSize'],
                    barcode=data['barcode'],
                    total_price=data['totalPrice'],
                    discount_percent=data['discountPercent'],
                    is_supply=data['isSupply'],
                    is_realization=data['isRealization'],
                    warehouse_name=data['warehouseName'],
                    country_name=data['countryName'],
                    oblast_okrug_name=data['oblastOkrugName'],
                    region_name=data['regionName'],
                    income_id=data['incomeID'],
                    paymen_sale_amount=data['paymentSaleAmount'],
                    spp=data['spp'],
                    for_pay=data['forPay'],
                    finished_price=data['finishedPrice'],
                    price_with_disc=data['priceWithDisc'],
                    subject=data['subject'],
                    category=data['category'],
                    brand=data['brand'],
                    order_type=data['orderType'],
                    g_number=data['gNumber'],
                    sticker=data['sticker'],
                    srid=data['srid']
                )
    else:
        Sales(
            pub_date=control_date_sales,
            sales_date=data['date'],
            last_change_date=data['lastChangeDate'],
            supplier_article=data['supplierArticle'],
            tech_size=data['techSize'],
            barcode=data['barcode'],
            total_price=data['totalPrice'],
            discount_percent=data['discountPercent'],
            is_supply=data['isSupply'],
            is_realization=data['isRealization'],
            warehouse_name=data['warehouseName'],
            country_name=data['countryName'],
            oblast_okrug_name=data['oblastOkrugName'],
            region_name=data['regionName'],
            income_id=data['incomeID'],
            paymen_sale_amount=data['paymentSaleAmount'],
            sale_id=data['saleID'],
            spp=data['spp'],
            for_pay=data['forPay'],
            finished_price=data['finishedPrice'],
            price_with_disc=data['priceWithDisc'],
            nm_id=data['nmId'],
            subject=data['subject'],
            category=data['category'],
            brand=data['brand'],
            order_type=data['orderType'],
            g_number=data['gNumber'],
            sticker=data['sticker'],
            srid=data['srid']
        ).save()


def add_data_delivery_to_db(data):
    """
    Записывает данные по поставкам из АПИ в базу данных
    """
    if Deliveries.objects.filter(income_id=data['incomeId'],
                            delivery_date=data['date'],
                            nmid=data['nmId'],
                            quantity=data['quantity'],
                            warehouse_name=data['warehouseName']
                            ).exists():
        Deliveries.objects.filter(
            income_id=data['incomeId'],
            delivery_date=data['date'],
            nmid=data['nmId'],
            quantity=data['quantity'],
            warehouse_name=data['warehouseName']
            ).update(
                number=data['number'],
                last_change_date=data['lastChangeDate'],
                supplier_article=data['supplierArticle'],
                tech_size=data['techSize'],
                barcode=data['barcode'],
                total_price=data['totalPrice'],
                date_close=data['dateClose'],
                status=data['status']
                )
    else:
        Deliveries(
            income_id=data['incomeId'],
            number=data['number'],
            delivery_date=data['date'],
            last_change_date=data['lastChangeDate'],
            supplier_article=data['supplierArticle'],
            tech_size=data['techSize'],
            barcode=data['barcode'],
            quantity=data['quantity'],
            total_price=data['totalPrice'],
            date_close=data['dateClose'],
            warehouse_name=data['warehouseName'],
            nmid=data['nmId'],
            status=data['status']
        ).save()


def add_data_orders_from_site_to_db(data):
    """
    Записывает данные по заказам из АПИ в базу данных
    """
    if Orders.objects.filter(order_date=data['date'],
                           nmid=data['nmId'],
                            g_number=data['gNumber'],
                            srid=data['srid']
                            ).exists():
        Orders.objects.filter(
            order_date=data['date'],
            nmid=data['nmId'],
            g_number=data['gNumber'],
            srid=data['srid']
            ).update(
                last_change_date=data['lastChangeDate'],
                warehouse_name=data['warehouseName'],
                country_name=data['countryName'],
                oblast_okrug_name=data['oblastOkrugName'],
                region_name=data['regionName'],
                supplier_article=data['supplierArticle'],
                barcode=data['barcode'],
                category=data['category'],
                subject=data['subject'],
                brand=data['brand'],
                tech_size=data['techSize'],
                income_id=data['incomeID'],
                is_supply=data['isSupply'],
                is_realization=data['isRealization'],
                total_price=data['totalPrice'],
                discount_percent=data['discountPercent'],
                spp=data['spp'],
                finish_price=data['finishedPrice'],
                price_with_disc=data['priceWithDisc'],
                is_cancel=data['isCancel'],
                cancel_date=data['cancelDate'],
                order_type=data['orderType'],
                sticker=data['sticker']
                )
    else:
        Orders(
            order_date=data['date'],
            last_change_date=data['lastChangeDate'],
            warehouse_name=data['warehouseName'],
            country_name=data['countryName'],
            oblast_okrug_name=data['oblastOkrugName'],
            region_name=data['regionName'],
            supplier_article=data['supplierArticle'],
            nmid=data['nmId'],
            barcode=data['barcode'],
            category=data['category'],
            subject=data['subject'],
            brand=data['brand'],
            tech_size=data['techSize'],
            income_id=data['incomeID'],
            is_supply=data['isSupply'],
            is_realization=data['isRealization'],
            total_price=data['totalPrice'],
            discount_percent=data['discountPercent'],
            spp=data['spp'],
            finish_price=data['finishedPrice'],
            price_with_disc=data['priceWithDisc'],
            is_cancel=data['isCancel'],
            cancel_date=data['cancelDate'],
            order_type=data['orderType'],
            sticker=data['sticker'],
            g_number=data['gNumber'],
            srid=data['srid']
        ).save()
