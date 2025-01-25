from collections import defaultdict
from datetime import datetime

from database.service.service import ModelObjectService

from api_requests.ozon_requests import OzonWarehouseApiRequest
from database.models import (
    Articles,
    Cluster,
    Company,
    Marketplace,
    MarketplaceOrders,
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
                        balance, created = (
                            WarehouseBalance.objects.update_or_create(
                                company=company,
                                warehouse=warehouse_obj,
                                article=article_obj,
                                date=datetime.now().date(),
                                defaults={"quantity": quantity, "idc": idc},
                            )
                        )


class OzonSalesOrdersHandler:
    """Обрабатывает продажи и заказы Озон"""

    def save_order_data(self, order_data: dict) -> None:

        order, created = MarketplaceOrders.objects.get_or_create(
            company=order_data.get("company"),
            marketplace=order_data.get("marketplace"),
            article=order_data.get("article"),
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
                article = Articles.objects.filter(
                    ozon_sku=product["sku"]
                ).first()
                amount = product["quantity"]
                price = product["price"]

                order_data = {
                    "company": company,
                    "marketplace": marketplace,
                    "article": article,
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
