from django.db import models

from database.models import Articles

class ReklamaCampaign(models.Model):
    """Описывает рекламныю кампанию"""
    campaign = models.IntegerField(
        verbose_name='Номер кампании'
    )
    campaign_type = models.IntegerField(
        verbose_name='Тип кампании'
    )
    campaign_status = models.IntegerField(
        verbose_name='Статус кампании'
    )
    create_time = models.DateTimeField(
        verbose_name='Дата создания кампании'
    )
    end_time = models.DateTimeField(
        verbose_name='Дата завершения кампании',
        blank=True,
        null=True,
    )
    articles = models.ManyToManyField(
        Articles,
        verbose_name='Артикулы',
        related_name='adv_campaigns',
        blank=True,
    )

    class Meta:
        verbose_name = 'Рекламная кампания на ВБ'
        verbose_name_plural = 'Рекламная кампания на ВБ'


class ArticleDailyCostToAdv(models.Model):
    """Затраты на рекламу одного артикула в день"""
    article = models.ForeignKey(
        Articles,
        verbose_name='Артикул',
        on_delete=models.SET_NULL,
        related_name='adv_daily_cost_article',
        blank=True,
        null=True,
    )
    cost_date = models.DateField(
        verbose_name='Дата затраты'
    )
    campaign = models.ForeignKey(
        ReklamaCampaign,
        verbose_name='Реклмная кампания',
        on_delete=models.SET_NULL,
        related_name='adv_daily_cost_campaign',
        blank=True,
        null=True,
    )
    cost = models.FloatField(
        verbose_name='Затраты'
    )
    class Meta:
        verbose_name = 'Затраты на рекламу артикула'
        verbose_name_plural = 'Затраты на рекламу артикула'