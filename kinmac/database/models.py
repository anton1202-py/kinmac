from datetime import datetime

from django.db import models
from django.urls import reverse


class Articles(models.Model):
    common_article = models.CharField(
        verbose_name='Артикул',
        max_length=50,
        unique=True,
        null=True
    )
    brend = models.CharField(
        verbose_name='Бренд',
        max_length=50,
        null=True,
    )
    barcode = models.CharField(
        verbose_name='Баркод',
        max_length=20,
        null=True,
    )
    nomenclatura_wb = models.CharField(
        verbose_name='Номенклатура WB',
        max_length=100,
        null=True,
    )
    nomenclatura_ozon = models.CharField(
        verbose_name='Номенклатура OZON',
        max_length=100,
        null=True,
    )
    predmet = models.CharField(
        verbose_name='Предмет',
        max_length=100,
        null=True,
    )
    size = models.CharField(
        verbose_name='Размер',
        max_length=50,
        null=True,
    )
    model = models.CharField(
        verbose_name='Модель',
        max_length=50,
        null=True,
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=100,
        null=True,
    )
    prime_cost = models.CharField(
        verbose_name='Себестоимость',
        max_length=100,
        null=True,
    )
    average_cost = models.CharField(
        verbose_name='Средняя себестоимость',
        max_length=100,
        null=True,
    )

    def __str__(self):
        return self.common_article

    def get_absolute_url(self):
        return f'/database/{self.id}'

    class Meta:
        verbose_name = 'Артикул'
        verbose_name_plural = 'Артикулы'


class CodingMarketplaces(models.Model):
    marketpalce = models.CharField(
        verbose_name='Название маркетплейса',
        max_length=15,
    )

    def __str__(self):
        return self.marketpalce

    class Meta:
        verbose_name = 'Код маркетплейса'
        verbose_name_plural = 'Коды маркетплейсов'


class CodingWbStock(models.Model):
    wb_stock = models.CharField(
        verbose_name='Название склада WB',
        max_length=40,
    )

    def __str__(self):
        return self.wb_stock

    class Meta:
        verbose_name = 'Название склада WB'
        verbose_name_plural = 'Название склада WB'


class StocksApi(models.Model):
    pub_date = models.DateField(
        verbose_name='Дата',
        null=True
    )
    last_change_date = models.DateTimeField(
        verbose_name='lastChangeDate',
        null=True
    )
    warehouse_name = models.CharField(
        verbose_name='warehouseName',
        max_length=50,
        null=True
    )
    supplier_article = models.CharField(
        verbose_name='supplierArticle',
        max_length=50,
    )
    nm_id = models.CharField(
        verbose_name='nmId',
        max_length=50,
        null=True
    )
    barcode = models.PositiveBigIntegerField(
        verbose_name='barcode',
        null=True
    )
    quantity = models.CharField(
        verbose_name='quantity',
        max_length=50,
        null=True
    )
    in_way_to_client = models.CharField(
        verbose_name='inWayToClient',
        max_length=50,
        null=True
    )
    in_way_from_client = models.CharField(
        verbose_name='inWayFromClient',
        max_length=50,
        null=True
    )
    quantity_full = models.CharField(
        verbose_name='quantityFull',
        max_length=50,
        null=True
    )
    category = models.CharField(
        verbose_name='category',
        max_length=50,
        null=True
    )
    subject = models.CharField(
        verbose_name='subject',
        max_length=50,
        null=True
    )
    brand = models.CharField(
        verbose_name='brand',
        max_length=50,
        null=True
    )
    tech_size = models.CharField(
        verbose_name='techSize',
        max_length=50,
        null=True
    )
    price = models.CharField(
        verbose_name='Price',
        max_length=50,
        null=True
    )
    discount = models.CharField(
        verbose_name='Discount',
        max_length=50,
        null=True
    )
    is_supply = models.CharField(
        verbose_name='isSupply',
        max_length=50,
        null=True
    )
    is_realization = models.CharField(
        verbose_name='isRealization',
        max_length=50,
        null=True
    )
    sccode = models.CharField(
        verbose_name='SCCode',
        max_length=50,
        null=True
    )

    class Meta:
        verbose_name = 'Остатки WB API'
        verbose_name_plural = 'Остатки WB API'


class StocksSite(models.Model):
    pub_date = models.DateTimeField(
        verbose_name='Дата',
        auto_now_add=True
    )
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=50,
        null=True
    )
    nomenclatura_wb = models.CharField(
        verbose_name='Номенклатура WB',
        max_length=50,
        null=True
    )
    warehouse = models.CharField(
        verbose_name='Название склада',
        max_length=150,
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество',
        null=True
    )
    price_u = models.PositiveIntegerField(
        verbose_name='priceU',
        null=True
    )
    basic_sale = models.PositiveIntegerField(
        verbose_name='basicSale',
        null=True
    )
    basic_price_u = models.PositiveIntegerField(
        verbose_name='basicPriceU',
        null=True
    )
    sale = models.PositiveIntegerField(
        verbose_name='Скидка',
        null=True
    )
    sale_price_u = models.PositiveIntegerField(
        verbose_name='salePriceU',
        null=True
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
        null=True
    )
    promotions = models.CharField(
        verbose_name='promotions',
        max_length=400,
        null=True
    )
    review_rating = models.FloatField(
        verbose_name='Рейтинг',
        null=True
    )
    feedbacks = models.PositiveIntegerField(
        verbose_name='Кол-во отзывов',
        null=True
    )

    def __str__(self):
        return self.seller_article, self.quantity

    class Meta:
        verbose_name = 'Склад с сайта'
        verbose_name_plural = 'Склад с сайта'


class Sales(models.Model):
    pub_date = models.DateTimeField(
        verbose_name='Дата',
    )
    sales_date = models.DateTimeField(
        verbose_name='Время продажи',
        null=True
    )
    last_change_date = models.DateTimeField(
        verbose_name='lastChangeDate',
        null=True
    )
    supplier_article = models.CharField(
        verbose_name='supplierArticle',
        max_length=50,
    )
    tech_size = models.CharField(
        verbose_name='techSize',
        max_length=50,
        null=True
    )
    barcode = models.PositiveBigIntegerField(
        verbose_name='barcode',
        null=True
    )
    total_price = models.CharField(
        verbose_name='totalPrice',
        max_length=50,
        null=True
    )
    discount_percent = models.CharField(
        verbose_name='discountPercent',
        max_length=50,
        null=True
    )
    is_supply = models.CharField(
        verbose_name='isSupply',
        max_length=50,
        null=True
    )
    is_realization = models.CharField(
        verbose_name='isRealization',
        max_length=50,
        null=True
    )
    promo_code_discount = models.CharField(
        verbose_name='promoCodeDiscount',
        max_length=50,
        null=True
    )
    warehouse_name = models.CharField(
        verbose_name='warehouseName',
        max_length=50,
        null=True
    )
    country_name = models.CharField(
        verbose_name='countryName',
        max_length=50,
        null=True
    )
    oblast_okrug_name = models.CharField(
        verbose_name='oblastOkrugName',
        max_length=50,
        null=True
    )
    region_name = models.CharField(
        verbose_name='regionName',
        max_length=50,
        null=True
    )
    income_id = models.CharField(
        verbose_name='incomeID',
        max_length=50,
        null=True
    )
    sale_id = models.CharField(
        verbose_name='saleID',
        max_length=50,
        null=True
    )
    odid = models.CharField(
        verbose_name='odid',
        max_length=50,
        null=True
    )
    spp = models.CharField(
        verbose_name='spp',
        max_length=50,
        null=True
    )
    for_pay = models.CharField(
        verbose_name='forPay',
        max_length=50,
        null=True
    )
    finished_price = models.CharField(
        verbose_name='finishedPrice',
        max_length=50,
        null=True
    )
    price_with_disc = models.CharField(
        verbose_name='priceWithDisc',
        max_length=50,
        null=True
    )
    nm_id = models.CharField(
        verbose_name='nmId',
        max_length=50,
        null=True
    )
    subject = models.CharField(
        verbose_name='subject',
        max_length=50,
        null=True
    )
    category = models.CharField(
        verbose_name='category',
        max_length=50,
        null=True
    )
    brand = models.CharField(
        verbose_name='brand',
        max_length=50,
        null=True
    )
    is_storno = models.CharField(
        verbose_name='IsStorno',
        max_length=50,
        null=True
    )
    g_number = models.CharField(
        verbose_name='gNumber',
        max_length=50,
        null=True
    )
    sticker = models.CharField(
        verbose_name='sticker',
        max_length=50,
        null=True
    )
    srid = models.CharField(
        verbose_name='srid',
        max_length=50,
        null=True
    )

    class Meta:
        verbose_name = 'Продажи'
        verbose_name_plural = 'Продажи'
