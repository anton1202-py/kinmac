from django.db import models

from database.models import Articles

class ArticlePosition(models.Model):
    """Описывает Позицию артикула по ключевому запросу"""
    wb_article = models.IntegerField(
        verbose_name='Номенклатура ВБ'
    )
    seller_article = models.CharField(
        verbose_name='Артикул продавца',
        max_length=255,
        null=True,
        blank=True
    )
    name = key_word = models.CharField(
        verbose_name='Название',
        max_length=255,
        null=True,
        blank=True
    )
    brand = key_word = models.CharField(
        verbose_name='Ключевой запрос',
        max_length=255,
        null=True,
        blank=True
    )
    key_word = models.TextField(
        verbose_name='Ключевой запрос'
    )
    position = models.IntegerField(
        verbose_name='Позиция по запросу',
        null=True,
        blank=True
    )
    create_time = models.DateTimeField(
        verbose_name='Дата создания кампании',
        auto_now=True
    )
    
    class Meta:
        verbose_name = 'Позиция артикула по запросу'
        verbose_name_plural = 'Позиция артикула по запросу'




