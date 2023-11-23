import os
import tracemalloc

import telegram
from dotenv import load_dotenv
from payment.models import (ApprovalStatus, ApprovedFunction, CashPayment,
                            Contractors, PayerOrganization, Payers, Payments,
                            PayWithCard, PayWithCheckingAccount,
                            TransferToCard)
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

tracemalloc.start()


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def message_constructor(user, creator_user, payment_id, payment, payment_method, pay_with_method):
    message = f'''
        {user.first_name}, пользователь {creator_user.last_name} {creator_user.first_name} создал новую заявку {payment_id}:
            Название проекта: *{payment.project.name}*
            Название категории: *{payment.category.name}*
            Сумма платежа: *{payment.payment_sum}*
            Комментарий к платежу: *{payment.comment}*
            Организация получателя: *{payment.contractor_name}*
            Способ оплаты: *{payment.payment_method.method_name}*
        '''
    
    if payment_method == 1:
        message = message + f"Файл счета: [Скачать файл](http://5.9.57.39/media/{pay_with_method.file_of_bill})"
    if payment_method == 2:
        message = message + f"Ссылка на платёж: *{pay_with_method.link_to_payment}*"
    if payment_method == 3:
        message = message + f'''Номер карты: *{pay_with_method.card_number}*
        Номер телефона: *{pay_with_method.phone_number}*
        Получатель платежа: *{pay_with_method.payment_receiver}*
        Банк для платежа: *{pay_with_method.bank_for_payment}*
        '''
    if payment_method == 4:
        message = message + f"Данные для оплаты: *{pay_with_method.cash_payment_payment_data}*"
    message = message.replace('            ', '').replace('        ', '')
    return message


def approve_process(payment_id, payment_creator, creator_user_rating):
    """
    Функция отвечает за процесс согласования заявки.
    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    users = ApprovedFunction.objects.all()
    creator_user = ApprovedFunction.objects.get(
        user_name=payment_creator)
    payment = Payments.objects.get(id=payment_id)
    
    
    rating_all_users = ApprovedFunction.objects.all(
    ).values_list('rating_for_approval', flat=True)
    
    if creator_user_rating <= 10:
        if creator_user_rating in rating_all_users and creator_user_rating > 0:
            for user in users:
                if user.rating_for_approval == creator_user_rating:
                    keyboard = [[InlineKeyboardButton("Согласовать", callback_data=f'Согласовать {payment_id} {user} {payment_creator}'),
                        InlineKeyboardButton("Отклонить", callback_data=f'Отклонить {payment_id} {user} {payment_creator}'),
                        InlineKeyboardButton("Оплатить", callback_data=f'Оплатить {payment_id} {user} {payment_creator}')]]

                    reply_markup = InlineKeyboardMarkup(keyboard)

                    if payment.payment_method.pk == 1:
                        pay_with_method = PayWithCheckingAccount.objects.get(payment_id=payment.pk)
                    elif payment.payment_method.pk == 2:
                        pay_with_method = PayWithCard.objects.get(payment_id=payment.pk)
                    elif payment.payment_method.pk == 3:
                        pay_with_method = TransferToCard.objects.get(payment_id=payment.pk)
                    elif payment.payment_method.pk == 4:
                        pay_with_method = CashPayment.objects.get(payment_id=payment.pk)

                    message = message_constructor(user, creator_user, payment_id, payment, payment.payment_method.pk, pay_with_method)
                    bot.send_message(
                        chat_id=f'{int(user.chat_id_tg)}', text=message, reply_markup=reply_markup, parse_mode='Markdown')
                    break
        else:
            approve_process(payment_id, payment_creator,
                            (creator_user_rating+1))


def start_tg_working(payment_id, payment_creator, creator_user_rating):
    """
    Функция запускает процесс согласования.
    Отвечает за процесс согласования заявки, если рейтинг пользователя = 10.
    """

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    accountant_job = Payers.objects.get(name='Бухгалтер')
    accountant = ApprovedFunction.objects.get(job_title=accountant_job.pk)
    creator = ApprovedFunction.objects.get(user_name=payment_creator)
    payment = Payments.objects.get(id=payment_id)
    if payment.payment_method.pk == 1:
        pay_with_method = PayWithCheckingAccount.objects.get(payment_id=payment.pk)
    elif payment.payment_method.pk == 2:
        pay_with_method = PayWithCard.objects.get(payment_id=payment.pk)
    elif payment.payment_method.pk == 3:
        pay_with_method = TransferToCard.objects.get(payment_id=payment.pk)
    elif payment.payment_method.pk == 4:
        pay_with_method = CashPayment.objects.get(payment_id=payment.pk)

    if creator_user_rating < 10:
        approve_process(payment_id, payment_creator, creator_user_rating)
    else:
        keyboard = [[InlineKeyboardButton("Отклонить", callback_data=f'Отклонить {payment_id} {accountant} {payment_creator}'),
                    InlineKeyboardButton("Оплатить", callback_data=f'Оплатить {payment_id} {accountant} {payment_creator}')]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        message = message_constructor(accountant, creator, payment_id, payment, payment.payment_method.pk, pay_with_method)
        bot.send_message(
            chat_id=f'{int(accountant.chat_id_tg)}', text=message, reply_markup=reply_markup, parse_mode='Markdown')
