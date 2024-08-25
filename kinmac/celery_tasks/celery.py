import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kinmac.settings')
app = Celery('celery_tasks',
             include=['celery_tasks.tasks',
                      'database.periodic_tasks',
                      'sales_analytics.periodic_tasks'])
app.config_from_object('celery_tasks.celeryconfig')


app.conf.beat_schedule = {
    "add_data_stock_api": {
        "task": "celery_tasks.tasks.add_data_stock_api",
        "schedule": crontab(hour=15, minute=17)
    },
    "add_data_sales": {
        "task": "celery_tasks.tasks.add_data_sales",
        "schedule": crontab(hour=6, minute=11)
    },
    "add_data_deliveries": {
        "task": "celery_tasks.tasks.delivery_statistic",
        "schedule": crontab(hour=6, minute=17)
    },
    "add_data_orders": {
        "task": "celery_tasks.tasks.orders_statistic",
        "schedule": crontab(hour=6, minute=19)
    },
    "add_data_reports": {
        "task": "celery_tasks.tasks.sales_report_statistic",
        "schedule": crontab(hour=22, minute=1)
    },
    "add_stock_data_site1": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=1, minute=1)
    },
    "add_stock_data_site2": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=7, minute=1)
    },
    "add_stock_data_site3": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=13, minute=1)
    },
    "add_stock_data_site4": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=19, minute=1)
    },
    "database_update_articles": {
        "task": "database.periodic_tasks.update_info_about_articles",
        "schedule": crontab(hour=22, minute=1)
    },
    "sales_analytics_article_analytic_update": {
        "task": "sales_analytics.periodic_tasks.articles_analytics_data",
        "schedule": crontab(hour=16, minute=1)
    },
    "sales_analytics_common_update": {
        "task": "sales_analytics.periodic_tasks.commom_analytics_data",
        "schedule": crontab(hour=18, minute=1)
    },
}
