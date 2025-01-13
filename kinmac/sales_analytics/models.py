from datetime import datetime

from database.models import Articles, Marketplace
from django.db import models
from django.urls import reverse


class ReportForCommonSaleAnalytic(models.Model):
    """Проверяет, суммировался ли отчет в общую статисттику или нет."""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="report_for_common_analytic_article",
        blank=True,
        null=True,
    )
    analytic_date = models.DateTimeField(
        verbose_name="Дата отчета",
        blank=True,
        null=True,
    )
    sales_report_number = models.BigIntegerField(
        verbose_name="Номер отчета",
        null=True,
        blank=True,
    )


class CommonSaleAnalytic(models.Model):
    """Общая таблица аналитики товаров. Без указания дат и маркетплейсов"""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="common_sales_analytic_article",
        blank=True,
        null=True,
    )
    average_price_before_spp = models.FloatField(
        verbose_name="Средняя цена до СПП",
        null=True,
        blank=True,
    )
    realization_summ_sale = models.FloatField(
        verbose_name="Реализация (сумма продаж до СПП)",
        null=True,
        blank=True,
    )
    for_pay = models.FloatField(
        verbose_name="К перечислению",
        null=True,
        blank=True,
    )
    sale = models.FloatField(
        verbose_name="Продажи",
        null=True,
        blank=True,
    )
    returns = models.FloatField(
        verbose_name="Возвраты",
        null=True,
        blank=True,
    )
    costprice_of_sales = models.FloatField(
        verbose_name="Себестоимость продаж",
        null=True,
        blank=True,
    )
    penalty = models.FloatField(
        verbose_name="Штрафы",
        null=True,
        blank=True,
    )
    compensation_for_the_substituted = models.FloatField(
        verbose_name="Компенсация подмененного",
        null=True,
        blank=True,
    )
    reimbursement_of_transportation_costs = models.FloatField(
        verbose_name="Возмещение издержек по перевозке",
        null=True,
        blank=True,
    )
    payment_defective_and_lost = models.FloatField(
        verbose_name="Оплата бракованного и потерянного",
        null=True,
        blank=True,
    )
    logistic = models.FloatField(
        verbose_name="Логистика",
        null=True,
        blank=True,
    )
    average_logistic_cost = models.FloatField(
        verbose_name="Средняя стоимость логистики",
        null=True,
        blank=True,
    )
    storage = models.FloatField(
        verbose_name="Хранение",
        null=True,
        blank=True,
    )
    box_multiplicity = models.FloatField(
        verbose_name="Кратность короба",
        null=True,
        blank=True,
    )
    ff_service = models.FloatField(
        verbose_name="Услуга ФФ",
        null=True,
        blank=True,
    )
    advertisment = models.FloatField(
        verbose_name="Рекламная кампания",
        default=0,
    )
    self_purchase = models.FloatField(
        verbose_name="Самовыкуп",
        default=0,
    )
    refusals_and_returns_amount = models.FloatField(
        verbose_name="Количество отказов и возвратов",
        null=True,
        blank=True,
    )
    sales_amount = models.FloatField(
        verbose_name="Продажи, шт",
        null=True,
        blank=True,
    )
    common_sales_with_returns = models.FloatField(
        verbose_name="Общее количество продаж с учетом возвратов",
        null=True,
        blank=True,
    )
    average_percent_of_buyout = models.FloatField(
        verbose_name="Средний процент выкупа",
        null=True,
        blank=True,
    )
    average_profit_for_one_piece = models.FloatField(
        verbose_name="Средняя прибыль на 1 шт",
        null=True,
        blank=True,
    )
    tax = models.FloatField(
        verbose_name="Налог",
        null=True,
        blank=True,
    )
    profit = models.FloatField(
        verbose_name="Прибыль",
        null=True,
        blank=True,
    )
    profit_with_self_purchase = models.FloatField(
        verbose_name="Прибыль с учетом самовыкупов",
        null=True,
        blank=True,
    )
    roi = models.FloatField(
        verbose_name="ROI",
        null=True,
        blank=True,
    )
    profitability = models.FloatField(
        verbose_name="Рентабельность",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Общая таблица аналитики товаров"
        verbose_name_plural = "Общая таблица аналитики товаров"


class ArticleSaleAnalytic(models.Model):
    """Таблица аналитики товаров. С датами и маркетплейсами"""

    article = models.ForeignKey(
        Articles,
        verbose_name="Артикул",
        on_delete=models.SET_NULL,
        related_name="article_sales_analytic_article",
        blank=True,
        null=True,
    )
    analytic_date = models.DateTimeField(
        verbose_name="Дата отчета",
        blank=True,
        null=True,
    )
    sales_report_number = models.BigIntegerField(
        verbose_name="Номер отчета",
        null=True,
        blank=True,
    )
    marketplace = models.ForeignKey(
        Marketplace,
        verbose_name="Маркетплейс",
        on_delete=models.SET_NULL,
        related_name="article_sales_analytic_marketplace",
        blank=True,
        null=True,
    )
    average_price_before_spp = models.FloatField(
        verbose_name="Средняя цена до СПП",
        null=True,
        blank=True,
    )
    realization_summ_sale = models.FloatField(
        verbose_name="Реализация (сумма продаж)",
        null=True,
        blank=True,
    )
    sale = models.FloatField(
        verbose_name="Продажи",
        null=True,
        blank=True,
    )
    for_pay = models.FloatField(
        verbose_name="К перечислению",
        null=True,
        blank=True,
    )

    returns = models.FloatField(
        verbose_name="Возвраты",
        null=True,
        blank=True,
    )
    costprice_of_sales = models.FloatField(
        verbose_name="Себестоимость продаж",
        null=True,
        blank=True,
    )
    penalty = models.FloatField(
        verbose_name="Штрафы",
        null=True,
        blank=True,
    )
    compensation_for_the_substituted = models.FloatField(
        verbose_name="Компенсация подмененного",
        null=True,
        blank=True,
    )
    reimbursement_of_transportation_costs = models.FloatField(
        verbose_name="Возмещение издержек по перевозке",
        null=True,
        blank=True,
    )
    payment_defective_and_lost = models.FloatField(
        verbose_name="Оплата бракованного и потерянного",
        null=True,
        blank=True,
    )
    logistic = models.FloatField(
        verbose_name="Логистика",
        null=True,
        blank=True,
    )
    average_logistic_cost = models.FloatField(
        verbose_name="Средняя стоимость логистики",
        null=True,
        blank=True,
    )
    storage = models.FloatField(
        verbose_name="Хранение",
        null=True,
        blank=True,
    )
    box_multiplicity = models.FloatField(
        verbose_name="Кратность короба",
        null=True,
        blank=True,
    )
    ff_service = models.FloatField(
        verbose_name="Услуга ФФ",
        null=True,
        blank=True,
    )
    advertisment = models.FloatField(
        verbose_name="Рекламная кампания",
        default=0,
    )
    self_purchase = models.FloatField(
        verbose_name="Самовыкуп",
        default=0,
    )
    refusals_and_returns_amount = models.FloatField(
        verbose_name="Количество отказов и возвратов",
        default=0,
    )
    sales_amount = models.FloatField(
        verbose_name="Продажи, шт",
        null=True,
        blank=True,
    )
    common_sales_with_returns = models.FloatField(
        verbose_name="Общее количество продаж с учетом возвратов",
        null=True,
        blank=True,
    )
    average_percent_of_buyout = models.FloatField(
        verbose_name="Средний процент выкупа",
        null=True,
        blank=True,
    )
    average_profit_for_one_piece = models.FloatField(
        verbose_name="Средняя прибыль на 1 шт",
        null=True,
        blank=True,
    )
    tax = models.FloatField(
        verbose_name="Налог",
        null=True,
        blank=True,
    )
    profit = models.FloatField(
        verbose_name="Прибыль",
        null=True,
        blank=True,
    )
    profit_with_self_purchase = models.FloatField(
        verbose_name="Прибыль с учетом самовыкупов",
        null=True,
        blank=True,
    )
    roi = models.FloatField(
        verbose_name="ROI",
        null=True,
        blank=True,
    )
    profitability = models.FloatField(
        verbose_name="Рентабельность",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Общая таблица аналитики товаров"
        verbose_name_plural = "Общая таблица аналитики товаров"
