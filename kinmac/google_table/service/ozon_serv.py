from datetime import datetime, timedelta
from django.db.models import Count, Sum, Max
from database.models import (
    Company,
    Marketplace,
    MarketplaceOrders,
    OzonArticleStorageCost,
    OzonProduct,
    OzonTransaction,
    WarehouseBalance,
)
from reklama.models import OzonArticleDailyCostToAdv

OZON_CATEGORY_LIST = [17028939, 17027904]

LOGISTIC_OPERATION_TYPES: list = [
    "MarketplaceNotDeliveredCostItem",
    "MarketplaceReturnAfterDeliveryCostItem",
    "MarketplaceDeliveryCostItem",
    "ItemAdvertisementForSupplierLogistic",
    "ItemAdvertisementForSupplierLogisticSeller",
    "MarketplaceServiceItemDelivToCustomer",
    "MarketplaceServiceItemDirectFlowTrans",
    "MarketplaceServiceItemDropoffFF",
    "MarketplaceServiceItemDropoffPVZ",
    "MarketplaceServiceItemDropoffSC",
    "MarketplaceServiceItemFulfillment",
    "MarketplaceServiceItemPickup",
    "MarketplaceServiceItemReturnAfterDelivToCustomer",
    "MarketplaceServiceItemReturnFlowTrans",
    "MarketplaceServiceItemDeliveryKGT",
    "MarketplaceServiceItemDirectFlowLogistic",
    "MarketplaceServiceItemReturnFlowLogistic",
    "MarketplaceServiceItemRedistributionReturnsPVZ",
    "MarketplaceServiceItemDirectFlowLogisticVDC",
]


class OzonMarketplaceArticlesData:
    """Данные артикулов по Озон"""

    def __init__(self, weeks_amount):
        self.weeks_amount = weeks_amount

    def only_sales_data(self):
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=self.weeks_amount)
        response_dict = {}
        sales_dict = {}

        sale_data = (
            MarketplaceOrders.objects.filter(
                company=Company.objects.filter(name="KINMAC").first(),
                marketplace=Marketplace.objects.filter(name="Ozon").first(),
                ozon_article__description_category_id__in=OZON_CATEGORY_LIST,
                date__gte=start_date,
                date__lte=end_date,
            )
            .order_by("ozon_article__seller_article")
            .values("ozon_article__seller_article")
            .annotate(
                sales_amount=Count("amount"),
                sales_sum=Sum("price"),
            )
        )
        for data in sale_data:
            sales_dict[data["ozon_article__seller_article"]] = {
                "sales_amount": data["sales_amount"],
                "sales_sum": data["sales_sum"],
            }
        for article_obj in OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article"):
            if article_obj.product_id in sales_dict:
                response_dict[article_obj.seller_article] = {
                    "sales_amount": sales_dict[article_obj.seller_article][
                        "sales_amount"
                    ],
                    "sales_sum": sales_dict[article_obj.seller_article][
                        "sales_sum"
                    ],
                }
            else:
                response_dict[article_obj.seller_article] = {
                    "sales_amount": 0,
                    "sales_sum": 0,
                }
        return response_dict

    def common_article_data(self):
        """Общая информация артикула"""
        comissions = OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article")
        response_dict = {}
        for data in comissions:
            response_dict[data.seller_article] = {
                "fbo_commission": data.fbo_comission,
                "width": data.width,
                "height": data.height,
                "length": data.depth,
                "weight": data.weight,
                "marketing_price": data.marketing_price,
                "with_ozon_card_price": data.with_card_price,
            }
        return response_dict

    def stock_data(self):
        """Отдает данные по SPP, остаткам, цене"""
        stock_data = (
            WarehouseBalance.objects.filter(
                ozon_article__description_category_id__in=OZON_CATEGORY_LIST
            )
            .values("ozon_article__seller_article")
            .annotate(
                latest_date=Max("date"),
                common_stock=Sum("quantity"),
            )
            .order_by("ozon_article__seller_article")
        )

        stock_dict = {}
        for data in stock_data:
            stock_dict[data["ozon_article__seller_article"]] = {
                "date": data["latest_date"],
                "common_stock": data["common_stock"],
            }
        response_dict = {}
        for article_obj in OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article"):
            if article_obj.seller_article in stock_dict:
                response_dict[article_obj.seller_article] = {
                    "date": stock_dict[article_obj.seller_article]["date"],
                    "common_stock": stock_dict[article_obj.seller_article][
                        "common_stock"
                    ],
                }
            else:
                response_dict[article_obj.seller_article] = {
                    "date": 0,
                    "common_stock": 0,
                }
        return response_dict

    def advert_data(self):
        """Получение данных а цене артикула в акции"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=self.weeks_amount)
        adv_dict = {}
        adv_data = (
            OzonArticleDailyCostToAdv.objects.filter(
                article__description_category_id__in=OZON_CATEGORY_LIST,
                cost_date__gte=start_date,
                cost_date__lte=end_date,
            )
            .order_by("article__seller_article")
            .values("article__seller_article")
            .annotate(sum_cost=Sum("cost"))
        )
        for data in adv_data:
            adv_dict[data["article__seller_article"]] = data["sum_cost"]

        response_dict = {}
        articles_data = OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article")
        for data in articles_data:
            response_dict[data.seller_article] = {
                "adv_cost_sum": (
                    round(adv_dict[data.seller_article], 2)
                    if data.seller_article in adv_dict
                    else 0
                ),
            }
        return response_dict

    def logistic_storage_cost(self):
        """
        Входящие данные - количество недель за которые нужно отдать данные
        """
        end_date = datetime.now()
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=self.weeks_amount)

        logistic_cost = {}
        storage_cost = {}

        main_returned_dict = {}

        storage_data = (
            OzonArticleStorageCost.objects.filter(
                company=Company.objects.filter(name="KINMAC").first(),
                date__gte=start_date,
                date__lte=end_date,
                article__description_category_id__in=OZON_CATEGORY_LIST,
            )
            .order_by("article__seller_article")
            .values("article__seller_article")
            .annotate(storage_cost=Sum("warehouse_price"))
        )

        for data in storage_data:
            storage_cost[data["article__seller_article"]] = round(
                data["storage_cost"], 2
            )

        logistic_data = (
            OzonTransaction.objects.filter(
                order_date__gte=start_date,
                order_date__lte=end_date,
                operation_type__in=LOGISTIC_OPERATION_TYPES,
                article__description_category_id__in=OZON_CATEGORY_LIST,
            )
            .order_by("article__seller_article")
            .values("article__seller_article")
            .annotate(logistic_cost=Sum("amount"))
        )
        for data in logistic_data:
            logistic_cost[data["article__seller_article"]] = round(
                data["logistic_cost"], 2
            )

        for article_obj in OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article"):

            main_returned_dict[article_obj.seller_article] = {
                "logistic_cost": (
                    logistic_cost[article_obj.seller_article]
                    if article_obj.seller_article in logistic_cost
                    else 0
                ),
                "storage_cost": (
                    storage_cost[article_obj.seller_article]
                    if article_obj.seller_article in storage_cost
                    else 0
                ),
            }
        return main_returned_dict
