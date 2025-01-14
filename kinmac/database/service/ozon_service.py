from datetime import datetime

from database.service.service import ModelObjectService

from api_requests.ozon_requests import OzonWarehouseApiRequest
from database.models import Cluster, Company, Marketplace, Warehouse, WarehouseBalance


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
        print("cluster_obj", cluster_obj)
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
        clusters_info = self.request.cluster_warehouse_req(self.company_obj.ozon_header)
        for cluster in clusters_info.get("clusters"):
            cluster_obj = self.get_cluster_obj(
                marketplace_obj=self.marketplace_obj, cluster_info=cluster
            )
            for logistic_clusters in cluster.get("logistic_clusters"):
                if logistic_clusters:
                    for warehouse in logistic_clusters.get("warehouses"):
                        warehouse_number = warehouse.get("warehouse_id")
                        warehouse_name = warehouse.get("name")

                        warehouse_obj, created = Warehouse.objects.get_or_create(
                            marketplace=self.marketplace_obj,
                            warehouse_number=warehouse_number,
                            name=warehouse_name,
                            defaults={"cluster": cluster_obj},
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
                        balance, created = WarehouseBalance.objects.update_or_create(
                            company=company,
                            warehouse=warehouse_obj,
                            article=article_obj,
                            date=datetime.now().date(),
                            defaults={"quantity": quantity, "idc": idc},
                        )
