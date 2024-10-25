from django.urls import path

from . import views

urlpatterns = [
    path('article_position', views.article_position, name='article_position'),
    path('article_position/<int:wb_article>',
          views.ArticlePositionDetailView.as_view(), name='one_article_position'),
]