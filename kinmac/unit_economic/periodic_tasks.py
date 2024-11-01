from celery_tasks.celery import app

from unit_economic.wb_tasks import wb_comission_add_to_db, wb_logistic_add_to_db


@app.task()
def update_tariffs_and_logistic():
    """Обновляет данные о продуктах c Wildberries"""
    wb_comission_add_to_db()
    wb_logistic_add_to_db()