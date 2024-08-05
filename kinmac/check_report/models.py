from django.db import models


class CommonSalesReportData(models.Model):
    """Общие сведенные данные еженедельного отчета по реализации"""
    realizationreport_id = models.BigIntegerField(
        verbose_name='Номер отчета',
        null=True,
        blank=True,
    )
    date_from = models.DateTimeField(
        verbose_name='Дата начала отчётного периода',
        null=True,
        blank=True,
    )
    date_to	= models.DateTimeField(
        verbose_name='Дата конца отчётного периода',
        null=True,
        blank=True,
    )
    create_dt = models.DateTimeField(
        verbose_name='Дата формирования отчёта',
        null=True,
        blank=True,
    )
    retail_amount = models.FloatField(
        verbose_name='Сумма продаж',
        null=True,
        blank=True,
    )
    return_amount = models.FloatField(
        verbose_name='Сумма возвратов',
        null=True,
        blank=True,
    )
    retail_without_return = models.FloatField(
        verbose_name='Продажи минус возвраты',
        null=True,
        blank=True,
    )
    delivery_rub = models.FloatField(
        verbose_name='Стоимость логистики',
        null=True,
        blank=True,
    )
    ppvz_for_pay = models.FloatField(
        verbose_name='К перечислению продавцу за реализованный товар',
        null=True,
        blank=True,
    )
    ppvz_retail = models.FloatField(
        verbose_name='К перечислению продажи',
        null=True,
        blank=True,
    )
    ppvz_return = models.FloatField(
        verbose_name='К перечислению возвраты',
        null=True,
        blank=True,
    )
    penalty = models.FloatField(
        verbose_name='Другие виды штрафов',
        null=True,
        blank=True,
    )
    common_penalty = models.FloatField(
        verbose_name='Общая сумма штрафов',
        null=True,
        blank=True,
    )
    storage_fee = models.FloatField(
        verbose_name='Стоимость хранения',
        null=True,
        blank=True,
    )
    acceptance_goods = models.FloatField(
        verbose_name='Стоимость платной приемки',
        null=True,
        blank=True,
    )
    deduction = models.FloatField(
        verbose_name='Прочие удержания/выплаты',
        null=True,
        blank=True,
    )
    total_paid = models.FloatField(
        verbose_name='Итого к оплате',
        null=True,
        blank=True,
    )
    check_ppvz_for_pay = models.FloatField(
        verbose_name='К перечислению (проверка)',
        null=True,
        blank=True,
    )
    check_comission_summ = models.FloatField(
        verbose_name='Сумма комиссий (проверка)',
        null=True,
        blank=True,
    )
    check_fact = models.BooleanField(
        verbose_name='Факт прошедшей проверки строки',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Сверка еженедельных отчетов'
        verbose_name_plural = 'Сверка еженедельных отчетов'
