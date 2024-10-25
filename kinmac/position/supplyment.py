from datetime import datetime
import urllib.parse
from api_requests.wb_requests import get_article_position, get_campaign_statistic, get_stock_from_webpage_api
from database.models import Articles
from position.models import ArticlePosition, CityData


def article_position_in_search(wb_article, keyword, dest, page=1):
    position = ''
    coder_keyword = urllib.parse.quote(keyword)
    print('coder_keyword', coder_keyword)
    data = get_article_position(coder_keyword, page, dest)
    in_advert = False
    cmp = None
    position_before_adv = None
    print('data', data)
    for position_numb, page_data in enumerate(data['data']['products']):
        if page_data['id'] == wb_article:
            position = position_numb + 1 + ((page-1) * 100)
            if 'log' in page_data:
                if 'cpm' in page_data['log']:
                    in_advert = True
                    cmp = page_data['log']['cpm']
                    position_before_adv = page_data['log']['position']
            return {'position': position,
                    'in_advert': in_advert,
                    'cmp': cmp,
                    'position_before_adv': position_before_adv}
    if not position and page < 10:
        page += 1
        return article_position_in_search(wb_article, keyword, dest, page)

def add_article_for_find_position(wb_article, key_word):
    """Добавляет Артикул в таблицу для поиска позиций"""
    seller_article = ''
    position = None
    in_advert=None
    cmp=None
    position_before_adv=None
    if Articles.objects.filter(nomenclatura_wb=wb_article).exists():
        seller_article = Articles.objects.filter(nomenclatura_wb=wb_article).first().common_article
    about_article = get_stock_from_webpage_api(wb_article)
    if about_article:
        article_data = about_article['data']['products'][0]
        name = article_data['name']
        brand = article_data['brand']
    
    for citydata_obj in CityData.objects.all():
        position_data = article_position_in_search(wb_article, key_word, citydata_obj.dest)
        if position_data:
            position = position_data['position']
            in_advert = position_data.get('in_advert', None)
            cmp = position_data.get('cmp', None)
            position_before_adv = position_data.get('position_before_adv', None)
        if not ArticlePosition.objects.filter(
            wb_article=wb_article,
            key_word=key_word,
            district_position=citydata_obj,
            create_time=datetime.now()).exists():
            ArticlePosition(
                wb_article=wb_article,
                key_word=key_word,
                name=name,
                seller_article=seller_article,
                brand=brand,
                position=position,
                district_position=citydata_obj,
                in_advert=in_advert,
                cmp=cmp,
                position_before_adv=position_before_adv
            ).save()
        else:
            ArticlePosition.objects.filter(
                wb_article=wb_article,
                key_word=key_word,
                district_position=citydata_obj,
                create_time=datetime.now()).update(
                name=name,
                brand=brand,
                position=position,
                in_advert=in_advert,
                cmp=cmp,
                position_before_adv=position_before_adv
            )

    