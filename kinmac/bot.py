import os
import re
from datetime import datetime
from urllib.parse import urlencode

import django
from django.core.files.base import ContentFile

from kinmac.wsgi import *

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kinmac.settings')
django.setup()
import psycopg2
import requests
import telegram
from dotenv import load_dotenv
from payment.models import (ApprovalStatus, ApprovedFunction,
                            PayerOrganization, Payments,
                            TelegramMessageActions)
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram_working.assistance import save_message_function
from telegram_working.start_tg_approve import start_tg_working

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def command_reject(payment_id, user_id, reason):
    """Функция отвечает за обработку команды отклонения заявки"""
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
    messages = TelegramMessageActions.objects.filter(
        payment=Payments.objects.get(id=payment_id),
        message_type='create_approve'
    ).values_list('chat_id', 'message_id', 'message', 'attach')

    for message in messages:
        chat_id =  message[0]
        message_id = message[1]
        current_text = message[2]
        attach = message[3]
        words = current_text.split("Статус:")
        new_text = words[0] + f'\nСтатус: ❌ Отклонено\nПричина: {reason}'
        if attach == True:
            bot.edit_message_caption(caption=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
        else:
            bot.edit_message_text(text=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')


def reject_reason(update, context):
    """
    Функция обрабатывает текстовые сообщения, которые поступаю в бот.
    Если они удовлетвоябт условию логики бота, то выполняет с сообщениями
    дальнейшие действия
    """
    chat_id = update.effective_chat.id

    reply = update.message.reply_to_message
    mess_id = update.message.message_id
    
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
            payment = Payments.objects.get(id=payment_id)
            
            command_reject(payment_id, user_id, chat)
            reject_user = ApprovedFunction.objects.get(
                username=user_id)
            save_message_function(payment, chat_id,
                mess_id, 'rejected_reason_inform', 
                reject_user.user_name, update.message.text, False)
            create_user = ApprovedFunction.objects.get(
                user_name=payment_creator)
            # Удаляем все сообщения связанные с заявкой, кроме message_type=create_approve
            messages_for_delete = TelegramMessageActions.objects.filter(
                payment=Payments.objects.get(id=payment_id)).exclude(
                message_type='create_approve'
            ).values_list('chat_id', 'message_id')
            for message_del in messages_for_delete:
                chat_id =  message_del[0]
                message_id = message_del[1]
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            # Отрпавляем создателю заявки, что заявка отклонена по какой-то причине
            message = f'Отклонено.\nПричина: {chat}'
            message_rej_id = TelegramMessageActions.objects.get(
                payment=Payments.objects.get(id=payment_id),
                message_type='create_approve',
                message_author=payment_creator
            ).message_id
            message_obj = bot.send_message(
                chat_id=int(create_user.chat_id_tg), text=message, reply_to_message_id=message_rej_id)

            # Записываем сообщение с причиной в базу данных
            save_message_function(payment, create_user.chat_id_tg,
                message_obj.message_id, 'rejected_reason_inform', 
                create_user.user_name, message, False)


def command_approve(payment_id, user_id, payment_creator):
    """
    Функция вносит в базу данных изменения связанные с соглаованием
    заявки.
    """
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
    """Функция выполняет действия после нажатия на кнопку ОПЛАЧЕНО"""
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
        message_file_obj = bot.send_message(
            chat_id=int(creator_user.chat_id_tg), text=message)
        # Сохраняем сообщение в базу
        save_message_function(pay, creator_user.chat_id_tg, 
            message_file_obj.message_id, 'payment_file', 
            creator_user.user_name, message, False)
    else:
        # Изменяем текст во всех сообщениях связанных с заявкой
        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'attach')

        for message in messages:
            chat_id =  message[0]
            message_id = message[1]
            current_text = message[2]
            attach = message[3]
            words = current_text.split("Статус:")
            new_text = words[0] + 'Статус: ✅ Оплачено'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')

        # Удаляем все сообщения, относящиеся к заявки, кроме тех, у которых message_type='create_approve'
        messages_for_delete = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id)).exclude(
            message_type='create_approve'
        ).values_list('chat_id', 'message_id')
        for message_del in messages_for_delete:
            chat_id =  message_del[0]
            message_id = message_del[1]
            bot.delete_message(chat_id=chat_id, message_id=message_id)

        # Информирование создателя заявки, что заявка оплачена
        message_id = TelegramMessageActions.objects.get(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve',
            message_author=payment_creator
        ).message_id
        message_obj = bot.send_message(
            chat_id=int(creator_user.chat_id_tg), text='Оплачено', reply_to_message_id=message_id)
        save_message_function(pay, creator_user.chat_id_tg, 
            message_obj.message_id, 'payment_done', creator_user.user_name,
            message, False)    


def button_click(update, context):
    """Обрабатьвает нажатия кнопой в сообщении"""
    query = update.callback_query
    response = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    reaponse_data = response.split()
    payment_id = reaponse_data[1]
    user_id = reaponse_data[2]
    payment_creator = reaponse_data[3]

    payment = Payments.objects.get(id=payment_id)
    user = ApprovedFunction.objects.get(
                username=user_id)

    if 'Согласовать' in query.data:
        keyboard = [[
            InlineKeyboardButton("Отклонить", 
                callback_data=f'Отклонить {payment_id} {user_id} {payment_creator}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        command_approve(payment_id, user_id, payment_creator)
    elif 'Отклонить' in query.data:
        query = update.callback_query
        message_id = query.message.message_id
        #file_id = query.message.document.file_id
        text=f"Напишите причину отклонения заявки {payment_id} ОТВЕТОМ на это сообщение.\n * Техническая информация {payment_id}.{user_id}.{payment_creator} *"

        #context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
        message_obj = context.bot.send_message(chat_id=query.message.chat_id, text=text)
        save_message_function(payment, query.message.chat_id,
            message_obj.message_id, 'reject_reason', 
            user.user_name, text, False)        
        
    elif 'Оплатить' in query.data:
        payers = PayerOrganization.objects.all()
        pay_user = ApprovedFunction.objects.get(
                username=user_id)
        payers_names = []
        payers_id = []
        payers_info = {}
        keyboard = []
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        for payer in payers:
            payers_info[payer.pk] = payer.name
            payers_names.append(payer.name)
            payers_id.append(payer.pk)
            data_for_button = f'Сохранить_платёж {payment_id} {user_id} {payment_creator} {payer.pk}' 
            button = [InlineKeyboardButton(callback_data=data_for_button, text=payer.name)]
            keyboard.append(button)
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = f'Выберите платильщика'
        message_obj_payer = bot.send_message(
            chat_id=int(pay_user.chat_id_tg), text=message, reply_markup=reply_markup, parse_mode='Markdown')
        save_message_function(payment, pay_user.chat_id_tg, message_obj_payer.message_id,
            'payment_organization', pay_user.user_name, message, False)

    elif 'Сохранить_платёж' in query.data:
        payer_pk = reaponse_data[4]
        command_pay(payment_id, user_id, payment_creator, payer_pk)


def pay_file_handler(update, context):
    """Функция обрабатывает сообщения от пользователя, если они содержат файл"""
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
            save_message_function(pay, pay_user.chat_id_tg, message.message_id,
                'payment_done', pay_user.user_name, 'message_with_attach', False)

            pay.file_of_payment = file
            pay.save()

            messages = TelegramMessageActions.objects.filter(
                payment=Payments.objects.get(id=payment_id),
                message_type='create_approve'
            ).values_list('chat_id', 'message_id', 'message', 'attach')

            for message in messages:
                chat_id =  message[0]
                message_id = message[1]
                current_text = message[2]
                attach = message[3]
                words = current_text.split("Статус:")
                new_text = words[0] + 'Статус: ✅ Оплачено'
                if attach == True:
                    bot.edit_message_caption(caption=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')
                else:
                    bot.edit_message_text(text=new_text, chat_id=chat_id, message_id=message_id, parse_mode='Markdown')

            # Удаляем все сообщения, относящиеся к заявки, кроме тех, у которых message_type='create_approve'
            messages_for_delete = TelegramMessageActions.objects.filter(
                payment=Payments.objects.get(id=payment_id)).exclude(
                message_type='create_approve'
            ).values_list('chat_id', 'message_id')
            for message_del in messages_for_delete:
                chat_id =  message_del[0]
                message_id = message_del[1]
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            
            message_id = TelegramMessageActions.objects.get(
                payment=Payments.objects.get(id=payment_id),
                message_type='create_approve',
                message_author=payment_creator
            ).message_id
            message_obj_done = bot.send_message(
                chat_id=int(creator_user.chat_id_tg), text='Оплачено', reply_to_message_id=message_id)
            save_message_function(pay, creator_user.chat_id_tg, message_obj_done.message_id,
                'payment_done', creator_user.user_name, message, False)


def command_start(update, context):
    """Функция, которая обрабатывает поступающую команду start"""
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    name = update.message.chat.first_name
    soname = update.message.chat.last_name
    username = update.message.chat.username
    idchat = update.message.chat.id

    buttons = ReplyKeyboardMarkup([
        ['/start']

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
    url = f'http://5.9.57.39/payment/login?chat_id={chat_id}'
    button_url = InlineKeyboardButton(text='Создать заявку', url=url)
    keyboard = [[button_url]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message_id = update.message.reply_text('Нажмите на кнопку, чтобы создать заявку:', reply_markup=reply_markup).message_id
    #message_id = update.message.message_id
    bot.pin_chat_message(chat_id=chat_id, message_id=message_id)


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
