from datetime import datetime, timedelta
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.shortcuts import redirect, render
from database.models import Articles
from position.periodic_tasks import article_position_task
from position.supplyment import add_article_for_find_position

from .models import ArticlePosition

def article_position(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('login')
    page_name = 'Позиция артикулов по запросам'
    show_period = datetime.now() - timedelta(days=1)
    data = ArticlePosition.objects.filter(create_time__gte=show_period)

    if request.POST:
        wb_article = request.POST.get('wb_article', '')
        key_word = request.POST.get('key_word', '')
        datestart = request.POST.get('datestart', '')
        datefinish = request.POST.get('datefinish', '')
        article_filter = request.POST.get('article_filter', '')
        data = ArticlePosition.objects.all()
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
    data = data.order_by('-create_time')
    context = {
        'page_name': page_name,
        'data': data,
    }
    return render(request, 'position/article_position.html', context)


class ArticlePositionDetailView(ListView):
    model = ArticlePosition
    template_name = 'position/one_article_position.html'
    context_object_name = 'articles'

    def get_context_data(self, **kwargs):
        context = super(ArticlePositionDetailView,
                        self).get_context_data(**kwargs)
        article_name = self.kwargs['wb_article']
        if Articles.objects.filter(nomenclatura_wb=article_name).exists():
            article_name = Articles.objects.filter(nomenclatura_wb=article_name).first()
        page_name = f'Позиция артикула {article_name}'
        show_period = datetime.now() - timedelta(days=7)
        data = ArticlePosition.objects.filter(
            wb_article=self.kwargs['wb_article'],
            create_time__gte=show_period
        ).order_by('-create_time')
        
        context.update({
            'data': data,
            'page_name': page_name,
        })
        return context

    def get_queryset(self):
        return ArticlePosition.objects.filter(
            wb_article=self.kwargs['wb_article'])