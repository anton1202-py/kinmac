import base64
from io import BytesIO
from datetime import datetime, timedelta

import pandas as pd
from api_requests.wb_requests import (
    create_excel_file_with_article_in_auto_actions,
    take_excel_file_data_in_auto_actions,
    wb_action_info_from_front,
)
from action.models import ArticleForAction
from database.models import Articles
from kinmac.constants_file import wb_header_with_lk_cookie


def add_article_may_be_in_action(article_action_data, action_obj):
    """Описывает артикулы, которые могут быть в акции"""
    if article_action_data:
        for_create_list = []
        for data in article_action_data:
            if Articles.objects.filter(nomenclatura_wb=data["id"]).exists():
                article_obj = Articles.objects.get(nomenclatura_wb=data["id"])
                if ArticleForAction.objects.filter(
                    action=action_obj, article=article_obj
                ).exists():
                    ArticleForAction.objects.filter(
                        action=action_obj, article=article_obj
                    ).update(
                        action_price=data["planPrice"],
                        plan_discount=data["planDiscount"],
                    )
                else:
                    maybe_obj = ArticleForAction(
                        action=action_obj,
                        article=article_obj,
                        in_action=data["inAction"],
                        action_price=data["planPrice"],
                        current_price=data["price"],
                        discount=data["discount"],
                        plan_discount=data["planDiscount"],
                    )
                    for_create_list.append(maybe_obj)
        if for_create_list:
            ArticleForAction.objects.bulk_create(for_create_list)


def get_excel_data_from_front(wb_cookie_header, action_number, action_period):
    """Получаем данные из Excel файла с фронта ВБ"""
    # Запускаем формирование Excel файла с ценами на артикул.
    create_excel_file_with_article_in_auto_actions(wb_cookie_header, action_period)
    # Получаем зашифрованный excel файл
    excel_data = take_excel_file_data_in_auto_actions(
        wb_cookie_header, action_number, action_period
    )
    if excel_data:
        decoded_data = base64.b64decode(excel_data["data"]["file"])
        excel_file = BytesIO(decoded_data)
        read_excel_file = pd.read_excel(excel_file)
        excel_data = pd.DataFrame(
            read_excel_file,
            columns=[
                "Артикул поставщика",
                "Артикул WB",
                "Плановая цена для акции",
                "Текущая розничная цена",
                "Текущая скидка на сайте, %",
                "Загружаемая скидка для участия в акции",
                "Товар уже участвует в акции",
            ],
        )
        wb_article_list = excel_data["Артикул WB"].to_list()
        action_price_list = excel_data["Плановая цена для акции"].to_list()
        current_price_without_discount_list = excel_data[
            "Текущая розничная цена"
        ].to_list()
        current_discount_list = excel_data["Текущая скидка на сайте, %"].to_list()
        action_discount_list = excel_data[
            "Загружаемая скидка для участия в акции"
        ].to_list()
        in_action_list = excel_data["Товар уже участвует в акции"].to_list()
        articles_action_data = []
        for i, article in enumerate(wb_article_list):
            # print('article', article)
            if Articles.objects.filter(nomenclatura_wb=article).exists():
                inner_dict = {}
                # article_obj = Articles.objects.filter(
                #     nomenclatura_wbe=article).first()
                action_price = action_price_list[i]
                current_seller_price = current_price_without_discount_list[i] * (
                    1 - current_discount_list[i] / 100
                )
                action_discount = (
                    (current_seller_price - action_price) / current_seller_price * 100
                )
                action_discount_from_wb = action_discount_list[i]
                articles_action_data.append(
                    {
                        "id": article,
                        "inAction": True if in_action_list[i] == "Да" else False,
                        "planPrice": action_price_list[i],
                        "price": current_price_without_discount_list[i],
                        "discount": current_discount_list[i],
                        "planDiscount": action_discount_list[i],
                    }
                )
        return articles_action_data


def action_data_from_front(wb_cookie_header):
    """
    Получает данные об акциях с фронта и возвращает словарь
    типа: {action_id: period}
    """
    date_from = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    returned_dict = {}
    action_data = wb_action_info_from_front(wb_cookie_header, date_from, date_to)
    if action_data:
        for data in action_data["data"]:
            returned_dict[data["actionID"]] = data["periodID"]

    return returned_dict
