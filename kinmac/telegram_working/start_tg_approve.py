import json
import os
import tracemalloc

import telegram
from dotenv import load_dotenv
from payment.models import (ApprovedFunction, CashPayment, Payers, Payments,
                            PayWithCard, PayWithCheckingAccount,
                            TelegramMessageActions, TransferToCard)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram_working.assistance import save_message_function

tracemalloc.start()


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telegram.Bot(token=TELEGRAM_TOKEN)


def message_constructor(user, creator_user, payment_id, payment, payment_method, pay_with_method):
    """Создает сообщение для пользователя о созданной заявке"""
    payment = Payments.objects.get(id=payment_id)
    add_urgent_message = ''
    add_payment_file_message = ''
    file_path = ''
    if payment.urgent_payment == True:
        add_urgent_message = '🔥*СРОЧНО!*\n'
    if payment.send_payment_file == True:
        add_payment_file_message = '*‼️НУЖНА ПЛАТЕЖКА / ЧЕК*\n'
    message =add_urgent_message +  add_payment_file_message + f'''
            *{payment.project.name}* - *{payment.category.name}*
            За что: {payment.comment}
            Сумма: {payment.payment_sum}
            Кому: {payment.contractor_name}
            Способ: *{payment.payment_method.method_name}* 
        '''
    
    if payment_method == 1:
        file_path = f'http://5.9.57.39/media/{pay_with_method.file_of_bill}'
    elif payment_method == 2:
        message = message + f"Ссылка на платёж: *{pay_with_method.link_to_payment}*"
    elif payment_method == 3:
        message = message + f'''Карта: *{pay_with_method.card_number}*
        Телефон: *{pay_with_method.phone_number}*
        Получатель по банку: *{pay_with_method.payment_receiver}*
        Банк: *{pay_with_method.bank_for_payment}*
        '''
    elif payment_method == 4:
        message = message + f"Данные для оплаты: *{pay_with_method.cash_payment_payment_data}*"
    
    if payment.status_of_payment == 'На согласовании' or payment.status_of_payment == 'Согласовано Лисов Юрий':
        payment_status = '🕐 Согласование'
    elif payment.status_of_payment == 'Согласовано Лисов Александр':
        payment_status = '💲Оплата'
    elif payment.status_of_payment == 'Оплачено':
        payment_status = '✅ Оплачено'
    elif 'Отклонено' in payment.status_of_payment:
        payment_status = '❌ Отклонено'
    message = message + f"""\nСтатус:  {payment_status}"""
    message = message.replace('            ', '').replace('        ', '')
    return message


def approve_process(payment_id, payment_creator, creator_user_rating):
    """
    Функция отвечает за процесс согласования заявки.
    """
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
                        InlineKeyboardButton("Оплачено", callback_data=f'Оплатить {payment_id} {user} {payment_creator}')]]

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
                    if payment.payment_method.pk == 1:
                        #file_path = f'http://5.9.57.39/media/{pay_with_method.file_of_bill}'
                        file_path = os.path.join(os.getcwd(), 'media/' f'{pay_with_method.file_of_bill}')
                        with open(file_path, 'rb') as f:
                            message_obj = bot.send_document(chat_id=int(user.chat_id_tg),
                                document=f,
                                reply_markup=reply_markup,
                                caption=message,
                                parse_mode='Markdown')
                            save_message_function(payment, user.chat_id_tg,
                                message_obj.message_id, 'create_approve',
                                user.user_name, message, reply_markup, True)
                    else:
                        message_obj = bot.send_message(
                            chat_id=int(user.chat_id_tg),
                            text=message,
                            reply_markup=reply_markup,
                            parse_mode='Markdown')
                        save_message_function(payment, user.chat_id_tg,
                            message_obj.message_id, 'create_approve',
                            user.user_name, message, reply_markup, False)
                    break
        else:
            approve_process(payment_id, payment_creator, (creator_user_rating+1))

def send_message_to_creator(payment_id, payment_creator, creator_user_rating):
    """Фнукция отрпавялет сообщение создателю с только что созданной заявкой"""
    payment = Payments.objects.get(id=payment_id)
    creator = ApprovedFunction.objects.get(user_name=payment_creator)
    if creator_user_rating == 0:
        if payment.payment_method.pk == 1:
            pay_with_method = PayWithCheckingAccount.objects.get(payment_id=payment.pk)
        elif payment.payment_method.pk == 2:
            pay_with_method = PayWithCard.objects.get(payment_id=payment.pk)
        elif payment.payment_method.pk == 3:
            pay_with_method = TransferToCard.objects.get(payment_id=payment.pk)
        elif payment.payment_method.pk == 4:
            pay_with_method = CashPayment.objects.get(payment_id=payment.pk)

        message = message_constructor(payment_creator, payment_creator, payment_id, payment, payment.payment_method.pk, pay_with_method)
        keyboard = [[InlineKeyboardButton("Отклонить", callback_data=f'Отклонить {payment_id} {creator} {payment_creator}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if payment.payment_method.pk == 1:
            file_path = os.path.join(os.getcwd(), 'media/' f'{pay_with_method.file_of_bill}')
            with open(file_path, 'rb') as f:
                message_obj = bot.send_document(
                    chat_id=int(creator.chat_id_tg),
                    document=f,
                    reply_markup=reply_markup,
                    caption=message,
                    parse_mode='Markdown')
                save_message_function(payment, creator.chat_id_tg,
                    message_obj.message_id, 'create_approve',
                    creator.user_name, message, reply_markup, True)
        else:
            message_obj = bot.send_message(
                chat_id=int(creator.chat_id_tg),
                text=message,
                reply_markup=reply_markup,
                parse_mode='Markdown')
            save_message_function(payment, creator.chat_id_tg,
                message_obj.message_id, 'create_approve',
                creator.user_name, message, reply_markup, False)
    start_tg_working(payment_id, payment_creator, creator_user_rating)


def start_tg_working(payment_id, payment_creator, creator_user_rating):
    """
    Функция запускает процесс согласования.
    Отвечает за процесс согласования заявки, если рейтинг пользователя = 10.
    Или заявку создал бухгалтер
    """
    
    accountant_job = Payers.objects.get(name='Бухгалтер')
    accountants = ApprovedFunction.objects.filter(job_title=accountant_job.pk)
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

    if creator_user_rating < 10 and creator.job_title != 'Бухгалтер':
        approve_process(payment_id, payment_creator, creator_user_rating)
    else:

        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'reply_markup', 'attach')

        for message in messages:
            chat_id_cicle =  message[0]
            message_id_cicle = message[1]
            current_text = message[2]
            reply_markup = json.loads(message[3].replace("'", "\""))
            attach = message[4]
            words = current_text.split("Статус:")
            new_text = words[0] + 'Статус: 💲Оплата'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, message_id=message_id_cicle, parse_mode='Markdown')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, message_id=message_id_cicle, parse_mode='Markdown')

        for accountant in accountants:
            keyboard = [[InlineKeyboardButton("Отклонить", callback_data=f'Отклонить {payment_id} {accountant} {payment_creator}'),
                        InlineKeyboardButton("В работе", callback_data=f'Вработе {payment_id} {accountant} {payment_creator}'),
                        InlineKeyboardButton("Оплачено", callback_data=f'Оплатить {payment_id} {accountant} {payment_creator}')]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            message = message_constructor(accountant, creator, payment_id, payment, payment.payment_method.pk, pay_with_method)
            if payment.payment_method.pk == 1:
                file_path = os.path.join(os.getcwd(), 'media/' f'{pay_with_method.file_of_bill}')
                with open(file_path, 'rb') as f:
                    message_obj = bot.send_document(
                        chat_id=int(accountant.chat_id_tg),
                        document=f,
                        reply_markup=reply_markup,
                        caption=message,
                        parse_mode='Markdown')
                    save_message_function(payment, accountant.chat_id_tg,
                        message_obj.message_id, 'create_approve',
                        accountant.user_name, message, reply_markup, True)
            else:
                message_obj = bot.send_message(
                    chat_id=int(accountant.chat_id_tg),
                    reply_markup=reply_markup,
                    text=message,
                    parse_mode='Markdown')
                save_message_function(payment, accountant.chat_id_tg,
                    message_obj.message_id, 'create_approve',
                    accountant.user_name, message, reply_markup, False)
