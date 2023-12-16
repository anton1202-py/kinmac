from datetime import datetime

from django.contrib.auth.models import User
from django.db import models

from .validators import StripToNumbers


class Projects(models.Model):
    name = models.CharField(
        verbose_name='Название проекта',
        max_length=50,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'


class Categories(models.Model):
    name = models.CharField(
        verbose_name='Название категории',
        max_length=50,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class PaymentMethod(models.Model):
    method_name = models.CharField(
        verbose_name='Метод оплаты',
        max_length=50,
    )

    def __str__(self):
        return self.method_name

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Способы оплаты'


class Payers(models.Model):
    name = models.CharField(
        verbose_name='Платильщик',
        max_length=150,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Оплачивающий'
        verbose_name_plural = 'Оплачивающий'


class PayerOrganization(models.Model):
    name = models.CharField(
        verbose_name='Платящая организация',
        max_length=150,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Оплачивающая компания'
        verbose_name_plural = 'Оплачивающая компания'


class Contractors(models.Model):
    name = models.CharField(
        verbose_name='Название организации',
        max_length=150,
        blank=True,
        null=True,
    )
    bill_number = models.CharField(
        verbose_name='Номер счета',
        max_length=30,
        blank=True,
        null=True,
    )
    bik_of_bank = models.CharField(
        verbose_name='БИК банка',
        max_length=20,
        blank=True,
        null=True,
    )
    bank_name = models.CharField(
        verbose_name='Название банка',
        max_length=50,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Контрагент'
        verbose_name_plural = 'Контрагенты'


class Payments(models.Model):
    pub_date = models.DateTimeField(
        verbose_name='Дата создания заявки',
        auto_now_add=True,
        editable=True,
    )
    creator = models.CharField(
        verbose_name='Создатель заявки',
        max_length=80,
        null=True,
        blank=True,
    )
    payer_organization = models.ForeignKey(
        PayerOrganization,
        verbose_name='Организация плательщик',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    project = models.ForeignKey(
        Projects,
        verbose_name='Проект',
        on_delete=models.PROTECT,
    )
    category = models.ForeignKey(
        Categories,
        verbose_name='Категория',
        on_delete=models.PROTECT,
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        verbose_name='Способ оплаты',
        on_delete=models.PROTECT,
    )
    payment_sum = models.FloatField(
        verbose_name='Сумма',
    )
    comment = models.TextField(
        verbose_name='За что платим',
        blank=True,
        null=True,
    )
    contractor_name = models.ForeignKey(
        Contractors,
        verbose_name='Кому',
        max_length=100,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    send_payment_file = models.BooleanField(
        verbose_name='Присылать платежку/чек',
    )
    file_of_payment = models.FileField(
        verbose_name='Файл платёжки',
        upload_to="uploads_of_payment_/%Y/%m/%d/",
        blank=True,
        null=True,
    )
    urgent_payment = models.BooleanField(
        verbose_name='Срочный платеж',
    )
    status_of_payment = models.CharField(
        verbose_name='Статус заявки',
        max_length=100,
        blank=True,
        null=True,
    )
    date_of_payment = models.DateTimeField(
        verbose_name='Дата и время оплаты',
        blank=True,
        null=True,
    )
    accountant = models.CharField(
        verbose_name='Произвел оплату',
        max_length=80,
        blank=True,
        null=True,
    )
    rejection_reason = models.CharField(
        verbose_name='Причина отказа заявки',
        max_length=300,
        blank=True,
        null=True,
    )
    payment_coefficient = models.FloatField(
        verbose_name='Коэффициент для учета',
        default=1.0,
        blank=True,
    )

    @property
    def my_file_of_payment(self):
        try:
            url = self.file_of_payment.url
        except:
            url = ''
        return url


class ApprovalStatus(models.Model):
    payment = models.ForeignKey(
        Payments,
        verbose_name='Номер оплаты',
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        'ApprovedFunction',
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    status = models.CharField(
        verbose_name='Статус',
        max_length=20,
        blank=True,
        null=True,
    )
    pub_date = models.DateTimeField(
        verbose_name='Изменения статуса',
        blank=True,
        null=True,
    )
    rejection_reason = models.CharField(
        verbose_name='Причина отказа заявки',
        max_length=300,
        blank=True,
        null=True,
    )


class PayWithCheckingAccount(models.Model):

    payment_id = models.ForeignKey(
        Payments,
        verbose_name='Номер оплаты',
        on_delete=models.CASCADE,
    )
    # contractor_name = models.CharField(
    # verbose_name='Название организации получателя',
    # max_length=100,
    # blank=True,
    # null=True,
    # )
    contractor_bill_number = models.CharField(
        verbose_name='Номер счета организации получателя',
        max_length=20,
        blank=True,
        null=True,
    )
    contractor_bik_of_bank = models.CharField(
        verbose_name='БИК банка организации получателя',
        max_length=20,
        blank=True,
        null=True,
    )
    file_of_bill = models.FileField(
        verbose_name='Файл счета',
        upload_to="uploads_of_bill_/%Y/%m/%d/",
    )

    class Meta:
        verbose_name = 'Оплата по счету'
        verbose_name_plural = 'Оплата по счету'


class PayWithCard(models.Model):
    """Модель описывает форму заполнения платежа - оплата картой"""
    payment_id = models.ForeignKey(
        Payments,
        verbose_name='Номер оплаты',
        on_delete=models.CASCADE,
    )
    # contractor_name = models.CharField(
    #     verbose_name='Получатель платежа',
    #     max_length=100,
    #     blank=True,
    #     null=True,
    # )
    link_to_payment = models.CharField(
        verbose_name='Ссылка на платёж',
        max_length=200,
        blank=True,
        null=True,
    )


class TransferToCard(models.Model):
    """Модель описывает форму заполнения платежа - перевод на карту"""
    payment_id = models.ForeignKey(
        Payments,
        verbose_name='Номер оплаты',
        on_delete=models.CASCADE,
    )
    card_number = models.CharField(
        verbose_name='Номер карты',
        max_length=19,
        validators=[StripToNumbers],
        blank=True,
        null=True,
    )
    phone_number = models.CharField(
        verbose_name='Номер телефона',
        # validators=[RegexValidator(r'^\d{1,10}$')],
        max_length=12,
        blank=True,  # optional
    )
    payment_receiver = models.CharField(
        verbose_name='Получатель платежа',
        max_length=150,
        blank=True,
        null=True,
    )
    bank_for_payment = models.CharField(
        verbose_name='Банк для платежа',
        max_length=30,
    )


class CashPayment(models.Model):
    payment_id = models.ForeignKey(
        Payments,
        verbose_name='Номер оплаты',
        on_delete=models.CASCADE,
    )
    cash_payment_payment_data = models.TextField(
        verbose_name='Данные для оплаты',
        blank=True,
        null=True,
    )


class ApprovedFunction(models.Model):
    username = models.ForeignKey(
        User,
        verbose_name='Имя пользователя',
        on_delete=models.PROTECT,
    )
    user_name = models.CharField(
        verbose_name='Username',
        max_length=50,
        blank=True,
        null=True,
    )
    first_name = models.CharField(
        verbose_name='Имя сотрудника',
        max_length=100,
    )
    last_name = models.CharField(
        verbose_name='Фамилия сотрудника',
        max_length=100,
    )
    job_title = models.ForeignKey(
        Payers,
        verbose_name='Должность',
        on_delete=models.PROTECT,
    )
    # project = models.ForeignKey(
    #    Projects,
    #    verbose_name='Проекты',
    #    on_delete=models.PROTECT,
    # )
    rating_for_approval = models.PositiveSmallIntegerField(
        verbose_name='Рейтинг для согласования',
    )
    chat_id_tg = models.CharField(
        verbose_name='Chat_id из Телеграм',
        max_length=15,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        self.user_name = self.username.username
        super(ApprovedFunction, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.username.id)

    class Meta:
        verbose_name = 'Рейтинг для согласования'
        verbose_name_plural = 'Рейтинг для согласования'


class TelegramMessageActions(models.Model):
    """
    Модель, которая содержит message_id сообщений бота.
    Что позволит редактировать сообщения в зависимости от статуса заявки
    """
    payment = models.ForeignKey(
        Payments,
        verbose_name='Номер заявки на оплату',
        on_delete=models.CASCADE,
    )
    chat_id = models.CharField(
        verbose_name='chat_id пользователя в телеграм',
        max_length=20,
        blank=True,
        null=True,
    )
    message_id = models.CharField(
        verbose_name='message_id сообщения в чате с ботом',
        max_length=50,
        blank=True,
        null=True,
    )
    message_type = models.CharField(
        verbose_name='Тип сообщения от бота',
        max_length=50,
        blank=True,
        null=True,
    )
    message_author = models.CharField(
        verbose_name='Автор сообщения',
        max_length=50,
        blank=True,
        null=True,
    )
    message = models.CharField(
        verbose_name='Текст сообщения',
        max_length=400,
        blank=True,
        null=True,
    )
    reply_markup = models.CharField(
        verbose_name='Кнопка из сообщения',
        max_length=800,
        blank=True,
        null=True,
    )

    attach = models.BooleanField(
        verbose_name='Документ в сообщении',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'Информация о сообщениях в телеграм'
        verbose_name_plural = 'Информация о сообщениях в телеграм'
