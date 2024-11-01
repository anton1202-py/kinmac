from django.db import models
from database.models import Articles



class MarketplaceCommission(models.Model):
    """Модель для хранения процента комиссии на разных платформах"""
    marketplace_product = models.OneToOneField(Articles, related_name='article_comission', on_delete=models.CASCADE,
                                               verbose_name='Комиссия артикула', null=True, blank=True)
    fbs_commission = models.FloatField(
        verbose_name='Комиссия FBS', null=True, blank=True)
    fbo_commission = models.FloatField(
        verbose_name='Комиссия FBO', null=True, blank=True)
    dbs_commission = models.FloatField(
        verbose_name='Комиссия DBS', null=True, blank=True)
    fbs_express_commission = models.FloatField(
        verbose_name='Комиссия FBS Express', null=True, blank=True)

    class Meta:
        verbose_name = "Комиссия на Маркетплейсе"
        verbose_name_plural = "Комиссия на Маркетплейсе"


class WbLogisticTariffs(models.Model):
    """
    Для товаров, которые поставляются на склад в коробах (коробках), возвращает стоимость:

    доставки со склада или пункта приёма до покупателя
    доставки от покупателя до пункта приёма
    хранения на складе WB
    """
    box_delivery_and_storage_expr = models.FloatField(
        verbose_name='Коэффициент, %. На него умножается стоимость доставки и хранения.', 
        null=True, blank=True)
    box_delivery_base = models.FloatField(
        verbose_name='Доставка 1 литра, ₽', 
        null=True, blank=True)
    box_delivery_liter = models.FloatField(
        verbose_name='Доставка каждого дополнительного литра, ₽', 
        null=True, blank=True)
    box_storage_base = models.FloatField(
        verbose_name='Хранение 1 литра, ₽', 
        null=True, blank=True)
    box_storage_liter = models.FloatField(
        verbose_name='Хранение каждого дополнительного литра, ₽', 
        null=True, blank=True)
    warehouseName = models.CharField(
        verbose_name='Название склада',
        max_length=255, 
        null=True, blank=True)
    date_start = models.DateField(
        verbose_name="Дата", null=True, blank=True)
    
    class Meta:
        verbose_name = "КОэффициенты хранения складов"
        verbose_name_plural = "Коэффициенты хранения складов"
    



class MarketplaceLogistic(models.Model):
    """Модель для хранения логистических затрат на разных платформах"""
    marketplace_product = models.OneToOneField(Articles, related_name='article_logistic', on_delete=models.CASCADE,
                                               verbose_name='Продукт на маркетплейсе', null=True, blank=True)
    cost_logistic = models.FloatField(
        verbose_name='Логистические затраты', null=True, blank=True)
    cost_logistic_fbo = models.FloatField(
        verbose_name='Логистические затраты FBO', null=True, blank=True)
    cost_logistic_fbs = models.FloatField(
        verbose_name='Логистические затраты FBS', null=True, blank=True)

    class Meta:
        verbose_name = "Логистические затраты на Маркетплейсе"
        verbose_name_plural = "Логистические затраты на Маркетплейсе"