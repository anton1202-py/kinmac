from datetime import datetime

from database.service.service import ModelObjectService

from api_requests.ozon_requests import OzonWarehouseApiRequest
from database.models import (
    Cluster,
    Company,
    Marketplace,
    MarketplaceOrders,
    OzonArticleStorageCost,
    OzonProduct,
    OzonTransaction,
    TransactionService,
    Warehouse,
    WarehouseBalance,
)


class OzonWarehouseInfo:
    """Кластеры. Склады. Остатки. Озон."""

    def __init__(self):
        self.request = OzonWarehouseApiRequest()
        self.company_obj = Company.objects.get(id=1)
        self.companies_list = Company.objects.filter(
            ozon_client_id__isnull=False
        ).order_by("id")
        self.marketplace_obj = Marketplace.objects.get(id=2)
        self.get_obj = ModelObjectService()

    def get_cluster_obj(
        self, marketplace_obj: Marketplace, cluster_info: dict
    ) -> Cluster:
        """Сохраняет кластер в БД, если его нет"""
        cluster_id = cluster_info.get("id")
        name = cluster_info.get("name")
        cluster_obj, created = Cluster.objects.get_or_create(
            marketplace=marketplace_obj, id=int(cluster_id), name=name
        )
        return cluster_obj

    def get_warehouse_obj(
        self, marketplace_obj: Marketplace, warehouse_name: str
    ) -> Warehouse:
        """."""
        warehouse_obj = Warehouse.objects.filter(
            marketplace=marketplace_obj, name=warehouse_name
        ).first()
        if warehouse_obj:
            return warehouse_obj

    def save_ozon_clusters_warehouses_info(self) -> None:
        """Сохраняет данные по кластерам и складам в них"""
        clusters_info = self.request.cluster_warehouse_req(
            self.company_obj.ozon_header
        )
        for cluster in clusters_info.get("clusters"):
            cluster_obj = self.get_cluster_obj(
                marketplace_obj=self.marketplace_obj, cluster_info=cluster
            )
            for logistic_clusters in cluster.get("logistic_clusters"):
                if logistic_clusters:
                    for warehouse in logistic_clusters.get("warehouses"):
                        warehouse_number = warehouse.get("warehouse_id")
                        warehouse_name = warehouse.get("name")

                        warehouse_obj, created = (
                            Warehouse.objects.get_or_create(
                                marketplace=self.marketplace_obj,
                                warehouse_number=warehouse_number,
                                name=warehouse_name,
                                defaults={"cluster": cluster_obj},
                            )
                        )

    def save_ozon_fbo_warehouse_stock(self) -> None:
        """Сохраняет данные по остаткам на ФБО складах Озон"""
        for company in self.companies_list:
            if company.ozon_token:
                common_stock_info = self.request.warehouse_stock_req(
                    company.ozon_header
                )
                for stock_info in common_stock_info:

                    warehouse_name = stock_info.get("warehouse_name")
                    warehouse_obj = self.get_warehouse_obj(
                        self.marketplace_obj, warehouse_name
                    )
                    sku = stock_info.get("sku")
                    ozon_seller_article = stock_info.get("item_code")
                    article_obj = self.get_obj.get_article_obj_from_ozon_data(
                        company, sku, ozon_seller_article
                    )
                    quantity = stock_info.get("free_to_sell_amount")
                    idc = stock_info.get("idc")

                    if warehouse_obj and article_obj:
                        WarehouseBalance.objects.update_or_create(
                            company=company,
                            warehouse=warehouse_obj,
                            ozon_article=article_obj,
                            date=datetime.now().date(),
                            defaults={"quantity": quantity, "idc": idc},
                        )


class OzonSalesOrdersHandler:
    """Обрабатывает продажи и заказы Озон"""

    def save_order_data(self, order_data: dict) -> None:

        MarketplaceOrders.objects.get_or_create(
            company=order_data.get("company"),
            marketplace=order_data.get("marketplace"),
            ozon_article=order_data.get("ozon_article"),
            posting_number=order_data.get("posting_number"),
            order_id=order_data.get("order_id"),
            order_number=order_data.get("order_number"),
            date=order_data.get("date"),
            amount=order_data.get("amount"),
            order_cluster=order_data.get("order_cluster"),
            order_type=order_data.get("order_type"),
            price=order_data.get("price"),
        )

    def order_data_handler(
        self, company: Company, raw_order_data: dict, order_type: str
    ) -> dict:

        company = company
        marketplace = Marketplace.objects.filter(name="Ozon").first()
        for order_info in raw_order_data:
            posting_number = order_info["posting_number"]
            order_id = order_info["order_id"]
            order_number = order_info["order_number"]

            date = datetime.fromisoformat(
                order_info["in_process_at"][:-1]
            ).date()
            order_cluster = Cluster.objects.filter(
                marketplace=marketplace,
                name=order_info["financial_data"]["cluster_to"],
            ).first()
            order_type = order_type

            products = order_info["products"]

            for product in products:
                article = OzonProduct.objects.filter(
                    sku=product["sku"]
                ).first()
                amount = product["quantity"]
                price = product["price"]

                order_data = {
                    "company": company,
                    "marketplace": marketplace,
                    "ozon_article": article,
                    "posting_number": posting_number,
                    "order_id": order_id,
                    "order_number": order_number,
                    "date": date,
                    "amount": amount,
                    "order_cluster": order_cluster,
                    "order_type": order_type,
                    "price": price,
                }
                self.save_order_data(order_data)


class OzonReportsHandler:
    """Обрабатывает и сохраняет данные из отчетов Озон"""

    def _get_service_object(
        self, service_name: str, service_price: float
    ) -> TransactionService:

        service_obj, create = TransactionService.objects.get_or_create(
            name=service_name, price=service_price
        )
        return service_obj

    def _save_transaction_to_db(
        self, company: Company, transaction: dict
    ) -> OzonTransaction:
        order_date = transaction.get("posting").get("order_date")
        if order_date == "":
            order_date = None
        ozon_transaction, created = OzonTransaction.objects.update_or_create(
            company=company,
            operation_id=transaction.get("operation_id"),
            operation_date=transaction.get("operation_date"),
            operation_type=transaction.get("operation_type"),
            defaults={
                "accruals_for_sale": transaction.get("accruals_for_sale"),
                "amount": transaction.get("amount"),
                "delivery_charge": transaction.get("delivery_charge"),
                "article": transaction.get("article"),
                "operation_type_name": transaction.get("operation_type_name"),
                "delivery_schema": transaction.get("posting").get(
                    "delivery_schema"
                ),
                "order_date": order_date,
                "posting_number": transaction.get("posting").get(
                    "posting_number"
                ),
                "warehouse_id": transaction.get("posting").get("warehouse_id"),
                "return_delivery_charge": transaction.get(
                    "return_delivery_charge"
                ),
                "sale_commission": transaction.get("sale_commission"),
                "type": transaction.get("type"),
            },
        )
        ozon_transaction.services.set(transaction.get("services"))

    def transaction_handler(
        self, company: Company, transactions_info: list[dict]
    ) -> None:
        """Обрабатывает данные по отчету транзакций"""
        for transaction in transactions_info:
            skus: list[dict] = transaction.get("items")
            article = None
            if skus:
                sku = skus[0].get("sku")
                article = OzonProduct.objects.filter(
                    company=company, sku=sku
                ).first()
            services = []
            services_raw = transaction.get("services")
            if services_raw:
                for service in services_raw:
                    service_obj = self._get_service_object(
                        service_name=service["name"],
                        service_price=service["price"],
                    )
                    services.append(service_obj)
            transaction["article"] = article
            transaction["services"] = services

            self._save_transaction_to_db(
                company=company, transaction=transaction
            )


class OzonFrontDataHandler:
    """Обрабатывает данные с АПи фронта Озон"""

    def storage_cost_to_db(
        self, company: Company, cost_info: list[dict], cost_date: str
    ) -> None:
        """Сохраняет данные о затратах на хранение артикулов"""

        save_objs: list = []
        update_objs: list = []
        commo_db_cost_info = OzonArticleStorageCost.objects.filter(
            company=company, date=cost_date
        ).values_list("article__sku", flat=True)
        for cost in cost_info:

            article: OzonProduct = OzonProduct.objects.filter(
                company=company, sku=cost.get("item").get("id").get("value")
            ).first()

            quantity: int = cost.get("total_stock").get("quantity")
            warehouse_price: float = cost.get("paid").get("amount")
            if article:
                if article.sku not in commo_db_cost_info:
                    cost_obj = OzonArticleStorageCost(
                        company=company,
                        article=article,
                        date=cost_date,
                        warehouse_price=warehouse_price,
                        article_count=quantity,
                    )
                    save_objs.append(cost_obj)
                else:
                    upd_cost_obj = OzonArticleStorageCost.objects.filter(
                        company=company, article=article, date=cost_date
                    ).first()
                    upd_cost_obj.warehouse_price = warehouse_price
                    upd_cost_obj.article_count = quantity
                    update_objs.append(upd_cost_obj)

        OzonArticleStorageCost.objects.bulk_update(
            update_objs, ["warehouse_price", "article_count"]
        )
        OzonArticleStorageCost.objects.bulk_create(save_objs)

    def article_price_info_to_db(
        self, company: Company, price_info: list[dict]
    ):
        """Сохраняет цены артикула в базу данных"""
        update_data = []
        for price in price_info:
            article: OzonProduct = OzonProduct.objects.get(
                company=company, product_id=int(price["item_id"])
            )
            article.with_card_price = price.get("marketing_oa_price")
            update_data.append(article)

        OzonProduct.objects.bulk_update(update_data, ["with_card_price"])
