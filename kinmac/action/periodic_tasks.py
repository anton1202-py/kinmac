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
from kinmac.constants_file import (
    TELEGRAM_ADMIN_CHAT_ID,
    bot,
    wb_headers,
    wb_header_with_lk_cookie,
    actions_info_users_list,
)
from database.models import CodingMarketplaces
from database.models import Articles


@app.task
def add_new_actions_wb_to_db():
    """Добавляет новую акцию ВБ в базу данных"""
    # Получаем информацию по новым акциям
    actions_data = wb_actions_first_list(wb_headers)
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
        actions_details = wb_action_details_info(wb_headers, actions_not_exist_str)
        action_front_info = action_data_from_front()
        if actions_details and "data" in actions_details:
            for detail in actions_details["data"]["promotions"]:
                # Получаем инормацию по артикулам, которые могут участвовать в акции
                article_action_data = wb_articles_in_action(wb_headers, detail["id"])
                articles_amount = 0
                if article_action_data:
                    # Смотрим кол-во артикулов, которые могут участвовать в акции
                    articles_amount = len(article_action_data)
                # Сохраняем новую акцию в базу
                search_params = {
                    "marketplace": CodingMarketplaces.objects.get(name="Wildberries"),
                    "action_number": detail["id"],
                }
                values_for_update = {
                    "name": detail["name"],
                    "period": (
                        action_front_info[detail["id"]] if action_front_info else None
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
    actions = Action.objects.filter(date_finish__gt=datetime.now())
    for action_obj in actions:
        # Получаем инормацию по артикулам, которые могут участвовать в акции
        if action_obj.action_type != "auto":
            article_action_data = wb_articles_in_action(
                wb_headers, action_obj.action_number
            )
        else:
            article_action_data = get_excel_data_from_front(
                action_obj.action_number, action_obj.period
            )
        # Сохраняем артикулы, которые могут участвовать в акции
        add_article_may_be_in_action(article_action_data, action_obj)
