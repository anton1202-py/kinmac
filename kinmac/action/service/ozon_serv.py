from database.models import Company, Marketplace
from action.models import Action, ArticleForAction
from database.service.service import ModelObjectService
from kinmac.constants_file import (
    event_bot,
    actions_info_users_list,
    TELEGRAM_ADMIN_CHAT_ID,
)


class OzonActionHandler:
    """Обработчик данных акций Озон"""

    def __init__(self):
        self.art_obj = ModelObjectService()

    def actions_save(self, company: Company, actions_raw_data: dict):
        """Сохраняет акции Озон в базу данных"""
        if "result" in actions_raw_data:
            marketplace = Marketplace.objects.filter(name="Ozon").first()
            action_info_list = actions_raw_data["result"]
            # TODO Возможно пондобится в модель добавить
            # поле is_participating:
            # Участвуете вы в этой акции или нет.
            # И по нму фильтровать список акций
            for action_info in action_info_list:
                action, created = Action.objects.update_or_create(
                    company=company,
                    marketplace=marketplace,
                    action_number=action_info["id"],
                    name=action_info["title"],
                    defaults={
                        "date_start": action_info["date_start"],
                        "date_finish": action_info["date_end"],
                        "articles_amount": action_info[
                            "potential_products_count"
                        ],
                        "description": action_info["description"],
                        "action_type": action_info["action_type"],
                    },
                )
                if created:
                    message = (
                        f"Появилась новая акция Озон: "
                        f"{action_info['id']}: {action_info['title']}.\n"
                        f"Дата начала: {action_info['date_start']}.\n"
                        f"Дата завершения {action_info['date_end']}."
                    )
                    for chat_id in actions_info_users_list:
                        try:
                            if chat_id:
                                event_bot.send_message(
                                    chat_id=chat_id, text=message
                                )
                        except Exception as e:
                            text = (
                                f"не удалось отправить сообщение с чатом id: "
                                f"{chat_id}. Текстом {message}. Ошибка: {e}"
                            )
                            event_bot.send_message(
                                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=text
                            )

    def hotsale_actions_save(self, company: Company, actions_raw_data: dict):
        """Сохраняет акции HOT SALE Озон в базу данных"""
        if "result" in actions_raw_data:
            marketplace = Marketplace.objects.filter(name="Ozon").first()
            action_info_list = actions_raw_data["result"]
            # TODO Возможно понадобится в модель
            # добавить поле is_participating:
            # Участвуете вы в этой акции или нет.
            # И по нму фильтровать список акций
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
                if created:
                    message = (
                        f"Появилась новая акция Озон Hotsale: "
                        f"{action_info['hotsale_id']}: "
                        f"{action_info['title']}.\n"
                        f"Дата начала: {action_info['date_start']}.\n"
                        f"Дата завершения {action_info['date_end']}."
                    )
                    for chat_id in actions_info_users_list:
                        try:
                            if chat_id:
                                event_bot.send_message(
                                    chat_id=chat_id, text=message
                                )
                        except Exception as e:
                            text = (
                                f"не удалось отправить сообщение с чатом id: "
                                f"{chat_id}. Текстом {message}. Ошибка: {e}"
                            )
                            event_bot.send_message(
                                chat_id=TELEGRAM_ADMIN_CHAT_ID, text=text
                            )

    def products_for_action(
        self, company: Company, product_raw_data: dict, action: Action
    ):
        """
        Сохраняет товары, которые могут участвовать в акции Озон
        """
        article = self.art_obj.get_article_obj_ozon_with_product_id(
            company=company, product_id=product_raw_data["id"]
        )
        if article:
            action_price = product_raw_data["action_price"]
            current_price = product_raw_data["price"]
            discount = (
                (1 - action_price / current_price) * 100
                if current_price != 0
                else 0
            )
            try:
                ArticleForAction.objects.update_or_create(
                    action=action,
                    ozon_article=article,
                    defaults={
                        "action_price": product_raw_data["action_price"],
                        "current_price": product_raw_data["price"],
                        "discount": discount,
                    },
                )
            except Exception as e:
                print(e)

    def products_for_hotsale_action(
        self, company: Company, product_raw_data: dict, action: Action
    ):
        """
        Сохраняет товары, которые могут участвовать в акции Hot Sale Озон
        """
        article = self.art_obj.get_article_obj_ozon_with_product_id(
            company=company, product_id=product_raw_data["id"]
        )
        if article:
            action_price = product_raw_data["action_price"]
            current_price = article.price
            discount = (
                (1 - action_price / current_price) * 100
                if current_price != 0
                else 0
            )
            ArticleForAction.objects.update_or_create(
                action=action,
                ozon_article=article,
                defaults={
                    "action_price": product_raw_data["action_price"],
                    "current_price": article.price,
                    "discount": discount,
                },
            )
