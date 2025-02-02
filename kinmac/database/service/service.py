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
            article_obj = OzonProduct.objects.filter(
                barcode=ozon_barcode,
            ).first()
            if article_obj:
                article_obj.product_id = ozon_product_id
                article_obj.seller_article = ozon_seller_article
                article_obj.sku = ozon_sku
                article_obj.barcode = ozon_barcode
                article_obj.save()
            elif OzonProduct.objects.filter(
                common_article=common_article,
            ).first():
                article_obj = OzonProduct.objects.filter(
                    common_article=common_article,
                ).first()
                article_obj.product_id = ozon_product_id
                article_obj.seller_article = ozon_seller_article
                article_obj.sku = ozon_sku
                article_obj.barcode = ozon_barcode
                article_obj.save()

            else:

                article_obj = OzonProduct.objects.get_or_create(
                    seller_article=common_article,
                    product_id=ozon_product_id,
                    sku=ozon_sku,
                    barcode=ozon_barcode,
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
    ) -> OzonProduct:
        """."""
        product_id = int(product_id)
        article_obj = OzonProduct.objects.filter(
            company=company, product_id=product_id
        ).first()

        # if not article_obj:
        #     article_obj = self.add_article_from_ozon(
        #         company=company, products=[product_id]
        #     )

        return article_obj
