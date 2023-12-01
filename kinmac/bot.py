import asyncio
import json
import os
import re
import tracemalloc
import urllib.parse
from datetime import datetime
from urllib.parse import urlencode

import django
from django.core.files.base import ContentFile
from django.urls import reverse

from kinmac.wsgi import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kinmac.settings')
django.setup()
import psycopg2
import requests
import telegram
from dotenv import load_dotenv
from payment.models import (ApprovalStatus, ApprovedFunction,
                            PayerOrganization, Payments)
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      InputMediaDocument, ReplyKeyboardMarkup)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram_working.start_tg_approve import start_tg_working

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def command_reject(payment_id, user_id, reason):
    ApprovalStatus.objects.filter(
        payment=Payments.objects.get(id=payment_id),
        user=ApprovedFunction.objects.get(
            username=user_id)
        ).update(
            status='REJECTED',
            rejection_reason=reason
        )
    approval_user = ApprovedFunction.objects.get(
        username=user_id)
    Payments.objects.filter(id=payment_id).update(
            accountant='',
            date_of_payment=None,
            status_of_payment=f'Отклонено {approval_user.last_name} {approval_user.first_name}',
            rejection_reason=reason
        )


def reject_reason(update, context):
    chat_id = update.effective_chat.id
    if 'Создать заявку' in update.message.text:
        #url=f'http://127.0.0.1:8000/payment/login?chat_id={chat_id}'
        url = f'http://5.9.57.39/payment/login?chat_id={chat_id}'
        button_url = InlineKeyboardButton(text='Создать заявку', url=url)
        keyboard = [[button_url]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Нажмите на кнопку, чтобы создать заявку:', reply_markup=reply_markup)

    reply = update.message.reply_to_message
    if reply:
        bot_text = reply.text  # Получаем текст сообщения, которое отправил бот
        if 'отклонения' in bot_text:
            chat = update.message.text
            result = re.search(r'\*(.*?)\*', bot_text).group(1)
            reaponse_data = result.split()
            my_data = reaponse_data[2]
            common_data = my_data.split('.')
            payment_id = common_data[0]
            user_id = common_data[1]
            payment_creator = common_data[2]

            command_reject(payment_id, user_id, chat)
            reject_user = ApprovedFunction.objects.get(
                username=user_id)
            create_user = ApprovedFunction.objects.get(
                user_name=payment_creator)
            
            message = f'{create_user.first_name}, пользователь {reject_user.last_name} {reject_user.first_name} отклонил вашу заявку {payment_id}. Причина: {chat}'
            bot.send_message(
                chat_id=int(create_user.chat_id_tg), text=message)

    

def command_approve(payment_id, user_id, payment_creator):
    ApprovalStatus.objects.filter(
        payment=Payments.objects.get(id=payment_id),
        user=ApprovedFunction.objects.get(
        username=user_id)
        ).update(status='OK')
    approval_user = ApprovedFunction.objects.get(
        username=user_id)
    Payments.objects.filter(id=payment_id).update(
        status_of_payment=f'Согласовано {approval_user.last_name} {approval_user.first_name}'
        )
    if approval_user.rating_for_approval < 10:
        start_tg_working(payment_id, payment_creator, (approval_user.rating_for_approval+1))
    elif approval_user.rating_for_approval == 10:
        start_tg_working(payment_id, payment_creator, approval_user.rating_for_approval)



def command_pay(payment_id, user_id, payment_creator, payer_company):
    pay_user = ApprovedFunction.objects.get(
        username=user_id)
    creator_user = ApprovedFunction.objects.get(
        user_name=payment_creator)
    pay = Payments.objects.get(id=payment_id)

    pay.status_of_payment = 'Оплачено'
    pay.date_of_payment = now
    pay.payer_organization = PayerOrganization.objects.get(
        id=payer_company)
    if str(pay.project) == 'KINMAC' and str(pay.payer_organization) == 'ИП Лисов Юрий Владимирович ИНН 366315065753' and (
       str(pay.payment_method) == 'Оплата по расчетному счету' or str(pay.payment_method) == 'Оплата по карте на сайте'):
        pay.payment_coefficient = 1.02
    if str(pay.project) == 'KINMAC' and (
       str(pay.payment_method) == 'Перевод на карту' or str(pay.payment_method) == 'Наличная оплата'):
        pay.payment_coefficient = 1.02
    pay.accountant = f'{pay_user.last_name} {pay_user.first_name}'
    pay.save()
    if pay.send_payment_file == True:
        message = f'Необходимо прислать платёжку к этому платежу. \nПрикрепите файл ОТВЕТОМ к этому сообщению.\n* Техническая информация {payment_id}.{user_id}.{payment_creator} *'
        bot.send_message(
            chat_id=int(creator_user.chat_id_tg), text=message)
    else:
        message = f'{creator_user.first_name}, пользователь {pay_user.last_name} {pay_user.first_name} оплатил вашу заявку {payment_id}'
        message_for_payer = f'Заявка {payment_id} оплачена'
        bot.send_message(
            chat_id=int(creator_user.chat_id_tg), text=message)
        bot.send_message(
            chat_id=int(pay_user.chat_id_tg), text=message_for_payer)


def button_click(update, context):

    query = update.callback_query
    response = query.data
    reaponse_data = response.split()
    payment_id = reaponse_data[1]
    user_id = reaponse_data[2]
    payment_creator = reaponse_data[3]

    if 'Согласовать' in query.data:
        command_approve(payment_id, user_id, payment_creator)
    elif 'Отклонить' in query.data:
        query = update.callback_query
        message_id = query.message.message_id
        #file_id = query.message.document.file_id
        text=f"Напишите причину отклонения заявки {payment_id} ОТВЕТОМ на это сообщение.\n * Техническая информация {payment_id}.{user_id}.{payment_creator} *"

        context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
        context.bot.send_message(chat_id=query.message.chat_id, text=text)

        # query.edit_message_text(
        # text=f"Напишите причину отклонения заявки {payment_id} ОТВЕТОМ на это сообщение.\n * Техническая информация {payment_id}.{user_id}.{payment_creator} *")
        
    elif 'Оплатить' in query.data:
        payers = PayerOrganization.objects.all()
        pay_user = ApprovedFunction.objects.get(
                username=user_id)
        payers_names = []
        payers_id = []
        payers_info = {}
        keyboard = []
        for payer in payers:
            payers_info[payer.pk] = payer.name
            payers_names.append(payer.name)
            payers_id.append(payer.pk)
            data_for_button = f'Сохранить_платёж {payment_id} {user_id} {payment_creator} {payer.pk}' 
            button = [InlineKeyboardButton(callback_data=data_for_button, text=payer.name)]
            keyboard.append(button)
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f'Выберите платильщика'
        bot.send_message(
            chat_id=int(pay_user.chat_id_tg), text=message, reply_markup=reply_markup, parse_mode='Markdown')


    elif 'Сохранить_платёж' in query.data:
        payer_pk = reaponse_data[4]
        command_pay(payment_id, user_id, payment_creator, payer_pk)

def pay_file_handler(update, context):

    message = update.message
    reply = update.message.reply_to_message
    if reply:
        bot_text = reply.text  # Получаем текст сообщения, которое отправил бот
        if 'Необходимо прислать платёжку' in bot_text:
            chat = update.message.text
            result = re.search(r'\*(.*?)\*', bot_text).group(1)
            reaponse_data = result.split()
            my_data = reaponse_data[2]
            common_data = my_data.split('.')
            payment_id = common_data[0]
            user_id = common_data[1]
            payment_creator = common_data[2]
            pay_user = ApprovedFunction.objects.get(
                username=user_id)
            creator_user = ApprovedFunction.objects.get(
                user_name=payment_creator)

            if message.document:
                file_id = update.message.document.file_id
                file_path = bot.get_file(file_id).file_path
                response = requests.get(file_path)
                file_content = response.content
                file = ContentFile(file_content)
                file.name = f'Платежка для заявки {payment_id} от {now}.pdf'  # Установка имени файла
            elif message.photo:
                file_id = update.message.photo[-1].file_id
                file_path = bot.get_file(file_id).file_path
                response = requests.get(file_path)
                file_content = response.content
                file = ContentFile(file_content)
                file.name = f'Платежка для заявки {payment_id} от {now}.png'  # Установка имени файла

            pay = Payments.objects.get(id=payment_id)
            pay.file_of_payment = file
            pay.save()
            message = f'{creator_user.first_name}, пользователь {pay_user.last_name} {pay_user.first_name} оплатил вашу заявку {payment_id}'
            bot.send_message(
                chat_id=int(creator_user.chat_id_tg), text=message)


def command_start(update, context):
    """Функция, которая обрабатывает поступающую команду start"""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    chat = update.effective_chat
    name = update.message.chat.first_name
    soname = update.message.chat.last_name
    username = update.message.chat.username
    idchat = update.message.chat.id

    buttons = ReplyKeyboardMarkup([
        ['/start'], ['Создать заявку']

    ], resize_keyboard=True)
    try:
        connection = psycopg2.connect(database=os.getenv('DB_NAME'),
                                      user=os.getenv('POSTGRES_USER'),
                                      password=os.getenv('POSTGRES_PASSWORD'),
                                      host=os.getenv('DB_HOST'),
                                      port=os.getenv('DB_PORT'),
                                      )
        cursor = connection.cursor()

        tg_select_Query = f'''INSERT INTO users_data (chat_id, username, firstname, lastname)
                VALUES({idchat}, '{username}', '{name}', '{soname}');'''
        cursor.execute(tg_select_Query)
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")
    bot.send_message(
        chat_id=chat.id,
        text=(f'{format(name)}, привет!\n'
              'Теперь я буду помогать тебе работать с платежами'),
        reply_markup=buttons
    )


def main():
    updater = Updater(token=TELEGRAM_TOKEN)
    updater.dispatcher.add_handler(CommandHandler('start', command_start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_click))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, reject_reason))
    updater.dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video, pay_file_handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
