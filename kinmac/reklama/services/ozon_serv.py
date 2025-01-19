from database.models import Articles, Company
from database.service.service import ModelObjectService
from reklama.models import OzonArticleDailyCostToAdv, OzonReklamaCampaign
from api_requests.ozon_requests import OzonAdvertismentApiRequest


class OzonAdvCampaignAndProducts:
    """Рекламные кампании Озон и продукты в них"""

    def __init__(self):
        self.get_obj = ModelObjectService()
        self.support_req = SupportQuery()

    def save_campaigns_to_database(
        self,
        company: Company,
        campaign_info: dict,
        campaign_type: str = None,
        article_obj: Articles = None,
    ):
        """Сохраняет рекламную кампанию озон в базу данных"""
        if article_obj is None:
            article_obj = self.support_req.product_in_campaign(
                company, campaign_info.get("id")
            )
        if campaign_info.get("placement") == [
            "PLACEMENT_TOP_PROMOTION"
        ] or campaign_info.get("placement") == ["PLACEMENT_SEARCH_AND_CATEGORY"]:
            article_obj = self.support_req.product_in_trafaret_top_campaign(
                company, campaign_info.get("id")
            )
        OzonReklamaCampaign.objects.update_or_create(
            company=company,
            number=campaign_info.get("id"),
            defaults={
                "article": article_obj,
                "name": campaign_info.get("title"),
                "status": campaign_info.get("state"),
                "type": (
                    campaign_type
                    if campaign_type
                    else campaign_info.get("advObjectType")
                ),
                "date_start": campaign_info.get("createdAt"),
            },
        )

    def article_adv_cost(self, company: Company, statistic: dict) -> None:
        """
        Сохранение расходов по рекламным кампаниям Озон
        statistic:
        {
            "id": "5310115",
            "date": "2025-01-01",
            "title": "Продвижение в поиске — все товары",
            "moneySpent": "563,20",
            "bonusSpent": "0,00",
            "prepaymentSpent": "0,00"
        }
        """
        campaign_id = statistic["id"]
        cost_date = statistic["date"]
        cost = statistic["moneySpent"]

        campaign = OzonReklamaCampaign.objects.filter(
            company=company, number=int(campaign_id)
        ).first()
        if campaign:
            article = campaign.article
            if article:
                cost = float(cost.replace(",", "."))
                OzonArticleDailyCostToAdv.objects.update_or_create(
                    campaign=campaign,
                    article=article,
                    cost_date=cost_date,
                    defaults={"cost": float(cost)},
                )

    def save_product_in_search_promo(
        self,
        company: Company,
        article_search_promo_info: dict,
        article_obj: Articles = None,
    ):
        """Артикул в продвижении в поиске"""
        if article_obj is None:
            article_obj = self.get_obj.get_article_obj_from_ozon_data(
                company_obj=company,
                sku=article_search_promo_info.get("sku"),
                ozon_seller_article=article_search_promo_info.get("sourceSku"),
            )

        status = article_search_promo_info.get("searchPromoStatus", False)
        if article_search_promo_info.get("update") is True:
            status = True
        OzonSearchPromo.objects.update_or_create(
            ur_lico=company,
            article=article_obj,
            defaults={
                "bid": article_search_promo_info.get("bid"),
                "bid_price": article_search_promo_info.get("bidPrice"),
                "is_search_promo_available": article_search_promo_info.get(
                    "isSearchPromoAvailable", True
                ),
                "search_promo_status": status,
                "sku": article_search_promo_info.get("sku"),
                "source_sku": article_search_promo_info.get("sourceSku"),
                "visibility_index": article_search_promo_info.get("visibilityIndex"),
            },
        )


class SupportQuery:
    """Вспомогательные запросы для получения информации"""

    def __init__(self):
        self.get_obj = ModelObjectService()
        self.req = OzonAdvertismentApiRequest()

    def product_in_campaign(self, company: Company, campaign_id: str) -> Articles:
        """Продукты в рекламной кампании"""
        header = company.ozon_header
        perfomance_header = company.ozon_perfomance_header
        product_info = self.req.products_in_campaign_req(
            header=header, perfomance_header=perfomance_header, campaign_id=campaign_id
        )
        if isinstance(product_info, dict):
            if product_info.get("list"):
                product = product_info.get("list")[0]
                sku = product.get("id")
                article_obj = self.get_obj.get_article_obj_from_ozon_data(
                    company=company, sku=sku
                )
                return article_obj

    def product_in_trafaret_top_campaign(
        self, company: Company, campaign_id: str
    ) -> Articles:
        """Продукты в рекламной кампании"""
        header = company.ozon_header
        perfomance_header = company.ozon_perfomance_header
        product_info = self.req.products_in_trafaret_top_campaign_req(
            header=header, perfomance_header=perfomance_header, campaign_id=campaign_id
        )
        if isinstance(product_info, dict):
            if product_info.get("products"):
                product = product_info.get("products")[0]
                sku = product.get("sku")
                article_obj = self.get_obj.get_article_obj_from_ozon_data(
                    company=company, sku=sku
                )
                return article_obj

    def product_in_search_promo(self, company: Company) -> Articles:
        """Продукты в рекламной кампании"""
        header = company.ozon_header
        perfomance_header = company.ozon_perfomance_header
        product_info = self.req.products_in_search_promo_campaign_req(
            header=header, perfomance_header=perfomance_header
        )
        if isinstance(product_info, dict):
            if product_info.get("products"):
                product = product_info.get("products")[0]
                sku = product.get("sku")
                article_obj = self.get_obj.get_article_obj_from_ozon_data(
                    company=company, sku=sku
                )
                return article_obj
