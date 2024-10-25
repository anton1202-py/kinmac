from datetime import datetime, timedelta
from django.shortcuts import redirect, render
from position.periodic_tasks import article_position_task
from position.supplyment import add_article_for_find_position

from .models import ArticlePosition

def article_position(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    article_position_task()
    page_name = 'Позиция артикулов по запросам'
    show_period = datetime.now() - timedelta(days=7)
    data = ArticlePosition.objects.filter(create_time__gte=show_period)

    if request.POST:
        wb_article = request.POST.get('wb_article', '')
        key_word = request.POST.get('key_word', '')
        datestart = request.POST.get('datestart', '')
        datefinish = request.POST.get('datefinish', '')
        article_filter = request.POST.get('article_filter', '')
        
        if key_word and wb_article:
            add_article_for_find_position(int(wb_article), key_word)
        if datestart:
            data = data.filter(create_time__gte=datestart)
        if datefinish:
            data = data.filter(create_time__lte=datefinish)
        if article_filter:
            if ArticlePosition.objects.filter(seller_article=article_filter).exists():
                data = data.filter(seller_article=article_filter)
            else:
                data = data.filter(wb_article=int(article_filter))
    context = {
        'page_name': page_name,
        'data': data,
    }
    return render(request, 'position/article_position.html', context)

