from django.db import models
from database.models import Marketplace
from database.models import Articles


class Action(models.Model):
    """Описывает акцию на маркетплейсе"""

    marketplace = models.ForeignKey(
        Marketplace,
        on_delete=models.SET_NULL,
        verbose_name="Маркетплейс",
        related_name="actions",
        blank=True,
        null=True,
    )
    action_number = models.CharField(verbose_name="Номер акции", max_length=100)
    name = models.CharField(verbose_name="Название акции", max_length=255)
    description = models.TextField(verbose_name="Описание акции")
    date_start = models.DateTimeField(verbose_name="Дата начала акции")
    date_finish = models.DateTimeField(verbose_name="Дата завершения акции")
    action_type = models.CharField(verbose_name="Тип акции", max_length=100)
    articles_amount = models.IntegerField(
        verbose_name="Количество товаров, которые могут участвовать",
        null=True,
        blank=True,
    )
    period = models.IntegerField(
        verbose_name="Период для запроса Excel файла", null=True, blank=True
    )

    def __str__(self):
        return f"{self.action_number} {self.name}"

    class Meta:
        verbose_name = "Акция на маркетплейсе"
        verbose_name_plural = "Акция на маркетплейсе"


class ArticleForAction(models.Model):
    """Описывает артикул, который может участвовать в акции"""

    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        verbose_name="Акция",
        related_name="article_for_action",
    )
    article = models.ForeignKey(
        Articles,
        on_delete=models.CASCADE,
        verbose_name="Артикул",
        related_name="article_in_action",
    )
    in_action = models.BooleanField(
        verbose_name="Участвует в акции", null=True, blank=True
    )
    action_price = models.FloatField(verbose_name="Цена в акции", null=True, blank=True)
    current_price = models.FloatField(
        verbose_name="Текущая цена", null=True, blank=True
    )
    discount = models.IntegerField(verbose_name="Текущая скидка", null=True, blank=True)
    plan_discount = models.IntegerField(
        verbose_name="Рекомендуемая скидка для участия в акции", null=True, blank=True
    )

    def __str__(self):
        return f"{self.article.common_article} {self.action.name}"

    class Meta:
        verbose_name = "Артикул, который может участвовать в акции"
        verbose_name_plural = "Артикул, который может участвовать в акции"
