from database.models import Articles, Company
from api_requests.ozon_requests import ArticleDataRequest


class ModelObjectService:
    """."""

    def __init__(self):
        self.article_info = ArticleDataRequest()

    def add_article_from_ozon(self, company: Company, sku: int):
        """Добавляет артикул в систему, если не нашел"""
        header = company.ozon_header

        article_common_data = self.article_info.ozon_product_info(
            header=header, sku=[sku]
        )
        article_info = article_common_data[0]

        ozon_product_id = article_info["id"]
        name = article_info["name"]
        ozon_sku = sku
        ozon_barcode = article_info["barcodes"][0]
        common_article = ozon_seller_article = article_info["offer_id"]

        article_obj = Articles.objects.get_or_create(
            common_article=common_article,
            ozon_product_id=ozon_product_id,
            ozon_seller_article=ozon_seller_article,
            ozon_sku=ozon_sku,
            ozon_barcode=ozon_barcode,
            name=name,
        )
        return article_obj

    def get_article_obj_from_ozon_data(
        self, company: Company, sku: int, ozon_seller_article: str = None
    ) -> Articles:
        """."""
        sku = int(sku)
        article_obj = Articles.objects.filter(ozon_sku=sku).first()

        if not article_obj:
            article_obj = Articles.objects.filter(
                ozon_seller_article=ozon_seller_article
            ).first()

        if not article_obj:
            article_obj = self.add_article_from_ozon(company, sku)

        return article_obj
