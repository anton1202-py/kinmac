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
    """Обновляет данные о комиссиях товаров для Озон"""
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
