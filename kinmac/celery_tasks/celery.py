from celery import Celery
from celery.schedules import crontab


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
        "schedule": crontab(hour=6, minute=30)
    },
    "add_stock_data_site": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=1, minute=0)
    },
    "add_stock_data_site": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=7, minute=0)
    },
    "add_stock_data_site": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=13, minute=0)
    },
    "add_stock_data_site": {
        "task": "celery_tasks.tasks.add_stock_data_site",
        "schedule": crontab(hour=19, minute=0)
    },
}

