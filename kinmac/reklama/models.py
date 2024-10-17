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


class CampaignDailyAdvStatistic(models.Model):
    """Ежедневная статистика рекламной кампании за день."""
    campaign = models.ForeignKey(
        ReklamaCampaign,
        verbose_name='Реклмная кампания',
        on_delete=models.SET_NULL,
        related_name='adv_daily_statistic_campaign',
        blank=True,
        null=True,
    )
    # article = models.ForeignKey(
    #     Articles,
    #     verbose_name='Артикул',
    #     on_delete=models.SET_NULL,
    #     related_name='adv_daily_cost_article',
    #     blank=True,
    #     null=True,
    # )
    statistic_date = models.DateField(
        verbose_name='Дата',
        blank=True,
        null=True
    )
    views = models.IntegerField(
        verbose_name='Просмотры',
        blank=True,
        null=True
    )
    clicks = models.IntegerField(
        verbose_name='Клики',
        blank=True,
        null=True
    )
    ctr = models.FloatField(
        verbose_name='CTR. Показатель кликабельности, отношение числа кликов к количеству показов, %',
        blank=True,
        null=True
    )
    cpc = models.FloatField(
        verbose_name='CPC. Средняя стоимость клика, ₽.',
        blank=True,
        null=True
    )
    summ = models.FloatField(
        verbose_name='Затраты, ₽.',
        blank=True,
        null=True
    )
    atbs = models.IntegerField(
        verbose_name='Добавления в корзину',
        blank=True,
        null=True
    )
    orders = models.IntegerField(
        verbose_name='Количество заказов',
        blank=True,
        null=True
    )
    cr = models.IntegerField(
        verbose_name='CR(conversion rate). Отношение количества заказов к общему количеству посещений кампании',
        blank=True,
        null=True
    )
    shks = models.IntegerField(
        verbose_name='Количество заказанных товаров, шт.',
        blank=True,
        null=True
    )
    sum_price = models.FloatField(
        verbose_name='Заказов на сумму, ₽',
        blank=True,
        null=True
    )
    class Meta:
        verbose_name = 'Затраты на рекламу артикула'
        verbose_name_plural = 'Затраты на рекламу артикула'