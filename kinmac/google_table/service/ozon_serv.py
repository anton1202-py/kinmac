from collections import defaultdict
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q, Case, When, IntegerField
from database.models import (
    Company,
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
    "MarketplaceServiceItemDelivToCustomer",
    "MarketplaceServiceItemDirectFlowTrans",
    "MarketplaceServiceItemReturnFlowTrans",
    "MarketplaceServiceItemDirectFlowLogistic",
    "MarketplaceServiceItemReturnFlowLogistic",
    "MarketplaceServiceItemReturnNotDelivToCustomer",
    "MarketplaceServiceItemPickup",
    "MarketplaceServiceItemDeliveryKGT",
    "MarketplaceServiceItemDirectFlowLogisticVDC",
    "MarketplaceServiceItemRedistributionReturnsPVZ",
    "MarketplaceServiceItemReturnAfterDelivToCustomer",
]


class OzonMarketplaceArticlesData:
    """Данные артикулов по Озон"""

    def __init__(self, weeks_amount):
        self.weeks_amount = weeks_amount

    def only_sales_data(self):
        end_date = datetime.now() - timedelta(days=9)
        start_date = end_date - timedelta(weeks=self.weeks_amount)
        response_dict = {}
        sales_dict = {}
        operation_list = ["orders", "returns"]
        # sale_data = (
        #     OzonTransaction.objects.filter(
        #         company=Company.objects.filter(name="KINMAC").first(),
        #         article__description_category_id__in=OZON_CATEGORY_LIST,
        #         operation_date__date__gte=start_date.date(),
        #         operation_date__date__lte=end_date.date(),
        #         type__in=operation_list,
        #     )
        #     .order_by("article__seller_article")
        #     .values("article__seller_article")
        #     .annotate(
        #         sales_amount=Count("accruals_for_sale"),
        #         sales_sum=Sum("accruals_for_sale"),
        #     )
        # )

        sale_data = (
            OzonTransaction.objects.filter(
                company=Company.objects.filter(name="KINMAC").first(),
                article__description_category_id__in=OZON_CATEGORY_LIST,
                operation_date__gte=start_date,
                operation_date__lte=end_date,
            )
            .exclude(accruals_for_sale=0)
            .order_by("article__seller_article")
            .values("article__seller_article")
            .annotate(
                sales_amount=Sum(
                    Case(
                        When(type="orders", then=1),
                        When(type="returns", then=-1),
                        output_field=IntegerField(),
                    )
                ),
                sales_sum=Sum("accruals_for_sale"),
            )
        )
        for data in sale_data:
            sales_dict[data["article__seller_article"]] = {
                "sales_amount": data["sales_amount"],
                "sales_sum": data["sales_sum"],
            }
        for article_obj in OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article"):
            if article_obj.seller_article in sales_dict:
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
        sales_sum = 0
        sales_amount = 0
        for article, data in response_dict.items():
            sales_sum += data["sales_sum"]
            sales_amount += data["sales_amount"]
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
                "price": data.price,
                "marketing_price": data.marketing_price,
                "with_ozon_card_price": data.with_card_price,
            }
        return response_dict

    def stock_data(self):
        """Отдает данные по SPP, остаткам, цене"""
        check_date = datetime.now().date()
        stock_data = (
            WarehouseBalance.objects.filter(
                ozon_article__description_category_id__in=OZON_CATEGORY_LIST,
                date=check_date,
            )
            .values("ozon_article__seller_article", "date")
            .annotate(
                common_stock=Sum("quantity"),
            )
            .order_by("ozon_article__seller_article")
        )

        stock_dict = {}
        for data in stock_data:
            stock_dict[data["ozon_article__seller_article"]] = {
                "common_stock": data["common_stock"],
                "date": data["date"],
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
        """Расход на рекламу"""
        end_date = (datetime.now() - timedelta(days=1)).date()
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
        end_date = datetime.now() - timedelta(days=1)
        # Дата начала периода (начало num_weeks назад)
        start_date = end_date - timedelta(weeks=self.weeks_amount)

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
        filtered_transactions = (
            (
                (
                    OzonTransaction.objects.filter(
                        operation_date__gte=start_date,
                        operation_date__lte=end_date,
                        # article__seller_article__in=art_list,
                        article__description_category_id__in=OZON_CATEGORY_LIST,
                    ).order_by("article__seller_article")
                )
                .prefetch_related("services")
                .select_related("article")
            )
            .annotate(
                total_price=Sum(
                    "services__price",
                    filter=Q(services__name__in=LOGISTIC_OPERATION_TYPES),
                )
            )
            .values("article__seller_article", "total_price", "posting_number")
        )
        logistic_data = defaultdict(int)

        for i in filtered_transactions:
            if i["total_price"]:
                logistic_data[i["article__seller_article"]] += i["total_price"]

        for article_obj in OzonProduct.objects.filter(
            company=Company.objects.filter(name="KINMAC").first(),
            description_category_id__in=OZON_CATEGORY_LIST,
        ).order_by("seller_article"):

            main_returned_dict[article_obj.seller_article] = {
                "logistic_cost": (
                    abs(logistic_data[article_obj.seller_article])
                    if article_obj.seller_article in logistic_data
                    else 0
                ),
                "storage_cost": (
                    storage_cost[article_obj.seller_article]
                    if article_obj.seller_article in storage_cost
                    else 0
                ),
            }
        return main_returned_dict
