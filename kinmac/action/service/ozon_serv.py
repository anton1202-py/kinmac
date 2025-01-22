from database.models import Company, Marketplace
from action.models import Action, ArticleForAction
from database.service.service import ModelObjectService


class OzonActionHandler:
    """Обработчик данных акций Озон"""

    def __init__(self):
        self.art_obj = ModelObjectService()

    def actions_save(self, company: Company, actions_raw_data: dict):
        """Сохраняет акции Озон в базу данных"""
        if "result" in actions_raw_data:
            marketplace = Marketplace.objects.filter(name="Ozon").first()
            action_info_list = actions_raw_data["result"]
            # TODO Возможно пондобится в модель добавить поле is_participating:
            # Участвуете вы в этой акции или нет. И по нму фильтровать список акций
            for action_info in action_info_list:
                action, created = Action.objects.update_or_create(
                    company=company,
                    marketplace=marketplace,
                    action_number=action_info["id"],
                    name=action_info["title"],
                    defaults={
                        "date_start": action_info["date_start"],
                        "date_finish": action_info["date_end"],
                        "articles_amount": action_info["potential_products_count"],
                        "description": action_info["description"],
                        "action_type": action_info["action_type"],
                    },
                )

    def hotsale_actions_save(self, company: Company, actions_raw_data: dict):
        """Сохраняет акции HOT SALE Озон в базу данных"""
        if "result" in actions_raw_data:
            marketplace = Marketplace.objects.filter(name="Ozon").first()
            action_info_list = actions_raw_data["result"]
            # TODO Возможно пондобится в модель добавить поле is_participating:
            # Участвуете вы в этой акции или нет. И по нму фильтровать список акций
            for action_info in action_info_list:
                action, created = Action.objects.update_or_create(
                    company=company,
                    marketplace=marketplace,
                    action_number=action_info["hotsale_id"],
                    name=action_info["title"],
                    defaults={
                        "date_start": action_info["date_start"],
                        "date_finish": action_info["date_end"],
                        "description": action_info["description"],
                        "action_type": "hotsale",
                    },
                )

    def products_for_action(
        self, company: Company, product_raw_data: dict, action: Action
    ):
        """Сохраняет товары, которые могут участвовать в акции Озон
        {
            "id": 226,
            "price": 250,
            "action_price": 0,
            "max_action_price": 175,
            "add_mode": "NOT_SET",
            "stock": 0,
            "min_stock": 0
        }
        """
        article = self.art_obj.get_article_obj_ozon_with_product_id(
            company=company, product_id=product_raw_data["id"]
        )
        ArticleForAction.objects.update_or_create(
            action=action,
            article=article,
            in_action=None,
            action_price=None,
            current_price=None,
            discount=None,
            plan_discount=None,
            defaults={
                "date_start": product_raw_data["date_start"],
                "date_finish": product_raw_data["date_end"],
                "articles_amount": product_raw_data["potential_products_count"],
                "description": product_raw_data["description"],
                "action_type": product_raw_data["action_type"],
            },
        )
