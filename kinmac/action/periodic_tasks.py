from datetime import datetime
from django.utils import timezone
from api_requests.wb_requests import (
    wb_action_details_info,
    wb_actions_first_list,
    wb_articles_in_action,
)
from celery_tasks.celery import app

from action.models import Action, ArticleForAction
from action.supplyment import (
    action_data_from_front,
    add_article_may_be_in_action,
    get_excel_data_from_front,
)
from api_requests.ozon_requests import ActionRequest
from action.service.ozon_serv import OzonActionHandler
from kinmac.constants_file import (
    TELEGRAM_ADMIN_CHAT_ID,
    bot,
    wb_headers,
    wb_header_with_lk_cookie,
    actions_info_users_list,
)
from database.models import Company, Marketplace
from database.models import Articles


@app.task
def add_new_actions_wb_to_db():
    """Добавляет новую акцию ВБ в базу данных"""
    # Получаем информацию по новым акциям
    for company in Company.objects.all():
        actions_data = wb_actions_first_list(company.wb_header)
        actions_not_exist_str = ""
        if actions_data:
            actions_info = actions_data["data"]["promotions"]
            for action in actions_info:
                # if not Action.objects.filter(action_number=action['id']).exists():
                # message = (f"{action['id']}: {action['name']}.\n"
                #             f"Дата начала: {datetime.strptime(action['startDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.\n"
                #             f"Дата завершения {datetime.strptime(action['endDateTime'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d')}.")
                # for chat_id in actions_info_users_list:
                #     bot.send_message(chat_id=chat_id,
                #          text=message)
                actions_not_exist_str += f"promotionIDs={action['id']}&"
        if actions_not_exist_str:
            # Получаем детальную информацию по новым акциям
            actions_details = wb_action_details_info(
                company.wb_header, actions_not_exist_str
            )
            action_front_info = action_data_from_front(
                company.wb_cookie_header
            )
            if actions_details and "data" in actions_details:
                for detail in actions_details["data"]["promotions"]:
                    # Получаем инормацию по артикулам, которые могут участвовать в акции
                    article_action_data = wb_articles_in_action(
                        company.wb_header, detail["id"]
                    )
                    articles_amount = 0
                    if article_action_data:
                        # Смотрим кол-во артикулов, которые могут участвовать в акции
                        articles_amount = len(article_action_data)
                    # Сохраняем новую акцию в базу
                    search_params = {
                        "marketplace": Marketplace.objects.get(
                            name="Wildberries"
                        ),
                        "action_number": detail["id"],
                    }
                    values_for_update = {
                        "name": detail["name"],
                        "period": (
                            action_front_info[detail["id"]]
                            if action_front_info
                            else None
                        ),
                        "description": detail["description"],
                        "date_start": detail["startDateTime"],
                        "action_type": detail["type"],
                        "date_finish": detail["endDateTime"],
                        "articles_amount": articles_amount,
                    }
                    Action.objects.update_or_create(
                        defaults=values_for_update, **search_params
                    )


@app.task
def add_article_in_actions_info():
    """Добавляет в базу информацию по артикулам в акции"""
    # Получаем информацию по новым акциям
    for company in Company.objects.all():
        actions = Action.objects.filter(
            marketplace=Marketplace.objects.get(name="Wildberries"),
            date_finish__gt=datetime.now(),
        )
        for action_obj in actions:
            # Получаем инормацию по артикулам, которые могут участвовать в акции
            if action_obj.action_type != "auto":
                article_action_data = wb_articles_in_action(
                    company.wb_header, action_obj.action_number
                )
            else:
                article_action_data = get_excel_data_from_front(
                    wb_cookie_header=company.wb_cookie_header,
                    action_number=action_obj.action_number,
                    action_period=action_obj.period,
                )
            # Сохраняем артикулы, которые могут участвовать в акции
            add_article_may_be_in_action(article_action_data, action_obj)


@app.task
def add_new_actions_ozon_to_db():
    """Добавляет новую акцию Озон в базу данных"""
    # Получаем информацию по новым акциям
    action_req = ActionRequest()
    action_handler = OzonActionHandler

    for company in Company.objects.all():
        header = company.ozon_header
        actions_raw_data = action_req.actions_list(header)
        action_handler.actions_save(
            company=company, actions_raw_data=actions_raw_data
        )

        hot_sale_actions_raw_data = action_req.hotsale_actions_list(header)
        action_handler.hotsale_actions_save(company, hot_sale_actions_raw_data)


@app.task
def products_in_action_ozon():
    """Сохраняет товары, которые могут участвовать в акциях Озон"""
    # Получаем информацию по новым акциям
    action_req = ActionRequest()
    action_handler = OzonActionHandler()
    marketplace = Marketplace.objects.filter(name="Ozon").first()

    for company in Company.objects.all():
        actions = Action.objects.filter(
            company=company,
            marketplace=marketplace,
            date_finish__gte=datetime.now(),
        ).exclude(action_type="hotsale")
        header = company.ozon_header
        for action in actions:
            products_list = action_req.access_products_for_action(
                header, int(action.action_number)
            )
            if products_list:
                for product_raw_data in products_list:
                    action_handler.products_for_action(
                        company, product_raw_data, action
                    )
        hotsale_actions = Action.objects.filter(
            company=company,
            marketplace=marketplace,
            date_finish__gte=datetime.now(),
            action_type="hotsale",
        )

        for action in hotsale_actions:
            products_list = action_req.products_in_hotsale(
                header, int(action.action_number)
            )
            if products_list:
                for product_raw_data in products_list:
                    action_handler.products_for_hotsale_action(
                        company, product_raw_data, action
                    )
