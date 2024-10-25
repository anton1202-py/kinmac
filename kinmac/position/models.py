from django.db import models

from database.models import Articles


class CityData(models.Model):
    """Описывает город и его dest для поиска позиции"""
    city_name = models.CharField(
        verbose_name='Название района для определения позиции',
        max_length=255,
        null=True,
        blank=True
    )
    dest = models.IntegerField(
        verbose_name='Координаты района',
        null=True,
        blank=True
    )
    class Meta:
        verbose_name = 'Город (район) для определения позиции'
        verbose_name_plural = 'Город (район) для определения позиции'


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
    brand = models.CharField(
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
    district_position = models.ForeignKey(
        CityData, 
        verbose_name='Район',
        on_delete=models.SET_NULL,
        related_name='article_position_city',
        blank=True,
        null=True,
    )
    create_time = models.DateTimeField(
        verbose_name='Дата создания кампании',
        auto_now=True
    )
    in_advert = models.BooleanField(
        verbose_name='Участвует в рекламе',
        null=True,
        blank=True
    )
    cmp = models.IntegerField(
        verbose_name='CPM в рекламе',
        null=True,
        blank=True
    )
    position_before_adv = models.IntegerField(
        verbose_name='Позиция до рекламы',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Позиция артикула по запросу'
        verbose_name_plural = 'Позиция артикула по запросу'


