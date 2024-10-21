from django.urls import path

from . import views

urlpatterns = [
    path('article_position', views.article_position, name='article_position'),
]