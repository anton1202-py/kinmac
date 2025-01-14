from database.models import Articles, Company


class ModelObjectService:
    """."""

    def get_article_obj_from_ozon_data(
        self, company: Company, sku: int, ozon_seller_article: str = None
    ) -> Articles:
        """."""
        sku = int(sku)
        article_obj = Articles.objects.filter(
            company=company.name, ozon_sku=sku
        ).first()

        if not article_obj:
            article_obj = Articles.objects.filter(
                company=company.name, ozon_seller_article=ozon_seller_article
            ).first()

        return article_obj
