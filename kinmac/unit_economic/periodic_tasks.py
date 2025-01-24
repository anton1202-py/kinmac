from celery_tasks.celery import app

from database.models import Company
from api_requests.ozon_requests import OzonPriceComissionApiRequest
from unit_economic.servise.ozon_serv import OzonComissionsPriceHandler
from unit_economic.wb_tasks import (
    wb_comission_add_to_db,
    wb_logistic_add_to_db,
)


@app.task()
def update_tariffs_and_logistic():
    """Обновляет данные о продуктах c Wildberries"""
    wb_comission_add_to_db()
    wb_logistic_add_to_db()


@app.task()
def update_ozon_tariffs_and_logistic():
    """Обновляет данные о комиссиях товаров для Озон
    {
            "acquiring": 376.6,
            "offer_id": "santa/pudrovij",
            "product_id": 26965030,
            "volume_weight": 64,
            "commissions": {
                "fbo_deliv_to_customer_amount": 500,
                "fbo_direct_flow_trans_max_amount": 2929.5,
                "fbo_direct_flow_trans_min_amount": 976.5,
                "fbo_return_flow_amount": 1953,
                "fbs_deliv_to_customer_amount": 500,
                "fbs_direct_flow_trans_min_amount": 2344,
                "fbs_direct_flow_trans_max_amount": 2344,
                "fbs_first_mile_max_amount": 30,
                "fbs_first_mile_min_amount": 5,
                "fbs_return_flow_amount": 2344,
                "sales_percent_fbo": 10,
                "sales_percent_fbs": 15
            },
            "marketing_actions": {
                "current_period_from": null,
                "current_period_to": null,
                "actions": [
                    {
                        "title": "Системная виртуальная скидка селлера",
                        "value": 6100,
                        "date_from": "2017-12-31T21:00:00Z",
                        "date_to": "9999-12-31T20:59:59.997Z"
                    }
                ],
                "ozon_actions_exist": false
            },
            "price": {
                "auto_action_enabled": true,
                "currency_code": "RUB",
                "marketing_price": 26900,
                "marketing_seller_price": 26900,
                "min_price": 18990,
                "old_price": 33000,
                "price": 26900,
                "retail_price": 0,
                "vat": 0.05
            },
            "price_indexes": {
                "external_index_data": {
                    "min_price": 0,
                    "min_price_currency": "RUB",
                    "price_index_value": 0
                },
                "ozon_index_data": {
                    "min_price": 0,
                    "min_price_currency": "RUB",
                    "price_index_value": 0
                },
                "color_index": "WITHOUT_INDEX",
                "self_marketplaces_index_data": {
                    "min_price": 0,
                    "min_price_currency": "RUB",
                    "price_index_value": 0
                }
            }
        },

    """
    tariff_req = OzonPriceComissionApiRequest()
    handler = OzonComissionsPriceHandler()
    for company in Company.objects.all():
        common_data = tariff_req.comission_price_req(
            header=company.ozon_header
        )
        for article_info in common_data:
            # Сохраняет комиссии
            handler.comission_handler(
                company=company, article_info=article_info
            )
            # Сохраняет Цены
            handler.price_handler(company=company, article_info=article_info)
