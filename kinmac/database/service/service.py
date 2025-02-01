from database.models import Articles, Company, OzonProduct
from api_requests.ozon_requests import ArticleDataRequest


class ModelObjectService:
    """."""

    def __init__(self):
        self.article_info = ArticleDataRequest()

    def add_article_from_ozon(
        self, company: Company, sku: list = None, products: list = None
    ):
        """Добавляет артикул в систему, если не нашел"""
        header = company.ozon_header

        article_common_data = self.article_info.ozon_product_info(
            header=header, sku=sku, products=products
        )
        article_info = article_common_data["items"][0]

        ozon_product_id = article_info["id"]
        name = article_info["name"]
        ozon_sku = sku
        if "barcodes" in article_info and article_info["barcodes"]:
            print(article_info["offer_id"], article_info["barcodes"])
            ozon_barcode = article_info["barcodes"][0]
            common_article = ozon_seller_article = article_info["offer_id"]
            article_obj = Articles.objects.filter(
                barcode=ozon_barcode,
            ).first()
            if article_obj:
                article_obj.ozon_product_id = ozon_product_id
                article_obj.ozon_seller_article = ozon_seller_article
                article_obj.ozon_sku = ozon_sku
                article_obj.ozon_barcode = ozon_barcode
                article_obj.save()
            elif Articles.objects.filter(
                common_article=common_article,
            ).first():
                article_obj = Articles.objects.filter(
                    common_article=common_article,
                ).first()
                article_obj.ozon_product_id = ozon_product_id
                article_obj.ozon_seller_article = ozon_seller_article
                article_obj.ozon_sku = ozon_sku
                article_obj.ozon_barcode = ozon_barcode
                article_obj.save()

            else:

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
    ) -> OzonProduct:
        """."""
        sku = int(sku)
        article_obj = OzonProduct.objects.filter(
            company=company, sku=sku
        ).first()

        if not article_obj:
            article_obj = OzonProduct.objects.filter(
                company=company, seller_article=ozon_seller_article
            ).first()

        # if not article_obj:
        #     article_obj = self.add_article_from_ozon(
        #         company=company, sku=[sku]
        #     )

        return article_obj

    def get_article_obj_ozon_with_product_id(
        self, company: Company, product_id: int
    ) -> Articles:
        """."""
        product_id = int(product_id)
        article_obj = Articles.objects.filter(
            ozon_product_id=product_id
        ).first()

        if not article_obj:
            article_obj = self.add_article_from_ozon(
                company=company, products=[product_id]
            )

        return article_obj
