from collections import defaultdict
from datetime import datetime, timedelta
import time
from api_requests.wb_requests import (
    get_adv_campaign_lists_data,
    get_adv_info,
    get_campaign_statistic,
)
from celery_tasks.celery import app


from api_requests.ozon_requests import OzonAdvertismentApiRequest
from kinmac.constants_file import TELEGRAM_ADMIN_CHAT_ID, wb_headers, bot
from database.models import Company
from reklama.services.ozon_serv import OzonAdvCampaignAndProducts
from reklama.supplyment import get_daily_adv_statistic

from .models import (
    ArticleDailyCostToAdv,
    Articles,
    CampaignDailyAdvStatistic,
    ReklamaCampaign,
)

WORKING_CAMPAIGN_STATUSES = [4, 9, 11]
WORKING_CAMPAIGN_TYPES = [8, 9]


@app.task
def campaign_list_to_db():
    """
    Добавляет в базу данных новые рекламные кампании
    Обновляет статус текущих кампаний
    """

    main_campaigns_data = get_adv_campaign_lists_data(wb_headers)
    new_campigns_dict = {}
    if main_campaigns_data:
        for data in main_campaigns_data["adverts"]:
            if (
                data["status"] in WORKING_CAMPAIGN_STATUSES
                and data["type"] in WORKING_CAMPAIGN_TYPES
            ):
                for advert in data["advert_list"]:
                    if not ReklamaCampaign.objects.filter(
                        campaign=advert["advertId"]
                    ).exists():
                        new_campigns_dict[advert["advertId"]] = {
                            "type": data["type"],
                            "status": data["status"],
                        }
    if new_campigns_dict:
        campaign_list = []
        for campaign, _ in new_campigns_dict.items():
            campaign_list.append(campaign)
        campaigns_data = get_adv_info(wb_headers, campaign_list)
        if campaigns_data:
            for adv_data in campaigns_data:
                create_time = adv_data["createTime"]
                reklama_obj = ReklamaCampaign.objects.create(
                    campaign=adv_data["advertId"],
                    campaign_type=new_campigns_dict[adv_data["advertId"]][
                        "type"
                    ],
                    campaign_status=new_campigns_dict[adv_data["advertId"]][
                        "status"
                    ],
                    create_time=create_time,
                )
                if new_campigns_dict[adv_data["advertId"]]["type"] == 8:
                    articles_data = adv_data["autoParams"]["nms"]
                if new_campigns_dict[adv_data["advertId"]]["type"] == 9:
                    articles_data = adv_data["unitedParams"][0]["nms"]

                for article in articles_data:
                    article_obj = Articles.objects.get(nomenclatura_wb=article)
                    reklama_obj.articles.add(article_obj)


@app.task
def update_daily_article_adv_cost():
    """
    Обновляет расходы на рекламу артикула в базе данных
    """

    # Достаем список всех рекламных кампаний.
    campaign_list = ReklamaCampaign.objects.all()
    statistic_date = datetime.now()
    date_from = (statistic_date - timedelta(days=7)).strftime("%Y-%m-%d")

    date_to = statistic_date.strftime("%Y-%m-%d")

    request_campaign_list = []

    for campaign in campaign_list:
        request_campaign_list.append(
            {
                "id": campaign.campaign,
                "interval": {"begin": f"{date_from}", "end": f"{date_to}"},
            }
        )
    statistic_data = get_campaign_statistic(wb_headers, request_campaign_list)
    if statistic_data:
        for data in statistic_data:
            campaign_number = data["advertId"]
            campaign_obj = ReklamaCampaign.objects.get(
                campaign=campaign_number
            )
            for day_statistic in data["days"]:
                articles_daily_statistic = defaultdict(int)
                date = (
                    datetime.fromisoformat(day_statistic["date"])
                    .date()
                    .isoformat()
                )
                for statistic in day_statistic["apps"]:
                    if statistic["appType"] != 0:
                        for article_statistic in statistic["nm"]:
                            article_obj = Articles.objects.get(
                                nomenclatura_wb=article_statistic["nmId"]
                            )
                            cost = article_statistic["sum"]
                            articles_daily_statistic[article_obj] += cost
                for (
                    article_obj,
                    daily_cost,
                ) in articles_daily_statistic.items():
                    if not ArticleDailyCostToAdv.objects.filter(
                        article=article_obj,
                        cost_date=date,
                        campaign=campaign_obj,
                    ).exists():
                        ArticleDailyCostToAdv(
                            article=article_obj,
                            cost_date=date,
                            cost=daily_cost,
                            campaign=campaign_obj,
                        ).save()
                    else:
                        ArticleDailyCostToAdv.objects.filter(
                            article=article_obj,
                            cost_date=date,
                            campaign=campaign_obj,
                        ).update(cost=daily_cost)


@app.task
def write_daily_adv_statistic():
    """
    Записывает в базу данных ежедневную статистику рекламных кампаний
    """
    # Достаю из БД активные РК.
    statistic_data = get_daily_adv_statistic()

    try:
        for data in statistic_data:
            campaign_number = data["advertId"]
            campaign_obj = ReklamaCampaign.objects.get(
                campaign=campaign_number
            )
            for stat in data["days"]:
                request_date = stat["date"]
                date_obj = datetime.fromisoformat(request_date)
                # Форматируем дату в нужный формат
                date = date_obj.strftime("%Y-%m-%d")
                views = stat["views"]
                clicks = stat["clicks"]
                ctr = stat["ctr"]
                cpc = stat["cpc"]
                sum = stat["sum"]
                atbs = stat["atbs"]
                orders = stat["orders"]
                cr = stat["cr"]
                shks = stat["shks"]
                sum_price = stat["sum_price"]
                search_params = {
                    "campaign": campaign_obj,
                    "statistic_date": date,
                }
                defaults = {
                    "views": views,
                    "clicks": clicks,
                    "ctr": ctr,
                    "cpc": cpc,
                    "summ": sum,
                    "atbs": atbs,
                    "orders": orders,
                    "cr": cr,
                    "shks": shks,
                    "sum_price": sum_price,
                }
                CampaignDailyAdvStatistic.objects.update_or_create(
                    defaults=defaults, **search_params
                )
    except Exception:
        message = "Не получил статистику для кампаний на сегодня"
        bot.send_message(chat_id=TELEGRAM_ADMIN_CHAT_ID, text=message[:4000])


@app.task
def add_ozon_adv_campaigns() -> None:
    """Проверяет рекламные кампании и их статус"""
    advert_req = OzonAdvertismentApiRequest()
    adv_handler = OzonAdvCampaignAndProducts()
    company_list = Company.objects.filter(
        ozon_perfomance_client_id__isnull=False
    ).order_by("id")
    for company in company_list:
        if company.ozon_token:
            header = company.ozon_header
            perfomance_header = company.ozon_perfomance_header
            advert_list = advert_req.campaigns_list_req(
                header, perfomance_header
            )
            if advert_list.get("list"):
                for campaign_info in advert_list.get("list"):
                    adv_handler.save_campaigns_to_database(
                        company, campaign_info
                    )


@app.task
def ozon_cost_adv_articles() -> None:
    """Рекламные расходы на артикул (Озон)"""
    advert_req = OzonAdvertismentApiRequest()
    adv_handler = OzonAdvCampaignAndProducts()
    company_list = Company.objects.filter(
        ozon_perfomance_client_id__isnull=False
    ).order_by("id")
    date_now = datetime.now() - timedelta(days=1)
    date_to = date_now.date()
    date_from = (date_now - timedelta(days=10)).date()
    for company in company_list:
        if company.ozon_token:
            header = company.ozon_header
            perfomance_header = company.ozon_perfomance_header

            statistic_data = advert_req.cost_statistic(
                header=header,
                perfomance_header=perfomance_header,
                date_from=date_from,
                date_to=date_to,
            ).get("rows")
            if statistic_data:
                for statistic in statistic_data:
                    adv_handler.article_adv_cost(
                        company=company, statistic=statistic
                    )


@app.task
def ozon_cost_adv_articles_promo_search() -> None:
    """Рекламные расходы артикула на продвижение в поиске (Озон)"""
    advert_req = OzonAdvertismentApiRequest()
    adv_handler = OzonAdvCampaignAndProducts()
    companies = Company.objects.filter(
        ozon_perfomance_client_id__isnull=False
    ).order_by("id")
    date_now = datetime.now() - timedelta(days=1)
    date_to = date_now.date()
    date_from = (date_now - timedelta(days=10)).date()
    for company in companies:
        if company.ozon_token:
            header = company.ozon_header
            perfomance_header = company.ozon_perfomance_header

            report_info = advert_req.search_promo_report(
                header=header,
                perfomance_header=perfomance_header,
                date_from=date_from,
                date_to=date_to,
            )
            report_uuid = report_info.get("UUID")
            if report_uuid:

                status = None
                while status != "OK":
                    time.sleep(50)
                    report_status_info = advert_req.check_report_status(
                        header=header,
                        perfomance_header=perfomance_header,
                        report_uuid=report_uuid,
                    )
                    status = report_status_info.get("state")

                promo_search_cost_data = advert_req.get_report(
                    header=header,
                    perfomance_header=perfomance_header,
                    report_uuid=report_uuid,
                )

                statistic_data = promo_search_cost_data.get("report", {}).get(
                    "rows"
                )
                if statistic_data:
                    adv_handler.promo_search_article_adv_cost(
                        company=company,
                        statistic=statistic_data,
                    )
