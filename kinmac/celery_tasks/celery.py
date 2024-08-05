import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kinmac.settings')
app = Celery('celery_tasks',
             include=['celery_tasks.tasks'])
app.config_from_object('celery_tasks.celeryconfig')


app.conf.beat_schedule = {
    "add_data_stock_api": {
        "task": "celery_tasks.tasks.add_data_stock_api",
        "schedule": crontab(hour=6, minute=0)
    },
    "add_data_sales": {
        "task": "celery_tasks.tasks.add_data_sales",
        "schedule": crontab(hour=6, minute=13)
    },
    "add_data_deliveries": {
        "task": "celery_tasks.tasks.delivery_statistic",
        "schedule": crontab(hour=6, minute=15)
    },
    "add_data_orders": {
        "task": "celery_tasks.tasks.orders_statistic",
        "schedule": crontab(hour=6, minute=17)
    },
    "add_data_reports": {
        "task": "celery_tasks.tasks.sales_report_statistic",
        "schedule": crontab(hour=11, minute=17)
    },
    "add_stock_data_site1": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=1, minute=0)
    },
    "add_stock_data_site2": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=7, minute=0)
    },
    "add_stock_data_site3": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=13, minute=0)
    },
    "add_stock_data_site4": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=19, minute=0)
    },
}
