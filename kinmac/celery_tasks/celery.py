import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kinmac.settings')
app = Celery('celery_tasks',
             include=['celery_tasks.tasks',
                      'action.periodic_tasks',
                      'database.periodic_tasks',
                      'sales_analytics.periodic_tasks',
                      'position.periodic_tasks',
                      'reklama.periodic_tasks',
                      'unit_economic.periodic_tasks',])
app.config_from_object('celery_tasks.celeryconfig')


app.conf.beat_schedule = {
    "check_token_life": {
        "task": "celery_tasks.tasks.check_wb_toket_expire",
        "schedule": crontab(hour=10, minute=1)
    },
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
        "schedule": crontab(hour=23, minute=1)
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
        "schedule": crontab(hour=13, minute=58)
    },
    "add_stock_data_site4": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=19, minute=1)
    },
    "database_update_articles": {
        "task": "database.periodic_tasks.update_info_about_articles",
        "schedule": crontab(hour=22, minute=1)
    },
    "database_update_storagecost": {
        "task": "database.periodic_tasks.calculate_storage_cost",
        "schedule": crontab(hour=22, minute=12)
    },
    # "sales_analytics_article_analytic_update": {
    #     "task": "sales_analytics.periodic_tasks.articles_analytics_data",
    #     "schedule": crontab(hour=22, minute=1)
    # },
    "sales_analytics_common_update": {
        "task": "sales_analytics.periodic_tasks.commom_analytics_data",
        "schedule": crontab(hour=23, minute=58)
    },

    "reklama_update_adv_list": {
        "task": "reklama.periodic_tasks.campaign_list_to_db",
        "schedule": crontab(hour=23, minute=30)
    },
    "reklama_update_article_costs": {
        "task": "reklama.periodic_tasks.update_daily_article_adv_cost",
        "schedule": crontab(hour=23, minute=40)
    },

    "reklama_daily_statistic": {
        "task": "reklama.periodic_tasks.write_daily_adv_statistic",
        "schedule": crontab(hour=23, minute=50)
    },

    # ========== ПОЗИЦИЯ ТОВАРА В ВЫДАЧЕ ========== #
    "position_articles_in_search": {
        "task": "position.periodic_tasks.article_position_task",
        "schedule": crontab(hour='9,15,21', minute=0)
    },
    # ========== КОНЕЦ ПОЗИЦИЯ ТОВАРА В ВЫДАЧЕ ========== #

    # ========== UNIT_ECONOMICS ========== #
    "tariffs_and_logistic": {
        "task": "unit_economic.periodic_tasks.update_tariffs_and_logistic",
        "schedule": crontab(hour=6, minute=2)
    },
    # ========== КОНЕЦ UNIT_ECONOMICS ========== #

    # ========== ACTIONS ========== #
    "actions_new_actions": {
        "task": "action.periodic_tasks.add_new_actions_wb_to_db",
        "schedule": crontab(hour=12, minute=50)
    },
    "actions_article_in_actions": {
        "task": "action.periodic_tasks.add_article_in_actions_info",
        "schedule": crontab(hour=13, minute=0)
    },
    # ========== КОНЕЦ ACTIONS ========== #


}
