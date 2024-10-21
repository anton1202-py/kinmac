import urllib.parse
from api_requests.wb_requests import get_article_position, get_campaign_statistic


def article_position_in_search(wb_article, keyword, page=1):
    position = ''
    print('keyword', keyword)
    coder_keyword = urllib.parse.quote(keyword)
    print('coder_keyword', coder_keyword)
    data = get_article_position(coder_keyword, page)
    for position_numb, page_data in enumerate(data['data']['products']):
        if page_data['id'] == wb_article:
            print("page_data['id'] == wb_article", page_data['id'], wb_article)
            position = position_numb + 1 + ((page-1) * 100)
            return position
    print('position, page', position, page)
    if not position and page < 10:
        page += 1
        return article_position_in_search(wb_article, keyword, page)
    
   