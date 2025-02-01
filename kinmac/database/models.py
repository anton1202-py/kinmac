from django.db import models


class Company(models.Model):
    name = models.CharField(verbose_name="Юр. лицо")
    english_name = models.CharField(verbose_name="Название на английском")
    wb_token = models.TextField(verbose_name="Токен ВБ", blank=True, null=True)
    wb_cookie_token = models.TextField(
        verbose_name="Куки токен ВБ", blank=True, null=True
    )
    ozon_token = models.TextField(
        verbose_name="Токен ОЗОН", blank=True, null=True
    )
    yandex_token = models.TextField(
        verbose_name="Токен ЯНДЕКС", blank=True, null=True
    )
    ozon_client_id = models.CharField(
        verbose_name="Client ID Озон",
        max_length=30,
        null=True,
        blank=True,
    )
    ozon_perfomance_client_id = models.CharField(
        verbose_name="client_id для работы с рекламой ОЗОН",
        max_length=255,
        null=True,
        blank=True,
    )
    ozon_perfomance_client_secret = models.TextField(
        verbose_name="client_secret для работы с рекламой ОЗОН",
        null=True,
        blank=True,
    )

    @property
    def wb_header(self):
        return {
            "Content-Type": "application/json",
            "Authorization": self.wb_token,
        }

    @property
    def wb_cookie_header(self):
        USER_AGENT = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 YaBrowser/24.10.0.0 "
            "Safari/537.36"
        )
        return {
            "authorizev3": "",
            "baggage": "",
            "cookie": self.wb_cookie_token,
            "sentry-trace": "",
            "user-agent": USER_AGENT,
            "Content-Type": "application/json",
        }

    @property
    def ozon_header(self):
        return {
            "Api-Key": self.ozon_token,
            "Content-Type": "application/json",
            "Client-Id": self.ozon_client_id,
        }

    @property
    def ozon_perfomance_header(self):
        return {
            "client_id": self.ozon_perfomance_client_id,
            "client_secret": self.ozon_perfomance_client_secret,
            "grant_type": "client_credentials",
        }

    @property
    def yandex_header(self):
        return {
            "Authorization": self.yandex_token,
        }

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компания"


class MarketplaceChoices(models.IntegerChoices):
    WILDBERRIES = 1, "Wildberries"
    OZON = 2, "OZON"
    YANDEX_MARKET = 3, "Яндекс Маркет"
    MEGA_MARKET = 4, "МегаМаркет"
    MOY_SKLAD = 5, "Мой склад"


class Platform(models.Model):
    """Платформа, на которой находятся товары"""

    name = models.CharField(
        max_length=100, null=False, verbose_name="Название"
    )

    platform_type = models.IntegerField(
        choices=MarketplaceChoices.choices,
        default=MarketplaceChoices.WILDBERRIES,
        null=False,
        blank=False,
        verbose_name="Платформа",
    )


class MarketplaceCategory(models.Model):
    """Описывает категорию товара на Маркетплейсе."""

    platform = models.ForeignKey(
        Platform,
        related_name="mcategory_plaform",
        on_delete=models.CASCADE,
        verbose_name="Платформа",
    )
    category_number = models.IntegerField(
        verbose_name="Номер категории",
        null=True,
        blank=True,
    )
    category_name = models.CharField(
        max_length=255,
        verbose_name="Название категории",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Категория на Маркетплейсе"
        verbose_name_plural = "Категория на Маркетплейсе"


class Articles(models.Model):
    common_article = models.CharField(
        verbose_name="Артикул", max_length=300, unique=True, null=True
    )
    brand = models.CharField(
        verbose_name="Бренд",
        max_length=300,
        null=True,
    )
    barcode = models.CharField(
        verbose_name="Баркод",
        max_length=20,
        null=True,
    )
    nomenclatura_wb = models.CharField(
        verbose_name="Номенклатура WB",
        max_length=100,
        null=True,
    )
    ozon_product_id = models.BigIntegerField(
        verbose_name="Product ID OZON",
        null=True,
    )
    ozon_seller_article = models.CharField(
        verbose_name="Product ID OZON",
        max_length=255,
        null=True,
    )
    ozon_sku = models.BigIntegerField(
        verbose_name="OZON SKU",
        null=True,
    )
    ozon_barcode = models.CharField(
        verbose_name="Баркод",
        max_length=255,
        null=True,
    )
    predmet = models.CharField(
        verbose_name="Предмет",
        max_length=100,
        null=True,
    )
    size = models.CharField(
        verbose_name="Размер",
        max_length=300,
        null=True,
    )
    model = models.CharField(
        verbose_name="Модель",
        max_length=50,
        null=True,
    )
    color = models.CharField(
        verbose_name="Цвет",
        max_length=100,
        null=True,
    )
    prime_cost = models.CharField(
        verbose_name="Себестоимость",
        max_length=100,
        null=True,
    )
    average_cost = models.CharField(
        verbose_name="Средняя себестоимость",
        max_length=100,
        null=True,
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=300,
        null=True,
    )
    width = models.IntegerField(verbose_name="Ширина", null=True, blank=True)
    height = models.IntegerField(verbose_name="Высота", null=True, blank=True)
    length = models.IntegerField(verbose_name="Длина", null=True, blank=True)
    weight = models.FloatField(verbose_name="Вес", null=True, blank=True)
    category = models.ForeignKey(
        MarketplaceCategory,
        related_name="mp_category",
        on_delete=models.CASCADE,
        verbose_name="Категория товара",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.common_article

    def get_absolute_url(self):
        return f"/database/{self.id}"

    class Meta:
        verbose_name = "Артикул"
        verbose_name_plural = "Артикулы"


class OzonProduct(models.Model):
    """Описывает товары на Озоне (без привязки к ВБ)"""

    company = models.ForeignKey(
        Company,
        verbose_name="Компания",
        related_name="ozon_product",
        on_delete=models.CASCADE,
    )
    product_id = models.BigIntegerField(
        verbose_name="Product ID OZON",
    )
    seller_article = models.CharField(
        verbose_name="Product ID OZON",
        max_length=255,
        null=True,
    )
    barcode = models.JSONField(
        verbose_name="Баркод",
        null=True,
    )
    sku = models.BigIntegerField(
        verbose_name="OZON SKU",
        null=True,
    )
    name = models.CharField(
        verbose_name="Название",
        max_length=300,
        null=True,
    )
    description_category_id: int = models.BigIntegerField(
        verbose_name="ID категории",
        null=True,
    )
    type_id = models.IntegerField(
        verbose_name="Идентификатор типа товара.",
        null=True,
    )
    created_at = models.DateTimeField(
        verbose_name="Дата и время создания товара.",
        null=True,
    )
    images = models.JSONField(
        verbose_name="Массив ссылок на изображения.",
        null=True,
    )
    marketing_price = models.CharField(
        verbose_name=(
            "Цена на товар с учётом всех акций. "
            "Это значение будет указано на витрине Ozon."
        ),
        max_length=20,
        null=True,
    )
    min_price = models.CharField(
        verbose_name="Минимальная цена товара после применения акций.",
        max_length=50,
        null=True,
    )
    old_price = models.CharField(
        verbose_name=(
            "Цена до учёта скидок. "
            "На карточке товара отображается зачёркнутой."
        ),
        max_length=50,
        null=True,
    )
    price = models.CharField(
        verbose_name=(
            "Цена товара с учётом скидок."
            "Это значение показывается на карточке товара."
        ),
        max_length=50,
        null=True,
    )
    volume_weight = models.FloatField(
        verbose_name="Объёмный вес товара.", null=True
    )
    height = models.FloatField(verbose_name="Высота упаковки, см", null=True)
    depth = models.FloatField(verbose_name="Глубина упаковки, см", null=True)
    width = models.FloatField(verbose_name="Ширина упаковки, см", null=True)
    weight = models.FloatField(verbose_name="Вес уваковки, кг", null=True)

    fbo_comission = models.FloatField(verbose_name="Комиссия ФБО", null=True)
    fbs_comission = models.FloatField(verbose_name="Комиссия ФБС", null=True)


class Marketplace(models.Model):
    name = models.CharField(
        verbose_name="Название маркетплейса",
        max_length=15,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Код маркетплейса"
        verbose_name_plural = "Коды маркетплейсов"


class CostPrice(models.Model):
    """Себестоимость товаров (вбивается вручную)"""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="costprice_article",
        blank=True,
        null=True,
    )
    costprice_date = models.DateTimeField(
        verbose_name="Дата себестоимости",
        null=True,
        blank=True,
    )
    costprice = models.FloatField(
        verbose_name="Себестоимость артикула",
        null=True,
        blank=True,
    )
    ff_cost = models.FloatField(
        verbose_name="Затраты на Фулфилмент", default=125
    )
    ff_cost_date = models.DateTimeField(
        verbose_name="Дата обновления затрат на ФФ",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Себестоимость"
        verbose_name_plural = "Себестоимость"


class CodingWbStock(models.Model):
    wb_stock = models.CharField(
        verbose_name="Название склада WB",
        max_length=40,
    )

    def __str__(self):
        return self.wb_stock

    class Meta:
        verbose_name = "Название склада WB"
        verbose_name_plural = "Название склада WB"


class StocksApi(models.Model):
    pub_date = models.DateField(verbose_name="Дата", null=True)
    last_change_date = models.DateTimeField(
        verbose_name="lastChangeDate", null=True
    )
    warehouse_name = models.CharField(
        verbose_name="warehouseName", max_length=50, null=True
    )
    supplier_article = models.CharField(
        verbose_name="supplierArticle",
        max_length=50,
    )
    nm_id = models.CharField(verbose_name="nmId", max_length=50, null=True)
    barcode = models.PositiveBigIntegerField(verbose_name="barcode", null=True)
    quantity = models.CharField(
        verbose_name="quantity", max_length=50, null=True
    )
    in_way_to_client = models.CharField(
        verbose_name="inWayToClient", max_length=50, null=True
    )
    in_way_from_client = models.CharField(
        verbose_name="inWayFromClient", max_length=50, null=True
    )
    quantity_full = models.CharField(
        verbose_name="quantityFull", max_length=50, null=True
    )
    category = models.CharField(
        verbose_name="category", max_length=50, null=True
    )
    subject = models.CharField(
        verbose_name="subject", max_length=50, null=True
    )
    brand = models.CharField(verbose_name="brand", max_length=50, null=True)
    tech_size = models.CharField(
        verbose_name="techSize", max_length=50, null=True
    )
    price = models.CharField(verbose_name="Price", max_length=50, null=True)
    discount = models.CharField(
        verbose_name="Discount", max_length=50, null=True
    )
    is_supply = models.CharField(
        verbose_name="isSupply", max_length=50, null=True
    )
    is_realization = models.CharField(
        verbose_name="isRealization", max_length=50, null=True
    )
    sccode = models.CharField(verbose_name="SCCode", max_length=50, null=True)

    class Meta:
        verbose_name = "Остатки WB API"
        verbose_name_plural = "Остатки WB API"


class StocksSite(models.Model):
    pub_date = models.DateTimeField(verbose_name="Дата", auto_now_add=True)
    seller_article = models.CharField(
        verbose_name="Артикул продавца", max_length=50, null=True
    )
    nomenclatura_wb = models.CharField(
        verbose_name="Номенклатура WB", max_length=50, null=True
    )
    warehouse = models.CharField(
        verbose_name="Название склада",
        max_length=150,
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество", null=True
    )
    price_u = models.PositiveIntegerField(verbose_name="priceU", null=True)
    basic_sale = models.PositiveIntegerField(
        verbose_name="basicSale", null=True
    )
    basic_price_u = models.PositiveIntegerField(
        verbose_name="basicPriceU", null=True
    )
    sale = models.PositiveIntegerField(verbose_name="Скидка", null=True)
    sale_price_u = models.PositiveIntegerField(
        verbose_name="salePriceU", null=True
    )
    name = models.CharField(verbose_name="Название", max_length=200, null=True)
    promotions = models.CharField(
        verbose_name="promotions", max_length=400, null=True
    )
    review_rating = models.FloatField(verbose_name="Рейтинг", null=True)
    feedbacks = models.PositiveIntegerField(
        verbose_name="Кол-во отзывов", null=True
    )

    def __str__(self):
        return self.seller_article, self.quantity

    class Meta:
        verbose_name = "Склад с сайта"
        verbose_name_plural = "Склад с сайта"


class Sales(models.Model):
    pub_date = models.DateTimeField(
        verbose_name="Дата",
    )
    sales_date = models.DateTimeField(verbose_name="Время продажи", null=True)
    last_change_date = models.DateTimeField(
        verbose_name="lastChangeDate", null=True
    )
    supplier_article = models.CharField(
        verbose_name="supplierArticle",
        max_length=50,
    )
    tech_size = models.CharField(
        verbose_name="techSize", max_length=50, null=True
    )
    barcode = models.PositiveBigIntegerField(verbose_name="barcode", null=True)
    total_price = models.CharField(
        verbose_name="totalPrice", max_length=50, null=True
    )
    discount_percent = models.CharField(
        verbose_name="discountPercent", max_length=50, null=True
    )
    is_supply = models.CharField(
        verbose_name="isSupply", max_length=50, null=True
    )
    is_realization = models.CharField(
        verbose_name="isRealization", max_length=50, null=True
    )
    promo_code_discount = models.CharField(
        verbose_name="promoCodeDiscount", max_length=50, null=True
    )
    warehouse_name = models.CharField(
        verbose_name="warehouseName", max_length=50, null=True
    )
    country_name = models.CharField(
        verbose_name="countryName", max_length=50, null=True
    )
    oblast_okrug_name = models.CharField(
        verbose_name="oblastOkrugName", max_length=50, null=True
    )
    order_type = models.CharField(
        verbose_name="oblastOkrugName", max_length=100, null=True, blank=True
    )
    region_name = models.CharField(
        verbose_name="regionName", max_length=50, null=True
    )
    income_id = models.CharField(
        verbose_name="incomeID", max_length=50, null=True
    )
    sale_id = models.CharField(verbose_name="saleID", max_length=50, null=True)
    odid = models.CharField(
        verbose_name="odid", max_length=50, null=True, blank=True
    )
    spp = models.CharField(verbose_name="spp", max_length=50, null=True)
    for_pay = models.CharField(verbose_name="forPay", max_length=50, null=True)
    finished_price = models.CharField(
        verbose_name="finishedPrice", max_length=50, null=True
    )
    price_with_disc = models.CharField(
        verbose_name="priceWithDisc", max_length=50, null=True
    )
    nm_id = models.CharField(verbose_name="nmId", max_length=50, null=True)
    subject = models.CharField(
        verbose_name="subject", max_length=50, null=True
    )
    category = models.CharField(
        verbose_name="category", max_length=50, null=True
    )
    brand = models.CharField(verbose_name="brand", max_length=50, null=True)
    paymen_sale_amount = models.IntegerField(
        verbose_name="Оплачено с WB Кошелька",
        blank=True,
        null=True,
    )
    is_storno = models.CharField(
        verbose_name="IsStorno", max_length=50, null=True, blank=True
    )
    g_number = models.CharField(
        verbose_name="gNumber", max_length=50, null=True
    )
    sticker = models.CharField(
        verbose_name="sticker", max_length=50, null=True
    )
    srid = models.CharField(verbose_name="srid", max_length=50, null=True)

    class Meta:
        verbose_name = "Продажи"
        verbose_name_plural = "Продажи"


class Deliveries(models.Model):
    """Описывает таблицу поставок"""

    income_id = models.CharField(
        verbose_name="ID поставки",
        max_length=15,
        null=True,
    )
    number = models.CharField(
        verbose_name="Номер УПД",
        max_length=15,
        null=True,
        blank=True,
    )
    delivery_date = models.DateTimeField(
        verbose_name="Дата поставки",
        null=True,
    )
    last_change_date = models.DateTimeField(
        verbose_name="Дата обновления информации в сервисе",
        null=True,
    )
    supplier_article = models.CharField(
        verbose_name="Артикул продавца",
        max_length=50,
    )
    tech_size = models.CharField(
        verbose_name="Размер товара",
        max_length=10,
        null=True,
    )
    barcode = models.PositiveBigIntegerField(
        verbose_name="Баркод",
        null=True,
    )
    quantity = models.IntegerField(
        verbose_name="Количество",
        null=True,
    )
    total_price = models.CharField(
        verbose_name="Цена из УПД",
        max_length=50,
        null=True,
    )
    date_close = models.DateTimeField(
        verbose_name="Дата принятия (закрытия) в WB",
        null=True,
    )
    warehouse_name = models.CharField(
        verbose_name="Название склада",
        max_length=50,
        null=True,
    )
    nmid = models.CharField(
        verbose_name="Артикул WB",
        max_length=50,
        null=True,
    )
    status = models.CharField(
        verbose_name="Текущий статус поставки",
        max_length=50,
        null=True,
    )

    class Meta:
        verbose_name = "Поставки"
        verbose_name_plural = "Поставки"


class Orders(models.Model):
    """Описывает таблицу заказов"""

    order_date = models.DateTimeField(
        verbose_name="Дата и время заказа",
        null=True,
    )
    last_change_date = models.DateTimeField(
        verbose_name="Дата и время обновления информации в сервисе",
        null=True,
    )
    warehouse_name = models.CharField(
        verbose_name="Склад отгрузки",
        max_length=50,
        null=True,
    )
    country_name = models.CharField(
        verbose_name="Страна",
        max_length=100,
        null=True,
    )
    oblast_okrug_name = models.CharField(
        verbose_name="Округ",
        max_length=200,
        null=True,
    )
    region_name = models.CharField(
        verbose_name="Регион",
        max_length=100,
        null=True,
    )
    supplier_article = models.CharField(
        verbose_name="Артикул продавца",
        max_length=75,
    )
    nmid = models.IntegerField(
        verbose_name="Артикул WB",
        null=True,
    )
    barcode = models.CharField(
        verbose_name="Баркод",
        max_length=30,
        null=True,
    )
    category = models.CharField(
        verbose_name="Категория",
        max_length=50,
        null=True,
    )
    subject = models.CharField(
        verbose_name="Предмет",
        max_length=50,
        null=True,
    )
    brand = models.CharField(
        verbose_name="Бренд",
        max_length=50,
        null=True,
    )
    tech_size = models.CharField(
        verbose_name="Размер товара",
        max_length=30,
        null=True,
    )
    income_id = models.IntegerField(
        verbose_name="Номер поставки",
        null=True,
    )
    is_supply = models.BooleanField(
        verbose_name="Договор поставки",
        null=True,
    )
    is_realization = models.BooleanField(
        verbose_name="Договор реализации",
        null=True,
    )
    total_price = models.FloatField(
        verbose_name="Цена без скидок",
        null=True,
    )
    discount_percent = models.SmallIntegerField(
        verbose_name="Скидка продавца",
        null=True,
    )
    spp = models.FloatField(
        verbose_name="Скидка постоянного покупателя",
        null=True,
    )
    finish_price = models.FloatField(
        verbose_name="Фактическая цена с учетом всех скидок",
        null=True,
    )
    # Цена со скидкой продавца (= totalPrice * (1 - discountPercent/100))
    price_with_disc = models.FloatField(
        verbose_name="Цена со скидкой продавца",
        null=True,
    )
    is_cancel = models.BooleanField(
        verbose_name="Отмена заказа. true - заказ отменен",
        null=True,
    )
    cancel_date = models.DateTimeField(
        verbose_name="Дата и время отмены заказа",
        null=True,
    )
    order_type = models.CharField(
        verbose_name="Тип заказа",
        max_length=80,
        null=True,
    )
    sticker = models.CharField(
        verbose_name="Идентификатор стикера",
        max_length=80,
        null=True,
    )
    g_number = models.CharField(
        verbose_name="Номер заказа",
        max_length=50,
        null=True,
    )
    srid = models.CharField(
        verbose_name="Уникальный идентификатор заказа",
        max_length=80,
        null=True,
    )

    class Meta:
        verbose_name = "Заказы"
        verbose_name_plural = "Заказы"


class SalesReportOnSales(models.Model):
    """Отчет о продажах по реализации"""

    date_writing = models.DateTimeField(
        verbose_name="Дата записи в базу",
        auto_now=True,
    )
    realizationreport_id = models.BigIntegerField(
        verbose_name="Номер отчета",
        null=True,
        blank=True,
    )
    date_from = models.DateTimeField(
        verbose_name="Дата начала отчётного периода",
        null=True,
        blank=True,
    )
    date_to = models.DateTimeField(
        verbose_name="Дата конца отчётного периода",
        null=True,
        blank=True,
    )
    create_dt = models.DateTimeField(
        verbose_name="Дата формирования отчёта",
        null=True,
        blank=True,
    )
    currency_name = models.CharField(
        verbose_name="Валюта отчёта",
        max_length=300,
        null=True,
        blank=True,
    )
    suppliercontract_code = models.CharField(
        verbose_name="Договор",
        max_length=300,
        null=True,
        blank=True,
    )
    rrd_id = models.BigIntegerField(
        verbose_name="Номер строки",
        null=True,
        blank=True,
    )
    gi_id = models.BigIntegerField(
        verbose_name="Номер поставки",
        null=True,
        blank=True,
    )
    subject_name = models.CharField(
        verbose_name="Предмет",
        max_length=300,
        null=True,
        blank=True,
    )
    nm_id = models.IntegerField(
        verbose_name="Артикул WB",
        null=True,
        blank=True,
    )
    brand_name = models.CharField(
        verbose_name="Бренд",
        max_length=300,
        null=True,
        blank=True,
    )
    sa_name = models.CharField(
        verbose_name="Артикул продавца",
        max_length=300,
        null=True,
        blank=True,
    )
    ts_name = models.CharField(
        verbose_name="Размер",
        max_length=300,
        null=True,
        blank=True,
    )
    barcode = models.CharField(
        verbose_name="Баркод",
        max_length=20,
        null=True,
        blank=True,
    )
    doc_type_name = models.CharField(
        verbose_name="Тип документа",
        max_length=300,
        null=True,
        blank=True,
    )
    quantity = models.BigIntegerField(
        verbose_name="Количество",
        null=True,
        blank=True,
    )
    retail_price = models.FloatField(
        verbose_name="Цена розничная",
        null=True,
        blank=True,
    )
    retail_amount = models.FloatField(
        verbose_name="Сумма продаж (возвратов)",
        null=True,
        blank=True,
    )
    sale_percent = models.BigIntegerField(
        verbose_name="Согласованная скидка",
        null=True,
        blank=True,
    )
    commission_percent = models.FloatField(
        verbose_name="Процент комиссии",
        null=True,
        blank=True,
    )
    office_name = models.CharField(
        verbose_name="Склад",
        max_length=300,
        null=True,
        blank=True,
    )
    supplier_oper_name = models.CharField(
        verbose_name="Обоснование для оплаты",
        max_length=300,
        null=True,
        blank=True,
    )
    order_dt = models.DateTimeField(
        verbose_name="Дата заказа",
        null=True,
        blank=True,
    )
    sale_dt = models.DateTimeField(
        verbose_name="Дата продажи",
        null=True,
        blank=True,
    )
    rr_dt = models.DateTimeField(
        verbose_name="Дата операции",
        null=True,
        blank=True,
    )
    shk_id = models.BigIntegerField(
        verbose_name="Штрихкод",
        null=True,
        blank=True,
    )
    retail_price_withdisc_rub = models.FloatField(
        verbose_name="Цена розничная с учетом согласованной скидки",
        null=True,
        blank=True,
    )
    delivery_amount = models.BigIntegerField(
        verbose_name="Количество доставок",
        null=True,
        blank=True,
    )
    return_amount = models.BigIntegerField(
        verbose_name="Количество возвратов",
        null=True,
        blank=True,
    )
    delivery_rub = models.FloatField(
        verbose_name="Стоимость логистики",
        null=True,
        blank=True,
    )
    gi_box_type_name = models.CharField(
        verbose_name="Тип коробов",
        max_length=300,
        blank=True,
    )
    product_discount_for_report = models.FloatField(
        verbose_name="Согласованный продуктовый дисконт",
        null=True,
        blank=True,
    )
    supplier_promo = models.FloatField(
        verbose_name="Промокод",
        null=True,
        blank=True,
    )
    rid = models.BigIntegerField(
        verbose_name="Уникальный идентификатор заказа",
        null=True,
        blank=True,
    )
    ppvz_spp_prc = models.FloatField(
        verbose_name="Скидка постоянного покупателя",
        null=True,
        blank=True,
    )
    ppvz_kvw_prc_base = models.FloatField(
        verbose_name="Размер кВВ без НДС, % базовый",
        null=True,
        blank=True,
    )
    ppvz_kvw_prc = models.FloatField(
        verbose_name="Итоговый кВВ без НДС, %",
        null=True,
        blank=True,
    )
    sup_rating_prc_up = models.FloatField(
        verbose_name="Размер снижения кВВ из-за рейтинга",
        null=True,
        blank=True,
    )
    is_kgvp_v2 = models.FloatField(
        verbose_name="Размер снижения кВВ из-за акции",
        null=True,
        blank=True,
    )
    ppvz_sales_commission = models.FloatField(
        verbose_name=(
            "Вознаграждение с продаж до вычета услуг поверенного, без НДС"
        ),
        null=True,
        blank=True,
    )
    ppvz_for_pay = models.FloatField(
        verbose_name="К перечислению продавцу за реализованный товар",
        null=True,
        blank=True,
    )
    ppvz_reward = models.FloatField(
        verbose_name="Возмещение за выдачу и возврат товаров на ПВЗ",
        null=True,
        blank=True,
    )
    acquiring_fee = models.FloatField(
        verbose_name="Возмещение издержек по эквайрингу",
        null=True,
        blank=True,
    )
    acquiring_bank = models.CharField(
        verbose_name="Наименование банка-эквайера",
        max_length=300,
        blank=True,
    )
    ppvz_vw = models.FloatField(
        verbose_name="Вознаграждение WB без НДС",
        null=True,
        blank=True,
    )
    ppvz_vw_nds = models.FloatField(
        verbose_name="НДС с вознаграждения WB",
        null=True,
        blank=True,
    )
    ppvz_office_id = models.BigIntegerField(
        verbose_name="Номер офиса",
        null=True,
        blank=True,
    )
    ppvz_office_name = models.CharField(
        verbose_name="Наименование офиса доставки",
        max_length=300,
        null=True,
        blank=True,
    )
    ppvz_supplier_id = models.BigIntegerField(
        verbose_name="Номер партнера",
        null=True,
        blank=True,
    )
    ppvz_supplier_name = models.CharField(
        verbose_name="Партнер",
        max_length=300,
        null=True,
        blank=True,
    )
    ppvz_inn = models.CharField(
        verbose_name="ИНН партнера",
        max_length=30,
        null=True,
        blank=True,
    )
    declaration_number = models.CharField(
        verbose_name="Номер таможенной декларации",
        max_length=300,
        null=True,
        blank=True,
    )
    bonus_type_name = models.CharField(
        verbose_name="Обоснование штрафов и доплат",
        max_length=200,
        null=True,
        blank=True,
    )
    sticker_id = models.CharField(
        verbose_name="Цифровое значение стикера",
        max_length=80,
        null=True,
        blank=True,
    )
    site_country = models.CharField(
        verbose_name="Страна продажи",
        max_length=80,
        null=True,
        blank=True,
    )
    penalty = models.FloatField(
        verbose_name="Штрафы",
        null=True,
        blank=True,
    )
    additional_payment = models.FloatField(
        verbose_name="Доплаты",
        null=True,
        blank=True,
    )
    rebill_logistic_cost = models.FloatField(
        verbose_name="Возмещение издержек по перевозке",
        null=True,
        blank=True,
    )
    rebill_logistic_org = models.CharField(
        verbose_name="Организатор перевозки",
        max_length=150,
        null=True,
        blank=True,
    )
    kiz = models.CharField(
        verbose_name="Код маркировки",
        max_length=300,
        null=True,
        blank=True,
    )
    storage_fee = models.FloatField(
        verbose_name="Стоимость хранения",
        null=True,
        blank=True,
    )
    deduction = models.FloatField(
        verbose_name="Прочие удержания/выплаты",
        null=True,
        blank=True,
    )
    acceptance = models.FloatField(
        verbose_name="Стоимость платной приёмки",
        null=True,
        blank=True,
    )
    srid = models.CharField(
        verbose_name="Уникальный идентификатор заказа",
        max_length=300,
        null=True,
        blank=True,
    )
    report_type = models.IntegerField(
        verbose_name="Стоимость платной приёмки",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Отчет о продажах по реализации"
        verbose_name_plural = "Отчет о продажах по реализации"


class WeeklyReportInDatabase(models.Model):
    """
    Указывает, что еженедельный отчет записался в базу данных.
    К этой информации привязаны сигналы для обновления аналитики по отчетам.
    """

    realizationreport_id = models.BigIntegerField(
        verbose_name="Номер отчета", unique=True
    )
    date_from = models.DateTimeField(
        verbose_name="Дата начала отчётного периода",
        null=True,
        blank=True,
    )
    date_to = models.DateTimeField(
        verbose_name="Дата конца отчётного периода",
        null=True,
        blank=True,
    )
    create_dt = models.DateTimeField(
        verbose_name="Дата формирования отчёта",
        null=True,
        blank=True,
    )


class StorageCost(models.Model):
    """Стоимость хранения артикулов по датам"""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="storage_cost",
        blank=True,
        null=True,
    )
    start_date = models.DateField(
        verbose_name="Начало периода",
        null=True,
        blank=True,
    )
    storage_cost = models.FloatField(
        verbose_name="Затраты на хранение",
    )

    class Meta:
        verbose_name = "Стоимость хранения артикулов по датам"
        verbose_name_plural = "Стоимость хранения артикулов по датам"


class ArticleStorageCost(models.Model):
    """Стоимость хранения артикулов по датам"""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="article_storage_cost",
        blank=True,
        null=True,
    )
    date = models.DateField(
        verbose_name="Дата, за которую был расчёт или перерасчёт",
        null=True,
        blank=True,
    )
    log_warehouse_coef = models.FloatField(
        verbose_name="Коэффициент логистики и хранения",
    )
    office_id = models.IntegerField(
        verbose_name="ID склада",
    )
    warehouse = models.CharField(
        verbose_name="Название склада",
        max_length=300,
        null=True,
        blank=True,
    )
    warehouse_coef = models.FloatField(
        verbose_name="Коэффициент склада",
    )
    gi_id = models.IntegerField(
        verbose_name="ID поставки",
    )
    chrt_id = models.IntegerField(
        verbose_name="ID размера для этого артикула WB",
    )
    size = models.CharField(
        verbose_name="Размер (techSize в карточке товара)",
        max_length=300,
        null=True,
        blank=True,
    )
    barcode = models.CharField(
        verbose_name="Баркод",
        max_length=300,
        null=True,
        blank=True,
    )
    subject = models.CharField(
        verbose_name="Предмет",
        max_length=300,
        null=True,
        blank=True,
    )
    brand = models.CharField(
        verbose_name="Бренд",
        max_length=300,
        null=True,
        blank=True,
    )
    vendor_code = models.CharField(
        verbose_name="Артикул продавца",
        max_length=300,
        null=True,
        blank=True,
    )
    nm_id = models.IntegerField(
        verbose_name="Артикул WB",
    )
    volume = models.FloatField(
        verbose_name="Объём товара",
    )
    calc_type = models.CharField(
        verbose_name="Способ расчёта",
        max_length=300,
        null=True,
        blank=True,
    )
    warehouse_price = models.FloatField(
        verbose_name="Сумма хранения",
    )
    barcodes_count = models.IntegerField(
        verbose_name=(
            "Количество единиц товара (штук), "
            "подлежащих тарифицированию за расчётные сутки"
        ),
    )
    pallet_place_code = models.IntegerField(
        verbose_name="Код паллетоместа",
    )
    pallet_count = models.FloatField(
        verbose_name="Количество паллет",
    )
    original_date = models.CharField(
        verbose_name=(
            "Если был перерасчёт, это дата первоначального расчёта. "
            "Если перерасчёта не было, совпадает с date"
        ),
        max_length=300,
        null=True,
        blank=True,
    )
    loyalty_discount = models.FloatField(
        verbose_name="Скидка программы лояльности, ₽",
    )
    tariffFix_date = models.CharField(
        verbose_name="Дата фиксации тарифа",
        max_length=300,
        null=True,
        blank=True,
    )
    tariff_lower_date = models.CharField(
        verbose_name="Дата понижения тарифа",
        max_length=300,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Стоимость хранения артикулов по датам"
        verbose_name_plural = "Стоимость хранения артикулов по датам"


class ArticlePriceStock(models.Model):
    """
    Содержит данные об общих остатках каждого артикула, цене продавца и СПП
    """

    marketplace = models.ForeignKey(
        Marketplace,
        related_name="article_price_stock",
        on_delete=models.CASCADE,
        verbose_name="Маркетплейс",
        default=1,
    )
    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="article_pricestock",
        blank=True,
        null=True,
    )
    date = models.DateField(
        verbose_name="Дата обновления информации",
        null=True,
        blank=True,
    )
    common_stock = models.IntegerField(
        verbose_name="общий остаток на всех складах",
        null=True,
        blank=True,
    )
    price_in_page = models.FloatField(
        verbose_name="Цена товара на странице ВБ",
        null=True,
        blank=True,
    )
    price_after_seller_disc = models.FloatField(
        verbose_name="Цена товара после скидки продавца",
        null=True,
        blank=True,
    )
    price_before_seller_disc = models.FloatField(
        verbose_name="Цена товара до скидки продавца",
        null=True,
        blank=True,
    )
    seller_disc = models.FloatField(
        verbose_name="Скидка продавца",
        null=True,
        blank=True,
    )
    spp = models.FloatField(
        verbose_name="Скидка маркетплейса",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = (
            "Данные об общих остатках каждого артикула, цене продавца и СПП"
        )
        verbose_name_plural = (
            "Данные об общих остатках каждого артикула, цене продавца и СПП"
        )


# ========== КЛАСТЕРЫ. СКЛАДЫ. ОСТАТКИ. =========== #
class Cluster(models.Model):
    """Кластеры Маркетплейса"""

    id = models.IntegerField(primary_key=True, verbose_name="ID кластера")
    marketplace = models.ForeignKey(
        Marketplace,
        on_delete=models.CASCADE,
        verbose_name="Маркетплейс",
        related_name="cluster",
    )
    name = models.CharField(verbose_name="Название кластера", max_length=255)

    def __str__(self):
        return f"{self.marketplace.name} {self.name}"

    class Meta:
        verbose_name = "Кластеры маркетплейса"
        verbose_name_plural = "Кластеры маркетплейса"


class Warehouse(models.Model):
    """Склад Маркетплейса"""

    marketplace = models.ForeignKey(
        Marketplace,
        on_delete=models.CASCADE,
        verbose_name="Маркетплейс",
        related_name="warehouse",
        blank=True,
        null=True,
    )
    cluster = models.ForeignKey(
        Cluster,
        on_delete=models.SET_NULL,
        verbose_name="Кластер",
        related_name="warehouse",
        blank=True,
        null=True,
    )
    warehouse_number = models.BigIntegerField(
        verbose_name="ID склада в системе маркетплейса",
        default=0,
        blank=True,
        null=True,
    )
    name = models.CharField(
        verbose_name="Название склада на маркетпелйсе",
        max_length=255,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"{self.marketplace.name} {self.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["marketplace", "warehouse_number", "name"],
                name="unique_warehouse",
            )
        ]
        verbose_name = "Склады маркетплейса"
        verbose_name_plural = "Склады маркетплейса"


class WarehouseBalance(models.Model):
    """Остатки на складах маркетплейса"""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name="Компания",
        related_name="balance",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        verbose_name="Склад",
        related_name="balance",
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name="Артикул",
        related_name="balance",
        null=True,
    )
    ozon_article = models.ForeignKey(
        OzonProduct,
        on_delete=models.CASCADE,
        verbose_name="Артикул",
        related_name="balance",
        null=True,
    )
    date = models.DateField(
        verbose_name="Дата проверки",
        null=True,
    )
    quantity = models.IntegerField(
        verbose_name="Количество",
        default=0,
    )
    idc = models.FloatField(
        verbose_name=(
            "На сколько дней хватит остатка товара "
            "с учётом среднесуточных продаж."
        ),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Остатки на складах маркетплейса"
        verbose_name_plural = "Остатки на складах маркетплейса"


# ========== ПРОДАЖИ ОЗОН =========== #
class RealizationReportOzon(models.Model):
    """Ежемесячный отчет реализации Озон"""

    company = models.ForeignKey(
        Company,
        verbose_name="Компания",
        on_delete=models.SET_NULL,
        related_name="company_ozon_realization_report",
        null=True,
    )

    contract_date = models.DateField(
        verbose_name="Дата заключения договора.",
        null=True,
        blank=True,
    )
    contract_number = models.CharField(
        verbose_name="Номер договора.",
        max_length=255,
        null=True,
        blank=True,
    )
    currency_sys_name = models.CharField(
        verbose_name="Валюта.",
        max_length=255,
        null=True,
        blank=True,
    )
    doc_amount = models.FloatField(
        verbose_name="Всего к начислению.",
        null=True,
        blank=True,
    )
    doc_date = models.DateField(
        verbose_name="Дата формирования документа.",
        null=True,
        blank=True,
    )
    number = models.CharField(
        verbose_name="Номер отчёта о реализации.",
        max_length=255,
        null=True,
    )
    payer_inn = models.CharField(
        verbose_name="ИНН плательщика.",
        max_length=255,
        null=True,
    )
    payer_kpp = models.CharField(
        verbose_name="КПП плательщика.",
        max_length=255,
        null=True,
    )
    payer_name = models.CharField(
        verbose_name="Название плательщика.",
        max_length=255,
        null=True,
    )
    receiver_inn = models.CharField(
        verbose_name="ИНН получателя.",
        max_length=255,
        null=True,
    )
    receiver_kpp = models.CharField(
        verbose_name="КПП получателя.",
        max_length=255,
        null=True,
    )
    receiver_name = models.CharField(
        verbose_name="Название получателя.",
        max_length=255,
        null=True,
    )
    start_date = models.DateField(
        verbose_name="Начало периода.",
        null=True,
        blank=True,
    )
    stop_date = models.DateField(
        verbose_name="Конец периода.",
        null=True,
        blank=True,
    )
    vat_amount = models.FloatField(
        verbose_name="Итоговая сумма с НДС.",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Ежемесячный отчет реализации Озон"
        verbose_name_plural = "Ежемесячный отчет реализации Озон"


class ArticlesRealizationReportOzon(models.Model):
    """Ежемесячный отчет о реализации Озон (деализация)"""

    article = models.ForeignKey(
        OzonProduct,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="article_ozon_realization_report",
        null=True,
    )
    report = models.ForeignKey(
        RealizationReportOzon,
        on_delete=models.CASCADE,
        verbose_name="Отчет",
        related_name="report_detalization",
    )
    row_number = models.IntegerField(verbose_name="Номер строки в отчете")
    commission_ratio = models.FloatField(
        verbose_name="Доля комиссии за продажу по категории."
    )
    seller_price_per_instance = models.FloatField(
        verbose_name="Цена продавца с учётом скидки.",
        null=True,
    )
    price_per_instance = models.FloatField(
        verbose_name="Цена за экземпляр.",
        null=True,
    )
    quantity = models.IntegerField(
        verbose_name="Количество.",
        null=True,
    )
    amount = models.FloatField(verbose_name="Сумма.", null=True)
    compensation = models.FloatField(
        verbose_name="Доплата за счет Озон.",
        null=True,
    )
    commission = models.FloatField(
        verbose_name="Итого комиссия с учётом скидок и наценки.",
        null=True,
    )
    bonus = models.FloatField(
        verbose_name="Баллы за скидки.",
        null=True,
    )
    standard_fee = models.FloatField(
        verbose_name="Базовое вознаграждение Ozon.",
        null=True,
    )
    total = models.FloatField(
        verbose_name="Итого к начислению.",
        null=True,
    )
    stars = models.FloatField(
        verbose_name="Выплаты по механикам лояльности партнёров: звёзды.",
        null=True,
    )
    bank_coinvestment = models.FloatField(
        verbose_name=(
            "Выплаты по механикам лояльности партнёров: зелёные цены."
        ),
        null=True,
    )
    pick_up_point_coinvestment = models.FloatField(
        verbose_name="Выплаты по механикам лояльности партнёров: АПВЗ.",
        null=True,
    )

    class Meta:
        verbose_name = "Детализация ежемесячного отчета Озон"
        verbose_name_plural = "Детализация ежемесячного отчета Озон"


class ReturnArticlesRealizationReportOzon(models.Model):
    """Возвраты в Ежемесячном отчете о реализации Озон (деализация)"""

    report_row = models.ForeignKey(
        ArticlesRealizationReportOzon,
        verbose_name="Строка отчета",
        on_delete=models.SET_NULL,
        related_name="report_row_return",
        null=True,
    )
    price_per_instance = models.FloatField(
        verbose_name="Цена за экземпляр.",
        null=True,
    )
    quantity = models.IntegerField(
        verbose_name="Количество.",
        null=True,
    )
    amount = models.FloatField(verbose_name="Сумма.", null=True)
    compensation = models.FloatField(
        verbose_name="Доплата за счет Озон.",
        null=True,
    )
    commission = models.FloatField(
        verbose_name="Итого комиссия с учётом скидок и наценки.",
        null=True,
    )
    bonus = models.FloatField(
        verbose_name="Баллы за скидки.",
        null=True,
    )
    standard_fee = models.FloatField(
        verbose_name="Базовое вознаграждение Ozon.",
        null=True,
    )
    total = models.FloatField(
        verbose_name="Итого к начислению.",
        null=True,
    )
    stars = models.FloatField(
        verbose_name="Выплаты по механикам лояльности партнёров: звёзды.",
        null=True,
    )
    bank_coinvestment = models.FloatField(
        verbose_name=(
            "Выплаты по механикам лояльности партнёров: зелёные цены."
        ),
        null=True,
    )
    pick_up_point_coinvestment = models.FloatField(
        verbose_name="Выплаты по механикам лояльности партнёров: АПВЗ.",
        null=True,
    )

    class Meta:
        verbose_name = "Возвраты ежемесячного отчета Озон"
        verbose_name_plural = "Возвраты ежемесячного отчета Озон"


class MarketplaceOrders(models.Model):
    """Заказы с маркетплейсов"""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name="Компания",
        related_name="marketplace_orders",
    )
    marketplace = models.ForeignKey(
        Marketplace,
        on_delete=models.CASCADE,
        verbose_name="Маркетплейс",
        related_name="marketplace_orders",
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name="Артикул",
        related_name="marketplace_orders",
        null=True,
    )
    ozon_article = models.ForeignKey(
        OzonProduct,
        on_delete=models.CASCADE,
        verbose_name="Товар с Озон",
        related_name="marketplace_orders",
        null=True,
    )
    posting_number = models.CharField(
        verbose_name="Номер отправления.",
        max_length=255,
        null=True,
    )
    order_id = models.CharField(
        verbose_name="ID ордера.",
        max_length=255,
        null=True,
    )
    order_number = models.CharField(
        verbose_name="Номер ордера.",
        max_length=255,
        null=True,
    )
    date = models.DateField(
        verbose_name="Дата заказа",
    )
    amount = models.IntegerField(
        verbose_name="Количество",
    )
    order_cluster = models.ForeignKey(
        Cluster,
        on_delete=models.CASCADE,
        verbose_name="Кластер, из которого пришел заказ",
        related_name="marketplace_orders",
        null=True,
    )
    order_type = models.CharField(
        verbose_name="Тип заказа ФБО/ФБС.",
        max_length=10,
        null=True,
    )
    price = models.FloatField(
        verbose_name="Цена заказа.",
        null=True,
    )
