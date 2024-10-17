from datetime import datetime, timedelta
import math
from api_requests.wb_requests import get_adv_campaign_lists_data, get_adv_info, get_campaign_statistic, wb_article_data_from_api
from celery_tasks.celery import app

from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, wb_headers, bot

from .models import ArticleDailyCostToAdv, Articles, ReklamaCampaign


def get_daily_adv_statistic():
    """
    Достает из АПИ рекламы статистику всех кампаний
    """
    # Достаю из БД активные РК.
    campaign_list = ReklamaCampaign.objects.filter(campaign_status__in=[9, 11]).values_list('campaign', flat=True)
    campaign_amount = len(campaign_list)
    checker = math.ceil(campaign_amount / 50)
    statistic_date = datetime.today()
    date_from = (statistic_date - timedelta(days=7)).strftime('%Y-%m-%d')
    date_to = statistic_date.strftime('%Y-%m-%d')
    for_campaign_data = []
    for i in range(checker):
        campaign_statistic = []
        inner_list = campaign_list[i*50:(i+1)*50]
        for campaign_number in inner_list:
            campaign_statistic.append(
                {
                    "id": campaign_number,
                    "interval": {
                        "begin": date_from,
                        "end": date_to
                    }
                }
            )
        # Вызываю АПИ для получении статистики кампаний (до 50 штук)
        statistic_data = get_campaign_statistic(wb_headers, campaign_statistic)
        if statistic_data:
            for data in statistic_data:
              for_campaign_data.append(data)
        else:
            message = f'Не получил статистику для кампаний: {inner_list}'
            bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID,
                         text=message[:4000])
    return for_campaign_data