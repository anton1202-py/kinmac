from datetime import datetime
from database.models import ArticlePriceStock, Articles, Company, Marketplace
from unit_economic.models import MarketplaceCommission


class OzonComissionsPriceHandler:
    """Сохраняет комиссии и цену товаров с Озон"""

    def comission_handler(self, company: Company, article_info: dict):
        """Обрабатывает данные по комиссиям артикула"""
        article = Articles.objects.filter(
            ozon_product_id=article_info["product_id"]
        ).first()
        if not article:
            article = Articles.objects.filter(
                common_article=article_info["offer_id"]
            ).first()

        if article:
            comissions_data = article_info["commissions"]
            fbs_commission = comissions_data["sales_percent_fbs"]
            fbo_commission = comissions_data["sales_percent_fbo"]
            search_params = {
                "marketplace": Marketplace.objects.get(name="Ozon"),
                "marketplace_product": article,
            }
            values_for_update = {
                "fbs_commission": fbs_commission,
                "fbo_commission": fbo_commission,
            }

            MarketplaceCommission.objects.update_or_create(
                defaults=values_for_update, **search_params
            )

    def price_handler(self, company: Company, article_info: dict):
        """Обрабатывает данные по цене артикула"""
        article = Articles.objects.filter(
            ozon_product_id=article_info["product_id"]
        ).first()
        if not article:
            article = Articles.objects.filter(
                common_article=article_info["offer_id"]
            ).first()

        if article:
            seller_disc = (
                (
                    1
                    - article_info["price"]["marketing_seller_price"]
                    / article_info["price"]["old_price"]
                )
                * 100
                if article_info["price"]["old_price"] != 0
                else 0
            )
            defaults = {
                "date": datetime.now().date(),
                "price_in_page": article_info["price"]["price"],
                "price_after_seller_disc": article_info["price"][
                    "marketing_seller_price"
                ],
                "price_before_seller_disc": article_info["price"]["old_price"],
                "seller_disc": round(seller_disc),
            }
            ArticlePriceStock.objects.update_or_create(
                article=article,
                marketplace=Marketplace.objects.get(name="Ozon"),
                defaults=defaults,
            )
