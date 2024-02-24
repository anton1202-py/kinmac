import json
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
from django.contrib.auth.models import User
from django.db.models import Q
from dotenv import load_dotenv
from payment.models import (ApprovalStatus, ApprovedFunction,
                            PayerOrganization, Payments,
                            TelegramApproveButtonMessage,
                            TelegramMessageActions)
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup)
from telegram.ext import (CallbackQueryHandler, CommandHandler, Filters,
                          MessageHandler, Updater)
from telegram_working.assistance import (save_message_function,
                                         upgrade_message_function)
from telegram_working.start_tg_approve import start_tg_working

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telegram.Bot(token=TELEGRAM_TOKEN)


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
        chat_id_cicle =  message[0]
        message_id_cicle = message[1]
        current_text = message[2]
        attach = message[3]
        words = current_text.split("Статус:")
        new_text = words[0] + f'\nСтатус: ❌ Отклонено\nПричина: {reason}'
        if attach == True:
            bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')
        else:
            bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')


def reject_reason(update, context):
    """
    Функция обрабатывает текстовые сообщения, которые поступаю в бот.
    Если они удовлетвояют условию логики бота, то выполняет с сообщениями
    дальнейшие действия
    """
    chat_id = update.effective_chat.id
    if context.chat_data.get('last_bot_message_id'):
        last_bot_message_id = context.chat_data.get('last_bot_message_id')

    # Получаем информацию о последнем сообщении бота
        last_bot_message = TelegramMessageActions.objects.get(
                message_id=last_bot_message_id).message
    
        mess_id = update.message.message_id
    
        if 'Напишите причину отклонения заявки' in last_bot_message:
            chat = update.message.text
            payment_id = context.chat_data.get('payment_id')
            user_id = context.chat_data.get('user_id')
            payment_creator = context.chat_data.get('payment_creator')
            payment = Payments.objects.get(id=payment_id)
        
            command_reject(payment_id, user_id, chat)
            reject_user = ApprovedFunction.objects.get(
                username=user_id)
            save_message_function(payment, chat_id,
                mess_id, 'rejected_reason_inform', 
                reject_user.user_name, update.message.text, '', False)
            create_user = ApprovedFunction.objects.get(
                user_name=payment_creator)
            # Удаляем все сообщения связанные с заявкой, кроме message_type=create_approve
            messages_for_delete = TelegramMessageActions.objects.filter(
                Q(payment=Payments.objects.get(id=payment_id)) | Q(
                    message_type='comment_button'
                    )).exclude(
                message_type='create_approve'
            ).values_list('chat_id', 'message_id')
            for message_del in messages_for_delete:
                chat_id =  message_del[0]
                message_id = message_del[1]
                try:
                    bot.delete_message(chat_id=chat_id, message_id=message_id)
                except:
                    print(f'Сообщения {message_id} не найдено')
        
            # Отправляем создателю заявки, что заявка отклонена по какой-то причине
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
                create_user.user_name, message, '', False)

        elif 'Напишите комментарий к согласованному платежу' in last_bot_message:
            chat = update.message.text
            payment_id = context.chat_data.get('payment_id')
            user_id = context.chat_data.get('user_id')
            payment_creator = context.chat_data.get('payment_creator')
            payment = Payments.objects.get(id=payment_id)

            comment_user = ApprovedFunction.objects.get(
                username=user_id)
            comment_username = comment_user.user_name
            comment_text = update.message.text

            save_message_function(payment, chat_id,
                mess_id, 'comment_inform', 
                comment_user.user_name, update.message.text, '', False)
            command_approve(payment_id, user_id, payment_creator, comment_text, comment_username)

            

def command_approve(payment_id: int, user_id:int, payment_creator: str, comment_text: str, comment_username: str):
    """
    Функция вносит в базу данных изменения связанные с согласованием
    заявки.
    payment_id: id заявки на оплату.
    user_id: id пользователя, который совершает действия. Id из встроенной модели User
    payment_creator: создатель заявки. Записывается user_name модели ApprovedFunction
    comment_text: текст комментария пользователя, который согласовал заявку
    и может оставить комментарий.
    comment_username: username пользователя, который оставил комментарий.
    Из модели ApprovedFunction берется поле user_name
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
        start_tg_working(payment_id, payment_creator, (approval_user.rating_for_approval+1), comment_text, comment_username)
    elif approval_user.rating_for_approval == 10:
        start_tg_working(payment_id, payment_creator, approval_user.rating_for_approval, comment_text, comment_username)


def command_pay(context, payment_id, user_id, payment_creator, payer_company):
    """Функция выполняет действия после нажатия на кнопку ОПЛАЧЕНО"""
    now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pay_user = ApprovedFunction.objects.get(
        username=user_id)
    creator_user = ApprovedFunction.objects.get(
        user_name=payment_creator)
    pay = Payments.objects.get(id=payment_id)

    pay.status_of_payment = 'Оплачено'
    pay.date_of_payment = now_time
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
        message = f'Необходимо прислать платёжку к этому платежу.'
        message_file_obj = bot.send_message(
            chat_id=int(pay_user.chat_id_tg), text=message)
        
        # Сохраняем в данные чата идентификатор последнего сообщения от бота
        last_bot_message_id = message_file_obj.message_id
        context.chat_data['last_bot_message_id'] = last_bot_message_id
        context.chat_data['payment_id'] = payment_id
        context.chat_data['user_id'] = user_id
        context.chat_data['payment_creator'] = payment_creator
        # Сохраняем сообщение в базу
        save_message_function(pay, pay_user.chat_id_tg, 
            message_file_obj.message_id, 'payment_file', 
            pay_user.user_name, message, '', False)
    else:
        # Изменяем текст во всех сообщениях связанных с заявкой
        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'attach')

        for message in messages:
            chat_id_cicle =  message[0]
            message_id_cicle = message[1]
            current_text = message[2]
            attach = message[3]
            words = current_text.split("Статус:")
            new_text = words[0] + 'Статус: ✅ Оплачено'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')

        # Удаляем все сообщения, относящиеся к заявки, кроме тех, у которых message_type='create_approve'
        messages_for_delete = TelegramMessageActions.objects.filter(
            Q(payment=Payments.objects.get(id=payment_id))|Q(
                    message_type='comment_button'
                    )).exclude(
            message_type='create_approve'
        ).values_list('chat_id', 'message_id')
        for message_del in messages_for_delete:
            chat_id =  message_del[0]
            message_id = message_del[1]
            try:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            except:
                print(f'Сообщение {message_id} не найдено')

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
            message, '', False)


def button_click(update, context):
    """Обрабатьвает нажатия кнопок в сообщении"""
    query = update.callback_query
    response = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    reaponse_data = response.split()
    payment_id = reaponse_data[1]
    user_id = reaponse_data[2]
    payment_creator = reaponse_data[3]
    payment = Payments.objects.get(pk=payment_id)
    user = ApprovedFunction.objects.get(
                username=user_id)
    
    if 'Согласовать' in query.data:
        keyboard = [[
            InlineKeyboardButton("Отклонить", 
                callback_data=f'Отклонить {payment_id} {user_id} {payment_creator}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
        upgrade_message_function(message_id, reply_markup)

        button_approved_user = ApprovedFunction.objects.get(
            chat_id_tg=chat_id).pk

        button_user = TelegramApproveButtonMessage.objects.get(
           approve=button_approved_user
        )

        if button_user.button_name == 'Не оставлять комментарий':
            text="Напишите комментарий к согласованному платежу"
            message_obj = context.bot.send_message(chat_id=query.message.chat_id, text=text)

            # Сохраняем в данные чата идентификатор последнего сообщения от бота
            last_bot_message_id = message_obj.message_id
            context.chat_data['last_bot_message_id'] = last_bot_message_id
            context.chat_data['payment_id'] = payment_id
            context.chat_data['user_id'] = user_id
            context.chat_data['payment_creator'] = payment_creator

            save_message_function(payment, query.message.chat_id,
                message_obj.message_id, 'payment_organization', 
                user.user_name, text, '', False)  
        else:
            command_approve(payment_id, user_id, payment_creator, '', '')
    elif 'Отклонить' in query.data:
        query = update.callback_query
        message_id = query.message.message_id
        #file_id = query.message.document.file_id
        text=f"Напишите причину отклонения заявки {payment_id}."

        #context.bot.delete_message(chat_id=query.message.chat_id, message_id=message_id)
        message_obj = context.bot.send_message(chat_id=query.message.chat_id, text=text)

        # Сохраняем в данные чата идентификатор последнего сообщения от бота
        last_bot_message_id = message_obj.message_id
        context.chat_data['last_bot_message_id'] = last_bot_message_id
        context.chat_data['payment_id'] = payment_id
        context.chat_data['user_id'] = user_id
        context.chat_data['payment_creator'] = payment_creator

        save_message_function(payment, query.message.chat_id,
            message_obj.message_id, 'reject_reason', 
            user.user_name, text, '', False)        
        
    elif 'Оплатить' in query.data:
        payers = PayerOrganization.objects.all()
        pay_user = ApprovedFunction.objects.get(
                username=user_id)
        payers_names = []
        payers_id = []
        payers_info = {}
        keyboard = []
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id)
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
            chat_id=int(pay_user.chat_id_tg), text=message, reply_markup=reply_markup, parse_mode='HTML')
        save_message_function(payment, pay_user.chat_id_tg, message_obj_payer.message_id,
            'payment_organization', pay_user.user_name, message, reply_markup, False)

    elif 'Вработе' in query.data:
        payer_user = ApprovedFunction.objects.get(
                username=user_id)
        pay_user_lastname = payer_user.last_name
        pay_user_firstname = payer_user.first_name
        
        # Изменяем текст во всех сообщениях связанных с заявкой
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
            new_text = words[0] + f'‼️‼️ Статус: В работе у {pay_user_firstname} {pay_user_lastname}'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, message_id=message_id_cicle, parse_mode='HTML')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, message_id=message_id_cicle, parse_mode='HTML')
        # После нажатия на кнопку В Работе, у нажавшего меняются кнопки
        keyboard = [[InlineKeyboardButton("Отклонить", callback_data=f'Отклонить {payment_id} {user_id} {payment_creator}'),
                        InlineKeyboardButton("Вернуть в очередь", callback_data=f'О_тменить_В_работе {payment_id} {user_id} {payment_creator}'),
                        InlineKeyboardButton("Оплачено", callback_data=f'Оплатить {payment_id} {user_id} {payment_creator}')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
    
    elif 'О_тменить_В_работе' in query.data:
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
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, essage_id=message_id_cicle, parse_mode='HTML')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, reply_markup=reply_markup, message_id=message_id_cicle, parse_mode='HTML')
    
    elif 'Сохранить_платёж' in query.data:
        payer_pk = reaponse_data[4]
        command_pay(context, payment_id, user_id, payment_creator, payer_pk)

def button_comment_handler(update, context):
    """Обрабатывает нажатия на кнопки оставлять/не оставлять комментарий"""
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    approved_user = ApprovedFunction.objects.get(
            chat_id_tg=chat_id)
    payment = Payments.objects.filter(Q(payment_coefficient=1), Q(payment_coefficient__gte=1))
    save_message_function(payment[-1], chat_id,
        message_id, 'comment_button', 
        approved_user.user_name, update.message.text, '', False)

    if 'Не оставлять комментарий' in update.message.text:
        new_button_name = 'Оставлять комментарий'
        text='Теперь вам не нужно оставлять комментарий'
        TelegramApproveButtonMessage.objects.filter(
           approve=approved_user
        ).update(
            button_name=new_button_name
        )
        keyboard = ReplyKeyboardMarkup([['/start'], [KeyboardButton(new_button_name)]], resize_keyboard=True)
        message_obj = bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=keyboard)
        save_message_function(payment[-1], chat_id,
            message_obj.message_id, 'comment_button', 
            approved_user.user_name, text, '', False)

    elif 'Оставлять комментарий' in update.message.text:
        new_button_name = 'Не оставлять комментарий'
        approved_user = ApprovedFunction.objects.get(
            chat_id_tg=chat_id)
        text='Теперь вы сможете оставлять комментарий'
        TelegramApproveButtonMessage.objects.filter(
           approve=approved_user
        ).update(
            button_name=new_button_name
        )
        keyboard = ReplyKeyboardMarkup([['/start'], [KeyboardButton(new_button_name)]], resize_keyboard=True)
        message_obj = bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=keyboard)

        save_message_function(payment[-1], chat_id,
            message_obj.message_id, 'comment_button', 
            approved_user.user_name, text, '', False)


def pay_file_handler(update, context):
    """Функция обрабатывает сообщения от пользователя, если они содержат файл"""
    message = update.message
    last_bot_message_id = context.chat_data.get('last_bot_message_id')

    # Получаем информацию о последнем сообщении бота
    last_bot_message = TelegramMessageActions.objects.get(
                message_id=last_bot_message_id).message

    if 'Необходимо прислать платёжку' in last_bot_message:
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payment_id = context.chat_data.get('payment_id')
        user_id = context.chat_data.get('user_id')
        payment_creator = context.chat_data.get('payment_creator')
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
            file.name = f'Платежка для заявки {payment_id} от {now_time}.pdf'  # Установка имени файла
        elif message.photo:
            file_id = update.message.photo[-1].file_id
            file_path = bot.get_file(file_id).file_path
            response = requests.get(file_path)
            file_content = response.content
            file = ContentFile(file_content)
            file.name = f'Платежка для заявки {payment_id} от {now_time}.png'  # Установка имени файла
        pay = Payments.objects.get(id=payment_id)
        save_message_function(pay, pay_user.chat_id_tg, message.message_id,
            'payment_done', pay_user.user_name, 'message_with_attach', '', False)
        pay.file_of_payment = file
        pay.save()
        messages = TelegramMessageActions.objects.filter(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve'
        ).values_list('chat_id', 'message_id', 'message', 'attach')
        for message in messages:
            chat_id_cicle =  message[0]
            message_id_cicle = message[1]
            current_text = message[2]
            attach = message[3]
            words = current_text.split("Статус:")
            new_text = words[0] + 'Статус: ✅ Оплачено'
            if attach == True:
                bot.edit_message_caption(caption=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')
            else:
                bot.edit_message_text(text=new_text, chat_id=chat_id_cicle, message_id=message_id_cicle, parse_mode='HTML')
        # Удаляем все сообщения, относящиеся к заявки, кроме тех, у которых message_type='create_approve'
        messages_for_delete = TelegramMessageActions.objects.filter(
            Q(payment=Payments.objects.get(id=payment_id)) | Q(
                    message_type='comment_button'
                    )).exclude(
            message_type='create_approve'
        ).values_list('chat_id', 'message_id')
        
        for message_del in messages_for_delete:
            chat_id =  message_del[0]
            message_id = message_del[1]
            try:
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                print(e)
        
        message_id = TelegramMessageActions.objects.get(
            payment=Payments.objects.get(id=payment_id),
            message_type='create_approve',
            message_author=payment_creator
        ).message_id
        if Payments.objects.get(id=payment_id).send_payment_file == True:
            file_path = os.path.join(os.getcwd(), 'media/' f'{Payments.objects.get(id=payment_id).file_of_payment}')
            with open(file_path, 'rb') as f:
                message_obj_done = bot.send_document(
                    chat_id=int(creator_user.chat_id_tg),
                    document=f,
                    caption='Оплачено',
                    reply_to_message_id=message_id)
        else:
            message_obj_done = bot.send_message(
                chat_id=int(creator_user.chat_id_tg),
                text='Оплачено', reply_to_message_id=message_id)
        save_message_function(pay, creator_user.chat_id_tg, message_obj_done.message_id,
            'payment_done', creator_user.user_name, message, '', False)


def command_start(update, context):
    """Функция, которая обрабатывает поступающую команду start"""
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    name = update.message.chat.first_name
    soname = update.message.chat.last_name
    username = update.message.chat.username
    idchat = update.message.chat.id

    approved_user = ApprovedFunction.objects.get(
            chat_id_tg=chat_id)

    button_user = TelegramApproveButtonMessage.objects.get(
       approve=approved_user
    )

    if approved_user.rating_for_approval > 0:
        buttons = ReplyKeyboardMarkup([
            ['/start'], [KeyboardButton(button_user.button_name)]
        ], resize_keyboard=True)
    else: 
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
    updater.dispatcher.add_handler(MessageHandler(Filters.text("Оставлять комментарий"), button_comment_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.text("Не оставлять комментарий"), button_comment_handler))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_click))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, reject_reason))
    updater.dispatcher.add_handler(MessageHandler(Filters.document | Filters.photo | Filters.video, pay_file_handler))
    
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
