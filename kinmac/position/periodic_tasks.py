from datetime import datetime, timedelta
import math
from api_requests.wb_requests import get_adv_campaign_lists_data, get_adv_info, get_campaign_statistic, wb_article_data_from_api
from celery_tasks.celery import app


from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, wb_headers, bot
from position.supplyment import article_position_in_search
from reklama.supplyment import get_daily_adv_statistic

from .models import ArticlePosition


@app.task
def article_position_task():
    """
    Определеяет позицию артикула по запросу
    """
    unique_combinations = ArticlePosition.objects.values('wb_article', 'key_word').distinct()
    # Преобразуем результат в список, если нужно
    unique_combinations_list = list(unique_combinations)
    # Выводим результат
    for data in unique_combinations_list:
        wb_article = data['wb_article']
        keyword = data['key_word']
        article_obj = ArticlePosition.objects.filter(wb_article=wb_article).first()
        art_position = article_position_in_search(wb_article, keyword)
        position = None
        cmp = None
        position_before_adv = None
        if art_position:
            position = art_position['position']
            in_advert = art_position.get('in_advert', None)
            cmp = art_position.get('cmp', None)
            position_before_adv = art_position.get('position_before_adv', None)
        ArticlePosition(
                wb_article=wb_article,
                key_word=keyword,
                create_time=datetime.now(),
                name=article_obj.name,
                brand=article_obj.brand,
                position=position,
                in_advert=in_advert,
                cmp=cmp,
                position_before_adv=position_before_adv


            ).save()